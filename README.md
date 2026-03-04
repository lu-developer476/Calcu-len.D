# Calcu-len.D — ARS → Monedas (FastAPI + Vercel)

Convertidor de ARS a múltiples monedas con UI estática y backend en FastAPI.

## Qué incluye
- Frontend estático (`public/`) sin frameworks.
- Backend en **FastAPI** (`api/index.py`) desplegable en Vercel.
- Conversión ARS → USD con mercado local (`/api/convert`).
- Conversión ARS → FX internacional (`/api/convert-fx`) para:
  - BRL, EUR, CAD, AUD, CNY, PEN, GBP, PYG.
- Selector de monedas con símbolo monetario (ej: €, £, ¥, R$, ₲) para mejor legibilidad.

## Requisitos (local)
- Python 3.11+ recomendado

## Ejecutar local
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
```

Luego abrí:
- Frontend: http://localhost:8000 (si servís estáticos con otro server) o abrí `public/index.html`
- API docs: http://localhost:8000/docs

## Endpoints
- `GET /api/health`
- `GET /api/rate?casa=oficial|blue|...`
- `GET /api/convert?ars=100000&casa=oficial&lado=venta`
- `GET /api/convert-fx?ars=100000&target=EUR`

## Tests
```bash
python -m unittest discover -s tests -v
python -m compileall api tests
```

## Fuentes de datos
- ARS/USD local por mercado: https://dolarapi.com
- FX internacional: https://open.er-api.com
