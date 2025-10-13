/**
  * Devuelve la identificación a partir del concepto y el importe.
  * =IDENTIFICAR( concepto ; importe )
  *
  * En caso de que no se conozca devolverá "Otros gastos (CV)"
  */
function IDENTIFICAR(fecha, descripcion, importe) {

  if (descripcion === null || descripcion === ""){
    return null;
  }

  //Impuesto Sociedades (CV) seguridad social entre 27 y 31 de cada mes
  if (descripcion.includes("IMPUESTOS") && fecha.getDate() >= 27 && importe>=350 && importe<=400) return "631_000_000 (CV)";
  if (descripcion.includes("IMPUESTOS") && fecha.getDate() >= 27) return "642 (CV)";
  if (descripcion.includes("IMPUESTOS") && fecha.getDate() >= 20 && fecha.getDate() <= 23 && importe>=460 && importe<=470) return "Arrendamientos (CV)";
  if (descripcion.includes("IMPUESTOS") && fecha.getDate() >= 3 && fecha.getDate() <= 7) return "IVA trimestral (CV)";

  //631_000_000 (CV)


  //IVA trimestral (CV)


  // Servicios profesionales (CF)
  if (descripcion.includes("ADEUDO RECIBO MARIA JESUS ROSAS MORAO")) return "Servicios profesionales (CF)";
  if (descripcion.includes("TAX")) return "Servicios profesionales (CF)";
  if (descripcion.includes("NOTARIA")) return "Servicios profesionales (CF)";

  // Suministros (CF)
  if (descripcion.includes("APPLE")) return "Suministros (CF)";
  if (descripcion.includes("IATSAE")) return "Suministros (CF)";
  if (descripcion.includes("JAZZTEL")) return "Suministros (CF)";
  if (descripcion.includes("ENDESA")) return "Suministros (CF)";
  if (descripcion.includes("Jazztel")) return "Suministros (CF)";
  if (descripcion.includes("BeeDIGITAL")) return "Suministros (CF)";
  if (descripcion.includes("AGEDI") || descripcion.includes("SGAE")) return "Suministros (CF)";
  if (descripcion.includes("SECURITAS DIRECT")) return "Suministros (CF)";

  // Gastos de personal (CF)
  if (descripcion.includes("TRANSFERENCIA A") && descripcion.includes("AIDA NORA")) return "Gastos de personal (CF)";
  if (descripcion.includes("NOMINA COPALAU S.L.")) return "Gastos de personal (CF)";
  if (descripcion.includes("SEGUROS SOCIALES")) return "Gastos de personal (CF)";
  if (descripcion.includes("TGSS")) return "Gastos de personal (CF)";

  // Parking (CF)
  if (descripcion.includes("DOLORES TOLSA")) return "Parking (CF)";

  // Arrendamientos (CF)
  if (descripcion.includes("TRANSFERENCIA A PEDRO LOPEZ")) return "Arrendamientos (CF)";

  //Mobiliario (CV)
  if (descripcion.includes("COMPRA TARJ") && descripcion.includes("AMAZON")) return "Mobiliario (CV)";
  if (descripcion.includes("COMPRA TARJ") && descripcion.includes("Amazon")) return "Mobiliario (CV)";
  if (descripcion.includes("COMPRA TARJ") && descripcion.includes("LEROY")) return "Mobiliario (CV)";
  if (descripcion.includes("COMPRA TARJ") && descripcion.includes("BASAR")) return "Mobiliario (CV)";
  if (descripcion.includes("COMPRA TARJ") && descripcion.includes("BAZAR")) return "Mobiliario (CV)";

  // Gastos de transporte (CV)
  if (descripcion.includes("IBERSANTJUST, S.L.")) return "Gastos de transporte (CV)";
  if (descripcion.includes("METRO")) return "Gastos de transporte (CV)";
  if (descripcion.includes("LOGISTICA")) return "Gastos de transporte (CV)";

  // Compra de Mercaderias (CV)
  if (descripcion.includes("CHLOE") && descripcion.includes("COMPRA")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("TRANSFERENCIA A")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("ADEUDO")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("BESTSELLER")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("BE THE REFERENCE")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("BLUE HOLE")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("BS")) return "Compra de Mercaderias (CV)";
  if (descripcion.includes("COMPRA TARJ")) return "Compra de Mercaderias (CV)";

  // Comision TPV (CF)
  if (descripcion.includes("TPV") && descripcion.includes("SERVICIO")) return "Comision TPV (CF)";

  // Comisiones bancarias (CF)
  if (descripcion.includes("COMISIONES KT")) return "Comisiones bancarias (CF)";
  if (descripcion.includes("COMISIONES") && importe==-54) return "Comisiones bancarias (CF)";
  

  // Comisiones bancarias (CV)
  if (descripcion.includes("COMISIONES") && descripcion.includes("MANTENIMIENTO")) return "Comisiones bancarias (CV)";
  if (descripcion.includes("COMISIONES")) return "Comisiones bancarias (CV)";
  if (descripcion.includes("COMISIÓN")) return "Comisiones bancarias (CV)";
  if (descripcion.includes("COMISION")) return "Comisiones bancarias (CV)";
  if (descripcion.includes("INTERESES")) return "Comisiones bancarias (CV)";

  // Cuotas aplazamientos (CV)
  if (descripcion.includes("IMPUESTOS")) return "Cuotas aplazamientos (CV)";

  // Deudas a corto plazo (CV)
  if (descripcion.includes("TARJETA CREDITO")) return "Deudas a corto plazo (CV)";

  // Primas de Seguro (CF)
  if (descripcion.includes("SEGUROS")) return "Primas de Seguro (CF)";

  // 700_000_000
  if (descripcion.includes("ABONO TPV")) return "700_000_000";

  // Fallback por importe
  if (!isNaN(importe)) {
    if (importe > 0) return "700_000_000";
    else return "Otros gastos (CV)";
  }

  return "Otros gastos (CV)";
}

/**
  * Devuelve la especificación a partir del concepto y la identificación.
  * =ESPECIFICACIÓN( concepto ; identificación )
  *
  * En caso de que no se conozca devoverá "DESCONOCIDO"
  */
function ESPECIFICACION(descripcion, identificacion) {
  7
  if (descripcion === null || descripcion === ""){
    return null;
  }

  // 700_000_000
  if (identificacion === "700_000_000") {
    return "VISA";
  }

  // 701_000_000
  if (identificacion === "701_000_000") {
    if (true) return "EFECTIVO";
  }

  // Arrendamientos (CF)
  if (identificacion === "Arrendamientos (CF)") {
    if (true) return "CAMPFASO 22";
  }

  // Compra de Mercaderias (CV)
  if (identificacion === "Compra de Mercaderias (CV)") {
    if (descripcion.includes("MERTOR INVEST")) return "VESMER";
    if (descripcion.includes("ANGELINA")) return "ANGELINA";
    if (descripcion.includes("ASHLEY")) return "ASHLEY";
    if (descripcion.includes("BESTSELLER")||descripcion.includes("BS")||descripcion.includes("Wholesale")) return "BESTSELLER";
    if (descripcion.includes("BSSG")) return "BSSG";
    if (descripcion.includes("BLUE HOLE")) return "BLUE HOLE";
    if (descripcion.includes("BE THE REFERENCE")) return "BE THE REFERENCE";
    if (descripcion.includes("LETIZ")) return "LETIZ";
    if (descripcion.includes("CHLOE LUCAS")||descripcion.includes("CHOE LUCAS")||descripcion.includes("CHOE & LUCAS")||descripcion.includes("CHLOE & LUCAS")||descripcion.includes("CLOE & LUCAS")||descripcion.includes("CLOE LUCAS")) return "CHLOE LUCAS";
    if (descripcion.includes("MERTOT")) return "VESMER";
    if (descripcion.includes("JIANNA")) return "JIANNA";
    if (descripcion.includes("PULSERAS")) return "PULSERAS";
    if (descripcion.includes("SHINE")) return "SHINE";
    if (descripcion.includes("JEWELS CENTURY")) return "PAN DE ORO";
    if (descripcion.includes("MIN MILA")) return "MIN MILA MOLINA";

    if (descripcion.includes("TRANSFERENCIA A")){
      nombre=descripcion;
      nombre = nombre.replace(/(TRANSFERENCIA|TRANSFERENCIA A)$/, "").trim();
      nombre = nombre.replace(/( S.L.|S.L)$/, "").trim();
      return nombre;
    }

    if (descripcion.includes("COMPRA TARJ")) {
      const regex = /^COMPRA TARJ\. \d{4}X{8}\d{4} (.+)$/;
      const match = descripcion.match(regex);
      if (match) {
        let nombre = match[1];
        nombre = nombre.replace(/-(BARCELONA|BADALONA|SAN ADRIA DEL|SANT JOAN|ESPLUGUES|ESPLUGUES DE)$/, "").trim();// Elimina barrio/zona
        return nombre;
      }
    }


    return "DESCONOCIDO";
  }
  
  // Comision TPV (CF)
  if (identificacion === "Comision TPV (CF)") {
    return "Comision TPV";
  }

  // Compra de Mercaderias B (CV)
  if (identificacion === "Compra de Mercaderias B (CV)") {
    if (descripcion.includes("LETIZ")) return "LETIZ";
    if (descripcion.includes("ASHLEY")) return "ASHLEY";
    if (descripcion.includes("CRISTINA")) return "CRISTINA";
    if (descripcion.includes("BEATIFUL ENCOUNTER")) return "BEATIFUL ENCOUNTER";
    if (descripcion.includes("ANGELINA")) return "ANGELINA";
    if (descripcion.includes("FEDERIKA")) return "FEDERIKA";

    return "DESCONOCIDO";
  }

  // Montse
  if (identificacion === "MONTSE") {
    if (descripcion.includes("YERAY")) return "YERAY (CV)";
    if (descripcion.includes("SERGIO")) return "SERGIO (CF)";
    if (descripcion.includes("MEDIA MENSUAL")) return "MEDIA MENSUAL (CF)";
    if (descripcion.includes("PANADERIA")) return "CASA COMIDA (CF)";
    if (descripcion.includes("LIDL")) return "CASA COMIDA (CF)";
    if (descripcion.includes("MERCADONA")) return "CASA COMIDA (CF)";
    if (descripcion.includes("CAFES")) return "TOMAR ALGO (CV)";
    if (descripcion.includes("PUYOL")) return "TOMAR ALGO (CV)";
    if (descripcion.includes("COMIDA")) return "TOMAR ALGO (CV)";
    if (descripcion.includes("FLORES")) return "CAPRICHOS (CV)";
    if (descripcion.includes("IMPUESTO") && descripcion.includes("COCHE")) return "IMPUESTOS (CF)";
    if (descripcion.includes("IMPUESTO")) return "IMPUESTOS (CV)";

    return "DESCONOCIDO";
  }

  // Gastos de personal (CF)
  if (identificacion === "Gastos de personal (CF)") {
    if (descripcion.includes("AIDA NORA")) return "NOMINA";
    if (descripcion.includes("NOMINA")) return "NOMINA";
    if (descripcion.includes("SEGUROS SOCIALES")) return "SSGG A CARGO EMPRESA";
    if (descripcion.includes("TGSS")) return "SSGG A CARGO EMPRESA";

    return "DESCONOCIDO";
  }

  // Gastos de transporte (CV)
  if (identificacion === "Gastos de transporte (CV)") {
    if (descripcion.includes("COMPRA TARJ")) return "GASOLINA";
    if (descripcion.includes("RECIBO")) return "GASTOS TRANSPORTE";

    return "DESCONOCIDO";
  }

  // Comisiones bancarias (CV)
  if (identificacion.includes("Comisiones bancarias")) {
    if (descripcion.includes("MANTENIMIENTO")) return "MANTENIMIENTO";
    if (descripcion.includes("INTERESES Y/O COMISIONES")) return "COMISIONES BANCARIAS";
    if (descripcion.includes("DIVISA")) return "DIVISA";
    
    return "POLIZA (GASTO)";
  }

  // Mobiliario (CV)
  if (identificacion === "Mobiliario (CV)") {
    if (descripcion.includes("AMAZON")||descripcion.includes("Amazon")||descripcion.includes("amazon")) return "AMAZON";
    if (descripcion.includes("LEROY")) return "LEROY MERLIN";
    if (descripcion.includes("BAZAR")||descripcion.includes("BASAR")) return "BASAR CHINO";
    
    return "POLIZA (GASTO)";
  }

  // Suministros (CF)
  if (identificacion === "Suministros (CF)") {
    if (descripcion.includes("IATSAE")) return "IATSAE";
    if (descripcion.includes("APPLE")) return "APPLE";
    if (descripcion.includes("BeeDIGITAL")) return "BEEDIGITAL";
    if (descripcion.includes("ENDESA")) return "LUZ";
    if (descripcion.includes("SECURITAS DIRECT")) return "SECURITAS DIRECT";
    if (descripcion.includes("JAZZTEL")||descripcion.includes("Jazztel")) return "JAZZTEL";
    if (descripcion.includes("AGEDI") || descripcion.includes("SGAE")) return "SGAE - MUSICA";


    return "DESCONOCIDO";
  }

  // Primas de Seguro (CF)
  if (identificacion === "Primas de Seguro (CF)") {
    if (descripcion.includes("DKV")) return "DKV";
    if (descripcion.includes("SEGURCAIXA")) return "COMPLEJO FAMILY";
    if (descripcion.includes("BANSABADELL")) return "OBLIGATORIO";

    return "DESCONOCIDO";
  }

  // Servicios profesionales (CF)
  if (identificacion === "Servicios profesionales (CF)") {
    if (descripcion.includes("TAX")) return "TAX";
    if (descripcion.includes("NOTARIA")) return "NOTARIA";
    if (true) return "SSGG";
  }

  // Deudas a corto plazo (CV)
  if (identificacion === "Deudas a corto plazo (CV)") {
    if (true) return "TARGETA CREDITO";
  }

  // Cuotas aplazamientos (CV)
  if (identificacion === "Cuotas aplazamientos (CV)") {
    if (true) return "IVA APLAZADO";
  }

  // Parking (CF)
  if (identificacion === "Parking (CF)") {
    if (true) return "PARKING TIENDA";
  }

  return "DESCONOCIDO";
}

//BORRA UN RANGO DE UNA HOJA ESPECÍFICA//
/**
 * Borra el contenido de un rango especófico en cualquier hoja del documento.
 * =borrarRangoEnHoja("nombre de la hoja", "rango que se quiere borrar")
 * 
 * Nombre de la hoja: escribir en formato texto y entre comillas
 * Rango que se quiere borrar:
 *      Para una celda, escribir celda: B18
 *      Para un rango, escribir extremos: B18:C20 (borra B18, B19, B20, C18, C19 y C20)
 */
function borrarRangoEnHoja(nombreHoja, rangoA1) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hoja = ss.getSheetByName(nombreHoja);
  
  if (!hoja) {
    SpreadsheetApp.getUi().alert("No se encontró la hoja '" + nombreHoja + "'");
    return;
  }
  
  hoja.getRange(rangoA1).clearContent(); // Borra solo los valores (no formato, notas, etc.)
}

// COPIAR CSV MOVIMIENTOS //
function CSVmovimientos() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hojaOrigen = ss.getSheetByName("CSV MOVIMIENTOS");
  var hojaDestino = ss.getSheetByName("CONSULTA MOVIMIENTOS");

  // Devuelve error si no se encuentra alguna de las hojas
  if (!hojaOrigen) {
    SpreadsheetApp.getUi().alert("No se encontró la hoja 'CSV MOVIMIENTOS'.");
    return;
  }
  if (!hojaDestino) {
    SpreadsheetApp.getUi().alert("No se encontró la hoja 'CONSULTA MOVIMIENTOS'.");
    return;
  }

  // Determinar última fila con datos en columna A (origen)
  var datos = hojaOrigen.getRange("A:A").getValues();
  var ultimaFilaOrigen = 0;
  for (var i = datos.length - 1; i >= 0; i--) {
    if (datos[i][0] !== "") {
      ultimaFilaOrigen = i + 1;
      break;
    }
  }

  // En caso de que no hayan datos a partir de la fila 10 devuelve el error
  if (ultimaFilaOrigen < 10) {
    SpreadsheetApp.getUi().alert("No hay suficientes datos para copiar desde la fila 10.");
    return;
  }

  var numFilas = ultimaFilaOrigen - 10 + 1;

  // Obtener datos en el orden A, B, H, I, D
  var datosA = hojaOrigen.getRange(10, 1, numFilas, 1).getValues(); // A
  var datosB = hojaOrigen.getRange(10, 2, numFilas, 1).getValues(); // B
  var datosH = hojaOrigen.getRange(10, 8, numFilas, 1).getValues(); // H
  var datosI = hojaOrigen.getRange(10, 9, numFilas, 1).getValues(); // I
  var datosD = hojaOrigen.getRange(10, 4, numFilas, 1).getValues(); // D

  // Combinar en una sola matriz
  var datosFinales = [];
  for (var i = 0; i < numFilas; i++) {
    datosFinales.push([datosA[i][0], datosB[i][0], datosH[i][0], datosI[i][0], datosD[i][0]]);
  }

  // Insertar filas necesarias en hoja destino a partir de la fila 8
  hojaDestino.insertRowsBefore(4, datosFinales.length);

  // Pegar los datos a partir de la celda B8
  hojaDestino.getRange(4, 2, datosFinales.length, datosFinales[0].length).setValues(datosFinales);

  //Borrado de datos existentes
  borrarRangoEnHoja("CSV MOVIMIENTOS", "A1:G");

  SpreadsheetApp.getUi().alert(
    "Se han insertado " + datosFinales.length + " filas en 'CONSULTA MOVIMIENTOS' a partir de B8 con los datos nuevos."
  );
}

// COPIAR CSV EFECTIVO //
function CSVefectivo() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hojaOrigen = ss.getSheetByName("CSV EFECTIVO");
  var hojaDestino = ss.getSheetByName("CONSULTA EFECTIVO");
  
  // Devuelve error si no se encuentra alguna de las hojas
  if (!hojaOrigen) {
    SpreadsheetApp.getUi().alert("No se encontró la hoja 'CSV EFECTIVO'.");
    return;
  }
  if (!hojaDestino) {
    SpreadsheetApp.getUi().alert("No se encontró la hoja 'CONSULTA EFECTIVO'.");
    return;
  }
  
  // Determinar última fila con datos en columna A (origen)
  var datos = hojaOrigen.getRange("A:A").getValues();
  var ultimaFilaOrigen = 0;
  for (var i = datos.length - 1; i >= 0; i--) {
    if (datos[i][0] !== "") {
      ultimaFilaOrigen = i + 1;
      break;
    }
  }
  
  // En caso de que no hayan datos a partir de la fila 6 devuelve el error
  if (ultimaFilaOrigen < 6) {
    SpreadsheetApp.getUi().alert("No hay suficientes datos para copiar desde la fila 6.");
    return;
  }

  var numFilas = ultimaFilaOrigen - 6 + 1;

  // Obtener datos en el orden B, C, D, E, J, T, N, O, P, Q desde hojaOrigen
  var datosB = hojaOrigen.getRange(6, 2, numFilas, 1).getValues();   // B Caja
  var datosC = hojaOrigen.getRange(6, 3, numFilas, 1).getValues();   // C Numero
  var datosD = hojaOrigen.getRange(6, 4, numFilas, 1).getValues();   // D Fecha
  var datosE = hojaOrigen.getRange(6, 5, numFilas, 1).getValues();   // E Empleado
  var datosF = hojaOrigen.getRange(6, 6, numFilas, 1).getValues();   // F Ventas totales 
  var datosJ = hojaOrigen.getRange(6, 10, numFilas, 1).getValues();  // J Venta efectivo
  var datosN = hojaOrigen.getRange(6, 14, numFilas, 1).getValues();  // N Calculado
  var datosO = hojaOrigen.getRange(6, 15, numFilas, 1).getValues();  // O Declarado
  var datosP = hojaOrigen.getRange(6, 16, numFilas, 1).getValues();  // P Descuadre
  var datosQ = hojaOrigen.getRange(6, 17, numFilas, 1).getValues();  // Q Retirado
  var datosL = hojaOrigen.getRange(6, 12, numFilas, 1).getValues();  // L Salida
  var datosK = hojaOrigen.getRange(6, 11, numFilas, 1).getValues();  // K Entrada

  // Combinar en una sola matriz
  var datosFinales = [];
  for (var i = 0; i < numFilas; i++) {
    datosFinales.push([
    /** 1Caja */ datosD[i][0],
    /** 2Numero */ datosC[i][0],
    /** 3Fecha */ datosB[i][0],
    /** 4Empleado */ datosE[i][0],
    /** 5Venta Efectivo */ datosJ[i][0],
    /** 6Venta Tarjeta */ datosF[i][0]-datosJ[i][0],
    /** 7Calculado */ datosN[i][0],
    /** 8Declarado */ datosO[i][0],
    /** 9Descuadre */ datosP[i][0],
    /** 0Retirado */ datosQ[i][0],
    /** 1Salida */ datosL[i][0],
    /** 2Entrada */ datosK[i][0],
    /** 3VENTA REAL */ 0,
    /** 4GASTOS */ 0,
    /** 5COMPARATIVA */ `=F${i+4} - L${i+4} + M${i+4}`,
    /** 6CONCEPTO */ "", 
    /** 7DESCRIPCION */ "",
    /** 8MONTSE */ `=IF(L${i+4}>=70;70;L${i+4})`,
    /** 9COMPRA MERCADERIAS */ `=IF(L${i+4}>=140;60;L${i+4}-P${i+4})`,
    /** 0YERAY */ `=L${i+4}-P${i+4}-Q${i+4}`
    ]);
  }

  // Insertar filas necesarias desde la fila 4 hacia abajo
  hojaDestino.insertRowsBefore(4, datosFinales.length);

  // Pegar datos en hojaDestino desde B11 (fila 4, columna 2)
  hojaDestino.getRange(4, 2, datosFinales.length, datosFinales[0].length).setValues(datosFinales);

  //Borrado de datos existentes
  borrarRangoEnHoja("CSV EFECTIVO", "A5:S");

  SpreadsheetApp.getUi().alert(
    "Datos copiados exitosamente desde 'CSV EFECTIVO' y pegados en 'CONSULTA EFECTIVO' insertando desde B11."
  );
}


/**
 * A partir de unas celdas fijas en "CONTROL EFECTIVO", se añade el efectivo "CONSULTA EFECTIVO"
 * Las celsad son C38 y F38.
 * En caso de añadir filas nuevas, hay que modificar este programa.
 */
function ContabilizarMonedas(){

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hojaOrigen = ss.getSheetByName("CONTROL EFECTIVO");
  var hojaDestino = ss.getSheetByName("CONSULTA EFECTIVO");

  var total = ss.getRangeByName("TOTALmonedas");
  var cuadrante = ss.getRangeByName("Acuadrar");


  if(cuadrante==0 || cuadrante==null){
    SpreadsheetApp.getUi().alert(
    "No se ha añadido cantidad para cuadrar."
    );
    return;
  }

  if(total<cuadrante){
    SpreadsheetApp.getUi().alert(
    "No hay sufucuente efectivo para añadirlo a la contabilidad (mínimo ",total,"€)."
    );
    return;
  }

  const ahora = new Date();
  const fecha = Utilities.formatDate(ahora, Session.getScriptTimeZone(), "dd/MM/yyyy");


  var datosInsertados = [];
  datosInsertados.push([
    /** Caja */ "001-100",
    /** Numero */ "1234",
    /** Fecha */ fecha,
    /** Empleado */ ,
    /** Venta Efectivo */ ,
    /** Venta Tarjeta */ ,
    /** Calculado */ ,
    /** Declarado */ ,
    /** Descuadre */ ,
    /** Retirado */ ,
    /** Salida */ ,
    /** Entrada */ ,
    /** VENTA REAL */ cuadrante,
    /** GASTOS */ ,
    /** COMPARATIVA */ cuadrante*(-1),
    /** CONCEPTO */ , 
    /** DESCRIPCION */ ,
    /** MONTSE */ 0,
    /** COMPRA MERCADERIAS */ 0,
    /** YERAY */ 0
  ]);

  // Insertar filas necesarias desde la fila 4 hacia abajo
  hojaDestino.insertRowsBefore(4, 1);

  // Pegar datos en hojaDestino desde B11 (fila 4, columna 2)
  hojaDestino.getRange(4, 2, datosInsertados.length, datosInsertados[0].length).setValues(datosInsertados);

  //Borrado de datos existentes
  borrarRangoEnHoja("CONTROL EFECTIVO", "F25");

}


/**
 * A partir de unas celdas fijas en "CONTROL EFECTIVO", se añade el gasto a "CONSULTA EFECTIVO"
 * Las celsad son B32, C32 y D32.
 * En caso de añadir filas nuevas, hay que modificar este programa.
 */
function ContabilizarPago(){

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hojaOrigen = ss.getSheetByName("CONTROL EFECTIVO");
  var hojaDestino = ss.getSheetByName("CONSULTA EFECTIVO");

  const especificacion = hojaOrigen.getRange("B44").getValue();
  const concepto = hojaOrigen.getRange("C44").getValue();
  fecha = hojaOrigen.getRange("D44").getValue();
  importe = hojaOrigen.getRange("E44").getValue();
  const descripcion = hojaOrigen.getRange("F44").getValue();


  if(especificacion=="" || especificacion==null || concepto=="" || concepto==null){
    SpreadsheetApp.getUi().alert(
    "Falta información por rellenar."
    );
    return;
  }

  if(especificacion=="" || especificacion==null || concepto=="" || concepto==null){
    SpreadsheetApp.getUi().alert(
    "Falta información por rellenar."
    );
    return;
  }


  if (fecha == 0 || fecha == null) {
    const ui = SpreadsheetApp.getUi();
    const respuesta = ui.alert(
      "Fecha no encontrada",
      "No se ha añadido fecha. ¿Quieres usar la fecha de hoy?",
      ui.ButtonSet.OK_CANCEL
    );

    if (respuesta == ui.Button.OK) {
      const hoy = new Date();
      fecha = Utilities.formatDate(hoy, Session.getScriptTimeZone(), "dd/MM/yyyy");
    } else {
      // Usuario eligió "Cancelar"
      return;
    }
  }

  if(especificacion=="GASTO"){
    if(importe>0) importe=importe*(-1);
    var datosInsertados = [];
    datosInsertados.push([
      /** 1Caja */   "001-111",
      /** 2Numero */ "3333",
      /** 3Fecha */ fecha,
      /** 4Empleado */ ,
      /** 5Venta Efectivo */ ,
      /** 6Venta Tarjeta */ ,
      /** 7Calculado */ ,
      /** 8Declarado */ ,
      /** 9Descuadre */ ,
      /** 0Retirado */ ,
      /** 1Salida */ ,
      /** 2Entrada */ ,
      /** 3VENTA REAL */ ,
      /** 4GASTOS */ importe,
      /** 5COMPARATIVA */ ,
      /** 6CONCEPTO */ concepto, 
      /** 7DESCRIPCION */ descripcion,
      /** 8MONTSE */ ,
      /** 9COMPRA MERCADERIAS */ ,
      /** 0YERAY */ 
    ]);
  }

  if(especificacion=="INGRESO"){
    if(importe<0) importe=importe*(-1);
    var datosInsertados = [];
    datosInsertados.push([
      /** Caja */   "001-111",
      /** Numero */ "3333",
      /** Fecha */ fecha,
      /** Empleado */ ,
      /** Venta Efectivo */ ,
      /** Venta Tarjeta */ ,
      /** Calculado */ ,
      /** Declarado */ ,
      /** Descuadre */ ,
      /** Retirado */ ,
      /** Salida */ ,
      /** Entrada */ ,
      /** VENTA REAL */ importe,
      /** GASTOS */ ,
      /** COMPARATIVA */ ,
      /** CONCEPTO */ concepto, 
      /** DESCRIPCION */ descripcion,
      /** MONTSE */ `=IF(N$4>=70;70;N$4)`,
      /** COMPRA MERCADERIAS */ `=IF(N$4>=140;60;N$4-S$4)`,
      /** YERAY */ `=N$4-S$4-T$4`
    ]);
  }
  

  // Insertar filas necesarias desde la fila 4 hacia abajo
  hojaDestino.insertRowsBefore(4, 1);

  // Pegar datos en hojaDestino desde B11 (fila 4, columna 2)
  hojaDestino.getRange(4, 2, datosInsertados.length, datosInsertados[0].length).setValues(datosInsertados);

  //Borrado de datos existentes
  borrarRangoEnHoja("CONTROL EFECTIVO", "B44:F44");

}

/**
 * A partir de unas celdas fijas en "CONTROL EFECTIVO", se añade el gasto a "CONSULTA EFECTIVO"
 * Las celsad son B32, C32 y D32.
 * En caso de añadir filas nuevas, hay que modificar este programa.
 */
function ControlCaja() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var hojaOrigen = ss.getSheetByName("CONTROL EFECTIVO");
  var hojaDestino = ss.getSheetByName("CONSULTA EFECTIVO");
  
  var datos = hojaOrigen.getRange("B50:F50").getValues()[0];
  var tipoMovimiento = datos[0];   // B50: "SALIDA CAJA" o "ENTRADA CAJA"
  var conceptoNumero = datos[1];   // C50 
  var fechaOriginal = datos[2];    // D50 Fecha
  var importe = datos[3];          // E50 Importe
  var descripcion = datos[4];      // F50 Descripción

  //Verificación de que toda la información esté rellenada
  if(tipoMovimiento=="" || tipoMovimiento==null || conceptoNumero==null || conceptoNumero==""){
    SpreadsheetApp.getUi().alert(
    "Falta información por rellenar."
    )
    return;
  }

  //En caso de que no se haya puesto fecha, preguntar si utilizar la actual 
  if (fechaOriginal == 0 || fechaOriginal == null) {
    const ui = SpreadsheetApp.getUi();
    const respuesta = ui.alert(
      "No se ha añadido fecha. ¿Quieres usar la fecha de hoy?",
      ui.ButtonSet.OK_CANCEL
    );

    if (respuesta == ui.Button.OK) {
      fechaOriginal = new Date(); // Usar objeto Date, no string
    } else {
      return;
    }
  }
  
  //En caso de que el importe sea 0, preguntar si utilizar 0€ 
  if (importe == 0 || importe == null) {
    const ui = SpreadsheetApp.getUi();
    const respuesta = ui.alert(
      "¿Seguro que quieres añadir un importe de 0€?",
      ui.ButtonSet.OK_CANCEL
    );

    if (respuesta == ui.Button.OK) {
      importe = 0;
    } else {
      return;
    }
  }

  
  // === BLOQUE 2: Convertir fecha de formato Date a "aaaa-mm-dd" ===
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var tz = ss.getSpreadsheetTimeZone();
  var fechaFormateada = Utilities.formatDate(fechaOriginal, ss.getSpreadsheetTimeZone(), "yyyy-MM-dd");
  

  // === BLOQUE 3: Lógica para "SALIDA CAJA" ===
  if (tipoMovimiento === "SALIDA CAJA") {
    if(importe>0)importe=importe*(-1);
    var datosInsertados = [];
    datosInsertados.push([
      /** Caja */   "100-100",
      /** Numero */ fechaFormateada,
      /** Fecha */ ,
      /** Empleado */ ,
      /** Venta Efectivo */ ,
      /** Venta Tarjeta */ ,
      /** Calculado */ ,
      /** Declarado */ ,
      /** Descuadre */ ,
      /** Retirado */ ,
      /** Salida */ importe,
      /** Entrada */ ,
      /** VENTA REAL */ ,
      /** GASTOS */ ,
      /** COMPARATIVA */ ,
      /** CONCEPTO */ conceptoNumero, 
      /** DESCRIPCION */ ,
      /** MONTSE */ ,
      /** COMPRA MERCADERIAS */ ,
      /** YERAY */ 
    ]);

    // Insertar filas necesarias desde la fila 4 hacia abajo
    hojaDestino.insertRowsBefore(4, 1);

    // Pegar datos en hojaDestino desde B11 (fila 4, columna 2)
    hojaDestino.getRange(4, 2, datosInsertados.length, datosInsertados[0].length).setValues(datosInsertados);

  }

  // === BLOQUE 4: Lógica para "ENTRADA CAJA" ===
  if (tipoMovimiento === "ENTRADA CAJA") {
    var insertado = false; // Variable booleana para verificar si se insertó algo
    
    // Obtenemos todos los valores desde B4 hasta U (según longitud de la hoja)
    var ultimaFila = hojaDestino.getLastRow();
    var rangoTabla = hojaDestino.getRange(4, 2, ultimaFila - 3, 20).getValues(); // 20 columnas: B a U

    // El concepto está formateado en mofo fecha. Convertirlo en el formato escrito para poder leerlo
    if(conceptoNumero != null && conceptoNumero != ""){
      var conceptoNumeroFormateado = Utilities.formatDate(conceptoNumero, Session.getScriptTimeZone(), "yyyy-MM-dd");
    }

    // Recorremos la tabla buscando coincidencia en la columna C absoluta (índice 1 de rangoTabla)
    for (var i = 0; i < rangoTabla.length; i++) {

      if(rangoTabla[i][1] != null && rangoTabla[i][1] != ""){
        var datoTabla = Utilities.formatDate(rangoTabla[i][1], Session.getScriptTimeZone(), "yyyy-MM-dd");
      }

      if (datoTabla == conceptoNumeroFormateado) { // columna C de la hoja
        var filaDestino = i + 4; // Ajustar índice a número de fila real
        if(importe+rangoTabla[i][10]>0){
          SpreadsheetApp.getUi().alert("El importe es más grande que la salida.");
          return;
        }
        hojaDestino.getRange(filaDestino, 4).setValue(fechaFormateada); // Columna D
        hojaDestino.getRange(filaDestino, 13).setValue(importe);        // Columna M
        hojaDestino.getRange(filaDestino, 15).setValue(`=L${i+4}+M${i+4}`);        // Columna O
        hojaDestino.getRange(filaDestino, 18).setValue(descripcion);    // Columna R
        
        insertado = true; // Marcamos que se insertó
        SpreadsheetApp.getUi().alert("Datos insertados en la fila " + filaDestino + ".");
        break; // Salimos tras encontrar la coincidencia
      }
    }
    
    // Si no se insertó nada, notificamos
    if (!insertado) {
      SpreadsheetApp.getUi().alert("No se encontró ninguna coincidencia para la Fecha Referencia: " + conceptoNumeroFormateado);
      return;
    }
  }

  //Borrado de datos existentes
  borrarRangoEnHoja("CONTROL EFECTIVO", "B50:F50");

}


function compararFechas(rango1, rango2) {
  if (!rango1 || !rango2) return "Rangos vacíos";

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var tz = ss.getSpreadsheetTimeZone();

  // Convertir los rangos a listas de fechas válidas
  var fechas1 = rango1
    .flat()
    .filter(f => f instanceof Date)
    .map(f => Utilities.formatDate(f, tz, "dd/MM/yyyy"));

  var fechas2 = rango2
    .flat()
    .filter(f => f instanceof Date)
    .map(f => Utilities.formatDate(f, tz, "dd/MM/yyyy"));

  if (fechas1.length === 0 || fechas2.length === 0) return "Sin fechas válidas";

  // Encontrar coincidencias
  var setFechas2 = new Set(fechas2);
  var coincidencias = fechas1.filter(f => setFechas2.has(f));

  if (coincidencias.length === 0) return "Sin coincidencias";

  // Pasar coincidencias a Date para ordenar
  var fechasOrdenadas = coincidencias
    .map(f => {
      var partes = f.split("/");
      return new Date(partes[2], partes[1] - 1, partes[0]);
    })
    .sort((a, b) => a - b);

  // Primera y última fecha
  var primera = fechasOrdenadas[0];
  var ultima = fechasOrdenadas[fechasOrdenadas.length - 1];

  return Utilities.formatDate(primera, tz, "dd/MM/yyyy") + " - " +
         Utilities.formatDate(ultima, tz, "dd/MM/yyyy");
}
