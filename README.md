# Calcu-len.D

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-000000?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Convertidor de ARS a múltiples monedas con UI estática y backend en FastAPI.

## Qué incluye
- Frontend estático (`public/`) sin frameworks.
- Backend en **FastAPI** (`api/index.py`) desplegable en Vercel.
- Conversión ARS → USD con mercado local (`/api/convert`).
- Conversión ARS → FX internacional (`/api/convert-fx`) para:
  - BRL, EUR (Italia y Francia), CAD, AUD, CNY, PEN, GBP, PYG, MXN, UAH, RUB.
- Selector de monedas con símbolo monetario (ej: €, £, ¥, R$, ₲, MX$, ₴, ₽) para mejor legibilidad.
- Favicon SVG custom con identidad de Calcu-len.D.

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
