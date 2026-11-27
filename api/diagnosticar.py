"""Endpoint serverless para Vercel: POST /api/diagnosticar

Recibe JSON con los síntomas y devuelve el diagnóstico del sistema experto.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from sistema_experto.base_conocimiento import REGLAS  # noqa: E402
from sistema_experto.motor import diagnosticar  # noqa: E402

MAX_BYTES = 10_000


class handler(BaseHTTPRequestHandler):
    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        self._responder(204, {})

    def do_GET(self):
        self._responder(200, {
            "servicio": "Sistema experto FTTH/GPON",
            "reglas": len(REGLAS),
            "uso": "POST con JSON: rx_ont, rx_olt, alcance, alarmas, intermitente, contexto",
        })

    def do_POST(self):
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            if largo <= 0 or largo > MAX_BYTES:
                raise ValueError("Cuerpo vacío o demasiado grande.")
            entrada = json.loads(self.rfile.read(largo).decode("utf-8"))
            self._responder(200, diagnosticar(entrada))
        except json.JSONDecodeError:
            self._responder(400, {"error": "El cuerpo no es un JSON válido."})
        except ValueError as exc:
            self._responder(400, {"error": str(exc)})
        except Exception:  # noqa: BLE001
            self._responder(500, {"error": "Error interno del servidor."})
