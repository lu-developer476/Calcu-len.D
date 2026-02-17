from __future__ import annotations

from typing import Any, Literal, Optional
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


"""
API de cotizaciones
- Listado: https://dolarapi.com/v1/dolares
- Una casa específica: https://dolarapi.com/v1/dolares/{casa}

Docs oficiales: https://dolarapi.com/docs/argentina/
"""

DOLARAPI_BASE = "https://dolarapi.com/v1"


app = FastAPI(
    title="ARS → USD Converter",
    version="1.0.0",
)

# En Vercel y en local, el frontend puede estar en otro origen durante dev.
# Para producción, podrías restringirlo a tu dominio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


Casa = Literal[
    "oficial",
    "blue",
    "bolsa",
    "contadoconliqui",
    "cripto",
    "tarjeta",
    "mayorista",
]


async def _get_json(url: str) -> Any:
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, headers={"User-Agent": "calcu-peso-usd/1.0"})
        r.raise_for_status()
        return r.json()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rate")
async def rate(
    casa: Optional[str] = Query(
        default=None,
        description="Casa/mercado (ej: oficial, blue, bolsa, contadoconliqui, cripto, tarjeta, mayorista). Si se omite, devuelve listado.",
    ),
) -> Any:
    """
    Devuelve:
    - Si casa es None: listado completo de cotizaciones
    - Si casa está: una cotización
    """
    if casa:
        data = await _get_json(f"{DOLARAPI_BASE}/dolares/{casa}")
        return data
    return await _get_json(f"{DOLARAPI_BASE}/dolares")


@app.get("/api/convert")
async def convert(
    ars: float = Query(..., gt=0, description="Monto en pesos argentinos (ARS)"),
    casa: str = Query("oficial", description="Casa/mercado para la cotización"),
    lado: Literal["venta", "compra", "promedio"] = Query(
        "venta",
        description="Qué valor usar: venta (recomendado), compra o promedio.",
    ),
) -> dict[str, Any]:
    """
    Convierte ARS → USD usando la cotización indicada.
    Por defecto usa 'venta' (lo típico cuando comprás USD).
    """
    quote = await _get_json(f"{DOLARAPI_BASE}/dolares/{casa}")

    compra = float(quote.get("compra") or 0)
    venta = float(quote.get("venta") or 0)

    if lado == "compra":
        rate_value = compra
    elif lado == "promedio":
        rate_value = (compra + venta) / 2 if compra and venta else (venta or compra)
    else:
        rate_value = venta or compra

    if not rate_value:
        return {
            "ok": False,
            "error": "No se pudo obtener una cotización válida.",
            "casa": casa,
            "raw": quote,
        }

    usd = ars / rate_value

    return {
        "ok": True,
        "ars": ars,
        "usd": usd,
        "rate": rate_value,
        "lado": lado,
        "casa": quote.get("casa", casa),
        "nombre": quote.get("nombre"),
        "fechaActualizacion": quote.get("fechaActualizacion"),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
