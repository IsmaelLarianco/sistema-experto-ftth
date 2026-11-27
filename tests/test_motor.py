import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sistema_experto.motor import diagnosticar, normalizar  # noqa: E402


def principal(entrada):
    return diagnosticar(entrada)["diagnosticos"][0]["causa"]


class PruebasMotor(unittest.TestCase):
    def test_corte_de_drop(self):
        self.assertEqual(principal({"alarmas": ["LOS"], "alcance": "una_ont"}), "corte_drop")

    def test_dying_gasp_es_ont_sin_energia(self):
        self.assertEqual(
            principal({"alarmas": ["LOS", "DYING_GASP"], "alcance": "una_ont"}),
            "ont_sin_energia",
        )

    def test_conector_sucio(self):
        self.assertEqual(principal({"rx_ont": -26.5, "alcance": "una_ont"}), "conector_sucio")

    def test_fibra_doblada_tras_manipulacion(self):
        r = principal({"rx_ont": -27, "alcance": "una_ont", "contexto": ["manipulacion"]})
        self.assertEqual(r, "fibra_doblada")

    def test_splitter_danado(self):
        self.assertEqual(principal({"rx_ont": -27, "alcance": "varias_splitter"}), "splitter_danado")

    def test_corte_troncal(self):
        self.assertEqual(principal({"alarmas": ["LOS"], "alcance": "todo_puerto_pon"}), "corte_troncal")

    def test_sobrecarga(self):
        self.assertEqual(principal({"rx_ont": -4}), "sobrecarga_optica")

    def test_enlace_sano(self):
        self.assertEqual(principal({"rx_ont": -20}), "sin_falla_optica")

    def test_combinacion_de_certeza(self):
        # R01 (0.60) + R02 (0.30) -> 0.60 + 0.30 * 0.40 = 0.72
        d = diagnosticar({"alarmas": ["LOS"], "alcance": "una_ont", "contexto": ["obras"]})
        self.assertEqual(d["diagnosticos"][0]["confianza"], 72)

    def test_entradas_invalidas(self):
        with self.assertRaises(ValueError):
            normalizar({"rx_ont": "abc"})
        with self.assertRaises(ValueError):
            normalizar({"alcance": "inexistente"})
        with self.assertRaises(ValueError):
            normalizar({"alarmas": ["FOO"]})


if __name__ == "__main__":
    unittest.main()
