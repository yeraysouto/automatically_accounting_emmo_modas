from __future__ import annotations

"""Pricing rules for invoice lines (non-AI).

This module evaluates whether an OCR-extracted line price looks plausible.
It supports two data sources:

1) Master data (`importacion_articulos_montcau.coste_unitario`) when available.
2) Historical observations (`price_observation`) as a fallback median per reference.

The result is a `PriceDecision` which can either:
- do nothing,
- flag the line,
- or adjust the price (depending on `EMMO_PRICE_CORRECTION_MODE`).
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ImportacionArticulosMontcau, OcrInfoClothes, PriceObservation
from app.settings import get_settings


@dataclass
class PriceDecision:
    """Decision output of the pricing evaluation."""
    flag: str | None
    reason: str | None
    adjusted_price: float | None


def evaluate_price(
    *,
    db: Session,
    line: OcrInfoClothes,
    article: ImportacionArticulosMontcau | None,
) -> PriceDecision:
    """Evaluate a line price against business rules.

    Args:
        db: SQLAlchemy session (used for historical fallback).
        line: The OCR line to validate.
        article: Master article (if known).

    Returns:
        A `PriceDecision` describing flags and optional correction.
    """
    settings = get_settings()

    if line.price is None or not line.reference_code:
        return PriceDecision(flag=None, reason=None, adjusted_price=None)

    # 1) If we have a known cost from master data, use that as the primary rule.
    if article is not None and article.coste_unitario is not None:
        floor = article.coste_unitario * settings.price_min_ratio
        if line.price >= floor:
            return PriceDecision(flag=None, reason=None, adjusted_price=None)

        if settings.price_correction_mode == "floor_to_cost":
            return PriceDecision(
                flag="corrected_to_cost",
                reason=f"below_{settings.price_min_ratio}_of_coste_unitario",
                adjusted_price=article.coste_unitario,
            )

        return PriceDecision(
            flag="too_low",
            reason=f"below_{settings.price_min_ratio}_of_coste_unitario",
            adjusted_price=None,
        )

    # 2) Otherwise, fall back to a historical median per reference_code.
    q = (
        select(PriceObservation.observed_price)
        .where(PriceObservation.reference_code == line.reference_code)
        .order_by(PriceObservation.created_at.desc())
        .limit(200)
    )
    prices = [float(p) for p in db.scalars(q).all() if p is not None]
    if len(prices) < settings.price_history_min_samples:
        return PriceDecision(flag=None, reason=None, adjusted_price=None)

    prices_sorted = sorted(prices)
    mid = len(prices_sorted) // 2
    if len(prices_sorted) % 2 == 1:
        median = prices_sorted[mid]
    else:
        median = (prices_sorted[mid - 1] + prices_sorted[mid]) / 2.0

    floor = median * settings.price_min_ratio
    if line.price >= floor:
        return PriceDecision(flag=None, reason=None, adjusted_price=None)

    if settings.price_correction_mode == "floor_to_reference_median":
        return PriceDecision(
            flag="corrected_to_reference_median",
            reason=f"below_{settings.price_min_ratio}_of_reference_median",
            adjusted_price=median,
        )

    return PriceDecision(
        flag="too_low",
        reason=f"below_{settings.price_min_ratio}_of_reference_median",
        adjusted_price=None,
    )


def apply_price_decision(line: OcrInfoClothes, decision: PriceDecision) -> None:
    """Apply a `PriceDecision` into the persisted line fields."""
    if decision.flag:
        line.price_flag = decision.flag
        line.price_flag_reason = decision.reason
    if decision.adjusted_price is not None:
        line.price = decision.adjusted_price
        if line.quantity is not None:
            line.total_no_iva = decision.adjusted_price * line.quantity
