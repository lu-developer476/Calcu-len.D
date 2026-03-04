from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


"""
API de cotizaciones
- Dólar ARS/USD (por mercado): https://dolarapi.com/v1/dolares
- FX general (base ARS): https://open.er-api.com/v6/latest/ARS

Docs oficiales:
- https://dolarapi.com/docs/argentina/
- https://www.exchangerate-api.com/docs/free
"""

DOLARAPI_BASE = "https://dolarapi.com/v1"
FX_BASE = "https://open.er-api.com/v6/latest"

app = FastAPI(
    title="ARS Converter",
    version="1.1.0",
)

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

TargetCurrency = Literal["USD", "BRL", "EUR", "CAD", "AUD", "CNY", "PEN", "GBP", "PYG", "MXN", "UAH", "RUB"]


async def _get_json(url: str) -> Any:
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, headers={"User-Agent": "calcu-len/1.1"})
        r.raise_for_status()
        return r.json()


def _pick_rate(compra: float, venta: float, lado: Literal["venta", "compra", "promedio"]) -> float:
    if lado == "compra":
        return compra or venta
    if lado == "promedio":
        return (compra + venta) / 2 if compra and venta else (venta or compra)
    return venta or compra


async def _fetch_quote(casa: Casa) -> dict[str, Any]:
    try:
        data = await _get_json(f"{DOLARAPI_BASE}/dolares/{casa}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Proveedor de cotizaciones no disponible ({exc.response.status_code}).",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo contactar al proveedor de cotizaciones.") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Respuesta inválida del proveedor de cotizaciones.")

    return data


async def _fetch_fx_rates(base: str = "ARS") -> dict[str, Any]:
    try:
        data = await _get_json(f"{FX_BASE}/{base}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Proveedor de FX no disponible ({exc.response.status_code}).",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo contactar al proveedor de FX.") from exc

    rates = data.get("rates") if isinstance(data, dict) else None
    if not isinstance(rates, dict):
        raise HTTPException(status_code=502, detail="Respuesta inválida del proveedor de FX.")

    return data


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rate")
async def rate(
    casa: Optional[Casa] = Query(
        default=None,
        description="Casa/mercado (ej: oficial, blue, bolsa, contadoconliqui, cripto, tarjeta, mayorista). Si se omite, devuelve listado.",
    ),
) -> Any:
    if casa:
        return await _fetch_quote(casa)
    try:
        return await _get_json(f"{DOLARAPI_BASE}/dolares")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Proveedor de cotizaciones no disponible ({exc.response.status_code}).",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo contactar al proveedor de cotizaciones.") from exc


@app.get("/api/convert")
async def convert(
    ars: float = Query(..., gt=0, description="Monto en pesos argentinos (ARS)"),
    casa: Casa = Query("oficial", description="Casa/mercado para la cotización"),
    lado: Literal["venta", "compra", "promedio"] = Query(
        "venta",
        description="Qué valor usar: venta (recomendado), compra o promedio.",
    ),
) -> dict[str, Any]:
    quote = await _fetch_quote(casa)

    compra = float(quote.get("compra") or 0)
    venta = float(quote.get("venta") or 0)
    rate_value = _pick_rate(compra, venta, lado)

    if not rate_value:
        return {
            "ok": False,
            "error": "No se pudo obtener una cotización válida.",
            "casa": casa,
            "raw": quote,
        }

    return {
        "ok": True,
        "ars": ars,
        "usd": ars / rate_value,
        "rate": rate_value,
        "lado": lado,
        "casa": quote.get("casa", casa),
        "nombre": quote.get("nombre"),
        "fechaActualizacion": quote.get("fechaActualizacion"),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/convert-fx")
async def convert_fx(
    ars: float = Query(..., gt=0, description="Monto en pesos argentinos (ARS)"),
    target: TargetCurrency = Query("USD", description="Moneda destino"),
) -> dict[str, Any]:
    if target == "USD":
        quote = await _fetch_quote("oficial")
        compra = float(quote.get("compra") or 0)
        venta = float(quote.get("venta") or 0)
        rate_ars_per_usd = venta or compra
        if not rate_ars_per_usd:
            raise HTTPException(status_code=502, detail="No se pudo obtener cotización USD válida.")
        return {
            "ok": True,
            "ars": ars,
            "target": target,
            "amount": ars / rate_ars_per_usd,
            "rate": 1 / rate_ars_per_usd,
            "rateType": "1 ARS -> USD",
            "provider": "dolarapi",
            "fechaActualizacion": quote.get("fechaActualizacion"),
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    fx = await _fetch_fx_rates("ARS")
    rates = fx["rates"]
    target_rate = float(rates.get(target) or 0)
    if target_rate <= 0:
        raise HTTPException(status_code=502, detail=f"No hay cotización disponible para {target}.")

    return {
        "ok": True,
        "ars": ars,
        "target": target,
        "amount": ars * target_rate,
        "rate": target_rate,
        "rateType": f"1 ARS -> {target}",
        "provider": "open.er-api.com",
        "fechaActualizacion": fx.get("time_last_update_utc"),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
