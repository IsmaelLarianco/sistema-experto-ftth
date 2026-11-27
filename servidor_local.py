"""Servidor local para desarrollo: sirve public/ y expone /api/diagnosticar.

Uso:  python servidor_local.py   ->  http://localhost:8000
"""

import json
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from sistema_experto.motor import diagnosticar

PUBLICO = Path(__file__).parent / "public"


class Manejador(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.split("?")[0] != "/api/diagnosticar":
            self.send_error(404)
            return
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            entrada = json.loads(self.rfile.read(largo).decode("utf-8"))
            codigo, datos = 200, diagnosticar(entrada)
        except (ValueError, json.JSONDecodeError) as exc:
            codigo, datos = 400, {"error": str(exc)}
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", 8000), partial(Manejador, directory=str(PUBLICO)))
    print("Sistema experto FTTH/GPON en http://localhost:8000  (Ctrl+C para salir)")
    servidor.serve_forever()
