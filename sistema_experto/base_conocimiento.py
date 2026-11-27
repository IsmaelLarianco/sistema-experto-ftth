"""Base de conocimiento del sistema experto FTTH/GPON.

Contiene:
  - UMBRALES: niveles de potencia óptica (dBm) usados para clasificar lecturas.
  - CAUSAS: catálogo de causas probables con descripción y acciones sugeridas.
  - REGLAS: reglas de producción SI <condiciones> ENTONCES <causa> con factor
    de certeza (CF entre 0 y 1).

Los umbrales corresponden a GPON clase B+ (ITU-T G.984.2). Ajústalos a las
especificaciones de tu operador/equipos.
"""

from dataclasses import dataclass
from typing import Callable

# --------------------------------------------------------------------------
# Umbrales de potencia (dBm)
# --------------------------------------------------------------------------
UMBRALES = {
    "ont_sobrecarga": -8.0,   # Rx ONT por encima: saturación del receptor
    "ont_normal_min": -25.0,  # Rx ONT entre -8 y -25: operación sana
    "ont_critico": -28.0,     # Rx ONT por debajo: sin margen / errores
    "olt_bajo": -27.0,        # Rx OLT (upstream) por debajo: ONT transmite débil
}

ALCANCES = ("una_ont", "varias_splitter", "todo_puerto_pon", "varios_puertos")
ALARMAS = ("LOS", "DYING_GASP", "LOF", "HIGH_BER", "ONT_OFFLINE")
CONTEXTOS = ("obras", "manipulacion", "lluvia", "instalacion_nueva")


# --------------------------------------------------------------------------
# Catálogo de causas
# --------------------------------------------------------------------------
CAUSAS = {
    "corte_drop": {
        "nombre": "Corte o daño en la fibra drop del cliente",
        "descripcion": "La acometida entre la caja terminal (NAP) y la ONT está cortada, "
                       "aplastada o con el conector arrancado.",
        "acciones": [
            "Inspeccionar visualmente el tendido del drop y el punto de ingreso a la vivienda.",
            "Usar un localizador visual de fallas (VFL) desde la ONT y buscar la fuga de luz roja.",
            "Medir con OTDR desde la NAP hacia el cliente para ubicar la distancia del corte.",
            "Reemplazar el tramo de drop o reconectorizar y volver a medir Rx.",
        ],
    },
    "corte_distribucion": {
        "nombre": "Corte en la red de distribución (después del splitter)",
        "descripcion": "Varios clientes del mismo splitter perdieron señal: el corte está "
                       "en el tramo común hacia ellos.",
        "acciones": [
            "Verificar en la NAP/splitter si hay luz en la entrada y en cada salida.",
            "Revisar postes, cámaras y cajas de empalme del tramo afectado (accidentes, obras).",
            "Medir con OTDR desde el splitter hacia los clientes afectados.",
            "Reparar con empalme por fusión y reportar el evento.",
        ],
    },
    "corte_troncal": {
        "nombre": "Corte en fibra troncal/alimentadora",
        "descripcion": "Todo el puerto PON (o varios) perdió señal: la falla está antes del "
                       "splitter primario, en el tramo entre la OLT y la red de distribución.",
        "acciones": [
            "Confirmar en la OLT que el puerto PON no tiene potencia de retorno.",
            "Medir con OTDR desde la OLT/ODF hacia la red para ubicar la distancia del corte.",
            "Despachar cuadrilla de emergencia al punto estimado y activar plan de contingencia.",
            "Después de reparar, validar la potencia de todas las ONT del puerto.",
        ],
    },
    "ont_sin_energia": {
        "nombre": "ONT sin energía (corte eléctrico o fuente dañada)",
        "descripcion": "El mensaje Dying Gasp indica que la ONT avisó que se quedó sin "
                       "alimentación antes de caer. La fibra probablemente está bien.",
        "acciones": [
            "Confirmar con el cliente si hubo corte de luz o si el adaptador está desconectado.",
            "Verificar el adaptador de corriente y el tomacorriente.",
            "Si hay energía y la ONT no enciende, reemplazar fuente o ONT.",
        ],
    },
    "puerto_olt_falla": {
        "nombre": "Falla en el puerto PON o transceptor óptico de la OLT",
        "descripcion": "El puerto o su módulo SFP/XFP pudo degradarse o fallar.",
        "acciones": [
            "Revisar el estado y la potencia de transmisión del transceptor en la OLT.",
            "Limpiar el conector del patchcord de la OLT y del ODF.",
            "Mover el servicio a un puerto de respaldo o reemplazar el módulo óptico.",
        ],
    },
    "olt_falla": {
        "nombre": "Falla de tarjeta/equipo OLT",
        "descripcion": "Varios puertos PON sin servicio al mismo tiempo apuntan a la "
                       "tarjeta de línea, la alimentación o el uplink de la OLT.",
        "acciones": [
            "Revisar alarmas de la tarjeta de servicio, energía y temperatura de la OLT.",
            "Verificar el uplink y la sincronización del equipo.",
            "Escalar a soporte del fabricante y evaluar reinicio controlado de la tarjeta.",
        ],
    },
    "conector_sucio": {
        "nombre": "Conector sucio o mal acoplado",
        "descripcion": "Polvo, grasa o un acople flojo en el conector (ONT, roseta, NAP) "
                       "atenúa la señal de forma moderada.",
        "acciones": [
            "Inspeccionar la ferrule con videoscopio o microscopio de fibra.",
            "Limpiar con limpiador de un toque o alcohol isopropílico y toallita sin pelusa.",
            "Reconectar firmemente y volver a medir Rx en la ONT.",
            "Si no mejora, cambiar el patchcord o el adaptador.",
        ],
    },
    "fibra_doblada": {
        "nombre": "Fibra doblada o con curvatura excesiva (macrobending)",
        "descripcion": "Un doblez cerrado o un aplastamiento deja escapar luz y baja la "
                       "potencia; suele ser intermitente si el cable se mueve.",
        "acciones": [
            "Revisar el recorrido buscando dobleces, grapas apretadas o cables pisados.",
            "Usar un VFL y buscar puntos donde la luz roja se escapa por el cable.",
            "Respetar el radio mínimo de curvatura (≈ 30 mm en fibra G.657.A1; 15 mm en A2).",
            "Reacomodar o reemplazar el tramo dañado y confirmar la mejora de Rx.",
        ],
    },
    "splitter_danado": {
        "nombre": "Splitter óptico dañado o con pérdida excesiva",
        "descripcion": "El splitter introduce más atenuación de la esperada (1:8 ≈ 10,5 dB; "
                       "1:16 ≈ 13,5 dB) por daño, conector sucio o puerto defectuoso.",
        "acciones": [
            "Medir potencia a la entrada y a la salida del splitter con power meter.",
            "Comparar la pérdida real con el valor teórico de la relación de división.",
            "Limpiar e inspeccionar los conectores del splitter.",
            "Reemplazar el splitter si la pérdida excede la especificación.",
        ],
    },
    "empalme_degradado": {
        "nombre": "Empalme o conector de red con pérdida alta",
        "descripcion": "Empalmes por fusión deficientes, muflas con humedad o conectores en "
                       "ODF/NAP agregan atenuación acumulada al enlace.",
        "acciones": [
            "Ejecutar OTDR y buscar eventos con pérdida mayor a 0,3 dB por empalme.",
            "Reabrir y rehacer los empalmes con pérdida alta.",
            "Revisar sellado de muflas y cajas (ingreso de agua).",
        ],
    },
    "empalme_defectuoso": {
        "nombre": "Atenuación excesiva por mala ejecución de la instalación",
        "descripcion": "Potencia muy baja con un solo cliente sugiere pérdidas acumuladas "
                       "(empalmes, conectores mecánicos, distancia) en su acometida.",
        "acciones": [
            "Medir la pérdida de cada tramo con power meter o OTDR.",
            "Revisar conectores mecánicos y empalmes del drop.",
            "Verificar que el presupuesto óptico no supere el máximo del equipo.",
        ],
    },
    "humedad_empalme": {
        "nombre": "Ingreso de agua en caja o empalme",
        "descripcion": "La lluvia puede revelar cajas, muflas o conectores mal sellados que "
                       "aumentan la atenuación.",
        "acciones": [
            "Revisar el sellado de cajas terminales, muflas y pasacables.",
            "Secar, limpiar y volver a sellar; reemplazar gel o selladores vencidos.",
            "Comparar la potencia antes y después de la intervención.",
        ],
    },
    "sobrecarga_optica": {
        "nombre": "Sobrecarga óptica en la ONT",
        "descripcion": "La potencia de recepción supera el máximo del receptor (≈ -8 dBm) "
                       "y puede causar errores o caídas.",
        "acciones": [
            "Revisar si el cliente está muy cerca de la OLT o si falta splitter en el tramo.",
            "Instalar un atenuador óptico fijo (5–10 dB) antes de la ONT.",
            "Confirmar que Rx queda en el rango sano (-8 a -25 dBm).",
        ],
    },
    "ont_falla": {
        "nombre": "ONT defectuosa o mal provisionada",
        "descripcion": "La potencia óptica es correcta pero la ONT muestra errores o está "
                       "fuera de línea: puede ser fallo de hardware, firmware o registro.",
        "acciones": [
            "Reiniciar la ONT y verificar su estado de registro (SN/LOID) en la OLT.",
            "Revisar el perfil de servicio y la VLAN aprovisionada.",
            "Actualizar el firmware o reemplazar la ONT si persiste.",
        ],
    },
    "ont_rogue": {
        "nombre": "ONT rogue (transmite fuera de su ventana)",
        "descripcion": "Una ONT con el láser siempre encendido interfiere a las demás del "
                       "mismo puerto PON y causa errores aun con buena potencia.",
        "acciones": [
            "Revisar en la OLT alarmas de interferencia o rogue ONU.",
            "Aislar ONT por ONT (apagando o desactivando) hasta que el puerto se normalice.",
            "Reemplazar la ONT con láser fijo.",
        ],
    },
    "ont_tx_degradado": {
        "nombre": "Transmisor de la ONT degradado (upstream débil)",
        "descripcion": "La ONT recibe bien pero la OLT recibe poco de ella: el láser de "
                       "subida está envejecido o hay un conector sucio en el sentido de retorno.",
        "acciones": [
            "Medir la potencia de transmisión de la ONT con power meter.",
            "Limpiar los conectores de la ONT y de la roseta.",
            "Reemplazar la ONT si la potencia de salida es menor a la especificada.",
        ],
    },
    "sin_falla_optica": {
        "nombre": "El enlace óptico está sano: revisar capas superiores",
        "descripcion": "Potencia y alarmas normales. El problema probablemente está en "
                       "Wi-Fi, router, configuración de servicio o equipos del cliente.",
        "acciones": [
            "Probar con cable Ethernet directo a la ONT/router.",
            "Revisar perfil de velocidad, VLAN y autenticación (PPPoE/IPoE).",
            "Revisar el Wi-Fi: canal, interferencia, cantidad de dispositivos.",
        ],
    },
}


# --------------------------------------------------------------------------
# Reglas de producción
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Regla:
    id: str
    si: str                      # texto legible de la condición
    causa: str                   # clave de CAUSAS
    cf: float                    # factor de certeza de la regla (0-1)
    cond: Callable[[dict], bool]


def _pot_baja(h):
    return h["rx_nivel"] in ("bajo", "critico")


REGLAS = [
    # ---- Pérdida total de señal (LOS) ----
    Regla("R01", "LOS en una sola ONT, sin Dying Gasp y sin intermitencia",
          "corte_drop", 0.60,
          lambda h: h["los"] and h["alcance"] == "una_ont" and not h["dying_gasp"] and not h["intermitente"]),
    Regla("R02", "LOS en una sola ONT y hubo obras cerca",
          "corte_drop", 0.30,
          lambda h: h["los"] and h["alcance"] == "una_ont" and not h["dying_gasp"] and "obras" in h["contexto"]),
    Regla("R03", "LOS en una sola ONT precedido de Dying Gasp",
          "ont_sin_energia", 0.80,
          lambda h: h["los"] and h["alcance"] == "una_ont" and h["dying_gasp"]),
    Regla("R04", "LOS intermitente en una sola ONT",
          "fibra_doblada", 0.35,
          lambda h: h["los"] and h["alcance"] == "una_ont" and h["intermitente"] and not h["dying_gasp"]),
    Regla("R05", "LOS intermitente en una sola ONT",
          "conector_sucio", 0.30,
          lambda h: h["los"] and h["alcance"] == "una_ont" and h["intermitente"] and not h["dying_gasp"]),
    Regla("R06", "LOS en una sola ONT con lluvia",
          "humedad_empalme", 0.25,
          lambda h: h["los"] and h["alcance"] == "una_ont" and "lluvia" in h["contexto"] and not h["dying_gasp"]),
    Regla("R07", "LOS en varios clientes del mismo splitter",
          "corte_distribucion", 0.70,
          lambda h: h["los"] and h["alcance"] == "varias_splitter"),
    Regla("R08", "LOS en varios clientes del splitter y hubo obras cerca",
          "corte_distribucion", 0.20,
          lambda h: h["los"] and h["alcance"] == "varias_splitter" and "obras" in h["contexto"]),
    Regla("R09", "LOS en todo el puerto PON",
          "corte_troncal", 0.60,
          lambda h: h["los"] and h["alcance"] == "todo_puerto_pon"),
    Regla("R10", "LOS en todo el puerto PON",
          "puerto_olt_falla", 0.25,
          lambda h: h["los"] and h["alcance"] == "todo_puerto_pon"),
    Regla("R11", "LOS en varios puertos de la OLT",
          "olt_falla", 0.65,
          lambda h: h["los"] and h["alcance"] == "varios_puertos"),
    Regla("R12", "LOS en varios puertos de la OLT",
          "corte_troncal", 0.40,
          lambda h: h["los"] and h["alcance"] == "varios_puertos"),

    # ---- Potencia baja (hay señal pero degradada) ----
    Regla("R13", "Potencia Rx baja en una sola ONT, estable",
          "conector_sucio", 0.50,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] == "una_ont" and not h["intermitente"]),
    Regla("R14", "Potencia Rx baja en una sola ONT tras manipulación del cliente",
          "fibra_doblada", 0.55,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] == "una_ont" and "manipulacion" in h["contexto"]),
    Regla("R15", "Potencia Rx baja e intermitente en una sola ONT",
          "fibra_doblada", 0.50,
          lambda h: _pot_baja(h) and h["alcance"] == "una_ont" and h["intermitente"]),
    Regla("R16", "Potencia Rx baja e intermitente en una sola ONT",
          "conector_sucio", 0.30,
          lambda h: _pot_baja(h) and h["alcance"] == "una_ont" and h["intermitente"]),
    Regla("R17", "Potencia Rx crítica (menor a -28 dBm) en una sola ONT",
          "empalme_defectuoso", 0.35,
          lambda h: h["rx_nivel"] == "critico" and not h["los"] and h["alcance"] == "una_ont"),
    Regla("R18", "Potencia Rx baja en varios clientes del mismo splitter",
          "splitter_danado", 0.55,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] == "varias_splitter"),
    Regla("R19", "Potencia Rx baja en varios clientes del mismo splitter",
          "empalme_degradado", 0.30,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] == "varias_splitter"),
    Regla("R20", "Potencia Rx baja en todo el puerto PON",
          "empalme_degradado", 0.45,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] in ("todo_puerto_pon", "varios_puertos")),
    Regla("R21", "Potencia Rx baja en todo el puerto PON",
          "splitter_danado", 0.35,
          lambda h: _pot_baja(h) and not h["los"] and h["alcance"] in ("todo_puerto_pon", "varios_puertos")),
    Regla("R22", "Potencia Rx baja con lluvia",
          "humedad_empalme", 0.40,
          lambda h: _pot_baja(h) and "lluvia" in h["contexto"]),
    Regla("R23", "Potencia Rx baja en una instalación nueva",
          "conector_sucio", 0.35,
          lambda h: _pot_baja(h) and "instalacion_nueva" in h["contexto"]),
    Regla("R24", "Potencia Rx baja en una instalación nueva",
          "empalme_defectuoso", 0.30,
          lambda h: _pot_baja(h) and "instalacion_nueva" in h["contexto"]),

    # ---- Potencia alta ----
    Regla("R25", "Potencia Rx por encima de -8 dBm",
          "sobrecarga_optica", 0.85,
          lambda h: h["rx_nivel"] == "sobrecarga"),

    # ---- Potencia normal pero con síntomas ----
    Regla("R26", "Rx normal con BER alto o LOF en una sola ONT",
          "ont_falla", 0.55,
          lambda h: h["rx_nivel"] == "normal" and (h["high_ber"] or h["lof"]) and h["alcance"] == "una_ont"),
    Regla("R27", "Rx normal con BER alto o LOF en varios clientes del puerto",
          "ont_rogue", 0.60,
          lambda h: h["rx_nivel"] == "normal" and (h["high_ber"] or h["lof"]) and h["alcance"] != "una_ont"),
    Regla("R28", "ONT fuera de línea con potencia Rx normal",
          "ont_falla", 0.45,
          lambda h: h["rx_nivel"] == "normal" and h["ont_offline"] and not h["los"]),
    Regla("R29", "Rx normal en la ONT pero Rx bajo en la OLT (upstream débil)",
          "ont_tx_degradado", 0.60,
          lambda h: h["rx_nivel"] == "normal" and h["olt_nivel"] == "bajo"),
    Regla("R30", "Rx normal, sin alarmas ópticas",
          "sin_falla_optica", 0.70,
          lambda h: h["rx_nivel"] == "normal" and not h["los"] and not h["high_ber"]
          and not h["lof"] and not h["ont_offline"] and h["olt_nivel"] != "bajo"),
]
