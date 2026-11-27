"""Motor de inferencia: encadenamiento hacia adelante con factores de certeza.

Flujo:
  1. normalizar(): valida la entrada y deriva hechos (p. ej. nivel de potencia).
  2. Se evalúan todas las reglas; las que se cumplen aportan un CF a su causa.
  3. Los CF de la misma causa se combinan al estilo MYCIN:
         CF = CF1 + CF2 * (1 - CF1)
  4. Se devuelven las causas ordenadas por confianza, con las reglas que las
     respaldan (explicación) y las acciones sugeridas.
"""

from .base_conocimiento import (
    ALARMAS, ALCANCES, CAUSAS, CONTEXTOS, REGLAS, UMBRALES,
)

CONFIANZA_MINIMA = 0.20


def _a_float(valor, campo):
    if valor is None or valor == "":
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"'{campo}' debe ser un número en dBm.")
    if not -60.0 <= numero <= 10.0:
        raise ValueError(f"'{campo}' fuera de rango razonable (-60 a +10 dBm).")
    return numero


def _nivel_ont(rx):
    if rx is None:
        return "desconocido"
    if rx > UMBRALES["ont_sobrecarga"]:
        return "sobrecarga"
    if rx >= UMBRALES["ont_normal_min"]:
        return "normal"
    if rx >= UMBRALES["ont_critico"]:
        return "bajo"
    return "critico"


def _nivel_olt(rx):
    if rx is None:
        return "desconocido"
    return "bajo" if rx < UMBRALES["olt_bajo"] else "normal"


def normalizar(entrada):
    """Valida la entrada del usuario y construye el diccionario de hechos."""
    if not isinstance(entrada, dict):
        raise ValueError("La entrada debe ser un objeto JSON.")

    rx_ont = _a_float(entrada.get("rx_ont"), "rx_ont")
    rx_olt = _a_float(entrada.get("rx_olt"), "rx_olt")

    alcance = entrada.get("alcance") or "una_ont"
    if alcance not in ALCANCES:
        raise ValueError(f"'alcance' debe ser uno de: {', '.join(ALCANCES)}.")

    alarmas = {str(a).upper() for a in (entrada.get("alarmas") or [])}
    desconocidas = alarmas - set(ALARMAS)
    if desconocidas:
        raise ValueError(f"Alarmas no reconocidas: {', '.join(sorted(desconocidas))}.")

    contexto = {str(c).lower() for c in (entrada.get("contexto") or [])}
    desconocidos = contexto - set(CONTEXTOS)
    if desconocidos:
        raise ValueError(f"Contextos no reconocidos: {', '.join(sorted(desconocidos))}.")

    los = "LOS" in alarmas
    return {
        "rx_ont": rx_ont,
        "rx_olt": rx_olt,
        "rx_nivel": "sin_senal" if los and rx_ont is None else _nivel_ont(rx_ont),
        "olt_nivel": _nivel_olt(rx_olt),
        "alcance": alcance,
        "intermitente": bool(entrada.get("intermitente")),
        "los": los,
        "dying_gasp": "DYING_GASP" in alarmas,
        "lof": "LOF" in alarmas,
        "high_ber": "HIGH_BER" in alarmas,
        "ont_offline": "ONT_OFFLINE" in alarmas,
        "contexto": contexto,
    }


def _combinar(a, b):
    return a + b * (1 - a)


def _faltantes(h):
    """Datos que mejorarían el diagnóstico."""
    sugerencias = []
    if h["rx_ont"] is None and not h["los"]:
        sugerencias.append("Ingresa la potencia Rx de la ONT (dBm): es el dato más útil.")
    if h["rx_olt"] is None:
        sugerencias.append("Si puedes, agrega la potencia Rx en la OLT para evaluar el sentido de subida.")
    if h["alcance"] == "una_ont":
        sugerencias.append("Confirma si hay otros clientes afectados en el mismo splitter o puerto PON.")
    return sugerencias


def diagnosticar(entrada):
    h = normalizar(entrada)

    acumulado = {}  # causa -> {"cf": float, "reglas": [...]}
    for regla in REGLAS:
        if regla.cond(h):
            item = acumulado.setdefault(regla.causa, {"cf": 0.0, "reglas": []})
            item["cf"] = _combinar(item["cf"], regla.cf)
            item["reglas"].append({"id": regla.id, "si": regla.si, "cf": regla.cf})

    diagnosticos = []
    for causa, item in sorted(acumulado.items(), key=lambda kv: kv[1]["cf"], reverse=True):
        if item["cf"] < CONFIANZA_MINIMA:
            continue
        info = CAUSAS[causa]
        diagnosticos.append({
            "causa": causa,
            "nombre": info["nombre"],
            "descripcion": info["descripcion"],
            "acciones": info["acciones"],
            "confianza": round(item["cf"] * 100),
            "reglas": item["reglas"],
        })

    hechos = {k: (sorted(v) if isinstance(v, set) else v) for k, v in h.items()}
    return {
        "hechos": hechos,
        "diagnosticos": diagnosticos,
        "faltantes": _faltantes(h),
    }
