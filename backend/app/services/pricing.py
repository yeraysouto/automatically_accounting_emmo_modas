from __future__ import annotations

from dataclasses import dataclass

from app.db.models import ImportacionArticulosMontcau, OcrInfoClothes
from app.settings import get_settings


@dataclass
class PriceDecision:
    flag: str | None
    reason: str | None
    adjusted_price: float | None


def evaluate_price(
    *,
    line: OcrInfoClothes,
    article: ImportacionArticulosMontcau | None,
) -> PriceDecision:
    settings = get_settings()
    if line.price is None or article is None or article.coste_unitario is None:
        return PriceDecision(flag=None, reason=None, adjusted_price=None)

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


def apply_price_decision(line: OcrInfoClothes, decision: PriceDecision) -> None:
    if decision.flag:
        line.price_flag = decision.flag
        line.price_flag_reason = decision.reason
    if decision.adjusted_price is not None:
        line.price = decision.adjusted_price
        if line.quantity is not None:
            line.total_no_iva = decision.adjusted_price * line.quantity
