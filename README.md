# Peso → Dólar (Python + FastAPI) — Deploy en Vercel

Convertidor de ARS a USD usando cotizaciones en tiempo real (DolarApi.com).

## Qué incluye
- Frontend estático (`public/`) con UI verde agua.
- Backend en **FastAPI** (`api/index.py`) desplegable en Vercel.
- Endpoint `/api/rate` para obtener cotizaciones y `/api/convert` para convertir.

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
uvicorn api.index:app --reload --port 8000
```

Luego abrí:
- Frontend: http://localhost:8000 (si servís estáticos con otro server) o abrí `public/index.html`
- API: http://localhost:8000/api/rate

> Tip: En local, si querés simular Vercel, podés usar `vercel dev` (opcional).

## Deploy en Vercel
1. Subí este repo a GitHub.
2. En Vercel: **New Project** → Import repo.
3. Framework Preset: **Other** (o detectará Python automáticamente).
4. No necesitás build command.
5. Deploy.

### Rutas
- `/` sirve `public/index.html`
- `/api/*` entra por `api/index.py` (ver `vercel.json`)

## Fuente de datos
- https://dolarapi.com (ver docs en `api/index.py`)

## Licencia
MIT (si querés, cambiála).
