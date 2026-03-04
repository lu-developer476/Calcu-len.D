const $ = (id) => document.getElementById(id);

const CURRENCY_META = {
  USD: { code: "USD", symbol: "$", label: "Dólar estadounidense" },
  BRL: { code: "BRL", symbol: "R$", label: "Real brasileño" },
  EUR: { code: "EUR", symbol: "€", label: "Euro" },
  CAD: { code: "CAD", symbol: "C$", label: "Dólar canadiense" },
  AUD: { code: "AUD", symbol: "A$", label: "Dólar australiano" },
  CNY: { code: "CNY", symbol: "¥", label: "Yuan chino" },
  PEN: { code: "PEN", symbol: "S/", label: "Sol peruano" },
  GBP: { code: "GBP", symbol: "£", label: "Libra esterlina" },
  PYG: { code: "PYG", symbol: "₲", label: "Guaraní paraguayo" },
  MXN: { code: "MXN", symbol: "MX$", label: "Peso mexicano" },
  UAH: { code: "UAH", symbol: "₴", label: "Grivna ucraniana" },
  RUB: { code: "RUB", symbol: "₽", label: "Rublo ruso" },
};

const fmtMoney = (n, currency = "$") => {
  if (typeof n !== "number" || !Number.isFinite(n)) return `${currency} —`;
  return `${currency} ${n.toLocaleString("es-AR", { maximumFractionDigits: 4 })}`;
};

const setMsg = (text, kind = "muted") => {
  const el = $("msg");
  el.className = "footer " + (kind === "error" ? "error" : "");
  el.textContent = text;
};

const setApiStatus = (text) => {
  $("apiStatus").textContent = text;
};

const isUsdMode = () => $("targetCurrency").value === "USD";

function renderFooter() {
  const footer = $("appFooter");
  if (!footer) return;

  footer.innerHTML = `<span class="text-cyber-gold">©</span> ${new Date().getFullYear()} Todos los derechos reservados • BUILT WITH PYTHON, FASTAPI & JAVASCRIPT • Deployed on Vercel ®`;
}

const setUsdControlsEnabled = (enabled) => {
  ["casa", "lado", "manualRate", "btnSync"].forEach((id) => {
    $(id).disabled = !enabled;
  });

  if (!enabled) {
    $("manualRate").value = "";
  }
};

const refreshModeUI = () => {
  const target = $("targetCurrency").value;
  const usdMode = isUsdMode();
  const meta = CURRENCY_META[target] ?? { code: target, symbol: target };

  setUsdControlsEnabled(usdMode);
  $("resultLabel").textContent = `${meta.code} (${meta.symbol}) estimados`;

  if (usdMode) {
    setMsg("Modo USD local activo: podés usar tipo de dólar, lado y cotización manual.");
  } else {
    setMsg(`Modo ${meta.code}: conversión por API FX global (sin tipo de dólar/manual).`);
  }
};

async function fetchRate(casa) {
  const res = await fetch(`/api/rate?casa=${encodeURIComponent(casa)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error (${res.status})`);
  return await res.json();
}

function pickRate(quote, lado) {
  const compra = Number(quote.compra ?? 0);
  const venta = Number(quote.venta ?? 0);

  if (lado === "compra") return compra || venta || 0;
  if (lado === "promedio") return compra && venta ? (compra + venta) / 2 : venta || compra || 0;
  return venta || compra || 0;
}

async function syncQuote() {
  if (!isUsdMode()) {
    setMsg("La cotización manual/sync aplica solo para USD.");
    return;
  }

  const casa = $("casa").value;
  const lado = $("lado").value;

  setMsg("Buscando cotización USD…");
  try {
    const quote = await fetchRate(casa);
    const rate = pickRate(quote, lado);

    if (!rate) throw new Error("Cotización inválida");

    $("manualRate").value = rate;
    $("rateValue").textContent = fmtMoney(rate, "$ ARS");
    $("rateMeta").textContent = `${quote.nombre ?? casa} · ${quote.fechaActualizacion ?? "sin fecha"}`;
    setApiStatus("OK");
    setMsg("Cotización USD actualizada. Ahora convertí.");
    return rate;
  } catch (e) {
    setApiStatus("ERROR");
    setMsg(`No pude traer la cotización: ${e.message}.`, "error");
    throw e;
  }
}

async function convert() {
  const ars = Number($("ars").value);
  const target = $("targetCurrency").value;
  const targetMeta = CURRENCY_META[target] ?? { code: target, symbol: target };

  if (!ars || ars <= 0) {
    setMsg("Poné un monto ARS válido (mayor a 0).", "error");
    return;
  }

  if (isUsdMode()) {
    const casa = $("casa").value;
    const lado = $("lado").value;
    const manualRate = Number($("manualRate").value);

    if (manualRate && manualRate > 0) {
      const usd = ars / manualRate;
      $("usd").textContent = fmtMoney(usd, CURRENCY_META.USD.symbol);
      $("usdMeta").textContent = `Manual · ${casa} · ${lado}`;
      $("rateValue").textContent = fmtMoney(manualRate, "$ ARS");
      $("rateMeta").textContent = `Manual · ${new Date().toLocaleString("es-AR")}`;
      setMsg("Convertido con cotización manual.");
      return;
    }

    setMsg("Convirtiendo USD con API local…");
    try {
      const res = await fetch(`/api/convert?ars=${encodeURIComponent(ars)}&casa=${encodeURIComponent(casa)}&lado=${encodeURIComponent(lado)}`, { cache: "no-store" });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data?.error ?? `API error (${res.status})`);

      $("usd").textContent = fmtMoney(Number(data.usd), CURRENCY_META.USD.symbol);
      $("usdMeta").textContent = `${data.nombre ?? casa} · ${data.lado} · ${data.fechaActualizacion ?? "sin fecha"}`;
      $("rateValue").textContent = fmtMoney(Number(data.rate), "$ ARS");
      $("rateMeta").textContent = `${data.casa ?? casa} · ${data.fechaActualizacion ?? "sin fecha"}`;
      setApiStatus("OK");
      setMsg("Listo. Convertido con cotización USD en vivo.");
    } catch (e) {
      setApiStatus("ERROR");
      setMsg(`Falló la conversión USD por API: ${e.message}.`, "error");
    }
    return;
  }

  setMsg(`Convirtiendo ARS → ${targetMeta.code} con API FX…`);
  try {
    const res = await fetch(`/api/convert-fx?ars=${encodeURIComponent(ars)}&target=${encodeURIComponent(target)}`, { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data?.detail ?? data?.error ?? `API error (${res.status})`);

    $("usd").textContent = fmtMoney(Number(data.amount), targetMeta.symbol);
    $("usdMeta").textContent = `${data.target} · ${data.provider} · ${data.fechaActualizacion ?? "sin fecha"}`;
    $("rateValue").textContent = `${Number(data.rate).toLocaleString("es-AR", { maximumFractionDigits: 8 })}`;
    $("rateMeta").textContent = data.rateType ?? "1 ARS -> FX";
    setApiStatus("OK");
    setMsg(`Listo. Convertido ARS → ${targetMeta.code}.`);
  } catch (e) {
    setApiStatus("ERROR");
    setMsg(`Falló la conversión FX: ${e.message}.`, "error");
  }
}

function clearAll() {
  $("ars").value = "";
  $("manualRate").value = "";
  $("usd").textContent = "$ —";
  $("usdMeta").textContent = "—";
  $("rateValue").textContent = "$ —";
  $("rateMeta").textContent = "—";
  setMsg("");
  setApiStatus("sin probar");
}

window.addEventListener("DOMContentLoaded", () => {
  $("btnConvert").addEventListener("click", convert);
  $("btnSync").addEventListener("click", syncQuote);
  $("btnClear").addEventListener("click", clearAll);
  $("targetCurrency").addEventListener("change", refreshModeUI);

  $("ars").addEventListener("keydown", (e) => {
    if (e.key === "Enter") convert();
  });

  ["casa", "lado"].forEach((id) => {
    $(id).addEventListener("change", () => {
      if (isUsdMode() && ($("ars").value || $("manualRate").value)) {
        syncQuote().catch(() => {});
      }
    });
  });

  renderFooter();
  refreshModeUI();
});
