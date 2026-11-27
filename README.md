# Diagnóstico de fallas FTTH/GPON (sistema experto)

Sistema experto en **Python** que, a partir de síntomas de una red de fibra óptica
(potencia Rx en ONT/OLT, alarmas LOS, Dying Gasp, BER, alcance de la falla y contexto),
deduce la **causa más probable** y sugiere las acciones de campo en orden.

- **Motor:** encadenamiento hacia adelante con reglas SI-ENTONCES.
- **Incertidumbre:** factores de certeza estilo MYCIN (`CF = CF1 + CF2 · (1 − CF1)`).
- **Explicabilidad:** cada diagnóstico muestra las reglas que lo respaldan.
- **Despliegue:** interfaz HTML estática + función serverless de Python en Vercel.
- **Dependencias:** ninguna (solo librería estándar).

## Estructura

```
├── api/diagnosticar.py          # Endpoint serverless (Vercel)
├── public/index.html            # Interfaz web
├── sistema_experto/
│   ├── base_conocimiento.py     # Umbrales, causas y reglas
│   └── motor.py                 # Motor de inferencia
├── tests/test_motor.py          # Pruebas unitarias
├── servidor_local.py            # Servidor de desarrollo
└── vercel.json
```

## Probar en local

```bash
python servidor_local.py
# abrir http://localhost:8000
```

Pruebas:

```bash
python -m unittest discover -s tests -v
```

## Desplegar en Vercel

1. Sube el proyecto a GitHub:
   ```bash
   git init
   git add .
   git commit -m "Sistema experto FTTH/GPON"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/diagnostico-ftth.git
   git push -u origin main
   ```
2. En [vercel.com/new](https://vercel.com/new) importa el repositorio.
3. Deja **Framework Preset: Other** y despliega. No requiere configuración adicional.

## API

`POST /api/diagnosticar`

```json
{
  "rx_ont": -26.5,
  "rx_olt": -22.0,
  "alcance": "una_ont",
  "alarmas": ["HIGH_BER"],
  "intermitente": false,
  "contexto": ["manipulacion"]
}
```

| Campo | Valores |
|---|---|
| `alcance` | `una_ont`, `varias_splitter`, `todo_puerto_pon`, `varios_puertos` |
| `alarmas` | `LOS`, `DYING_GASP`, `LOF`, `HIGH_BER`, `ONT_OFFLINE` |
| `contexto` | `obras`, `manipulacion`, `lluvia`, `instalacion_nueva` |

## Cómo extenderlo

Agrega una causa en `CAUSAS` y una `Regla` en `REGLAS` (`sistema_experto/base_conocimiento.py`).
Ajusta `UMBRALES` según las especificaciones de tu operador y equipos (OLT/ONT).

> Proyecto educativo: las reglas y umbrales son una base de conocimiento inicial
> y deben validarse con técnicos e ingenieros antes de usarse en operación real.
