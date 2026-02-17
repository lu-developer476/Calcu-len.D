const $ = (id) => document.getElementById(id);

const fmtMoney = (n, currency = "$") => {
  if (typeof n !== "number" || !Number.isFinite(n)) return `${currency} —`;
  // formato simple (es-AR) sin depender de Intl currency (para evitar sorpresas)
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

async function fetchRate(casa) {
  const res = await fetch(`/api/rate?casa=${encodeURIComponent(casa)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error (${res.status})`);
  return await res.json();
}

function pickRate(quote, lado) {
  const compra = Number(quote.compra ?? 0);
  const venta = Number(quote.venta ?? 0);

  if (lado === "compra") return compra || venta || 0;
  if (lado === "promedio") {
    if (compra && venta) return (compra + venta) / 2;
    return venta || compra || 0;
  }
  return venta || compra || 0; // venta por defecto
}

async function syncQuote() {
  const casa = $("casa").value;
  const lado = $("lado").value;

  setMsg("Buscando cotización…");
  try {
    const quote = await fetchRate(casa);
    const rate = pickRate(quote, lado);

    if (!rate) throw new Error("Cotización inválida");

    $("manualRate").value = rate;
    $("rateValue").textContent = fmtMoney(rate);
    $("rateMeta").textContent = `${quote.nombre ?? casa} · ${quote.fechaActualizacion ?? "sin fecha"}`;
    setApiStatus("OK");
    setMsg("Cotización actualizada. Ahora convertí.");
    return rate;
  } catch (e) {
    setApiStatus("ERROR");
    setMsg(`No pude traer la cotización: ${e.message}. Usá cotización manual y seguí.`, "error");
    throw e;
  }
}

function computeUsd(ars, rate) {
  return ars / rate;
}

async function convert() {
  const ars = Number($("ars").value);
  const casa = $("casa").value;
  const lado = $("lado").value;
  const manualRate = Number($("manualRate").value);

  if (!ars || ars <= 0) {
    setMsg("Poné un monto ARS válido (mayor a 0).", "error");
    return;
  }

  // Si hay cotización manual, la usamos (modo offline / fallback)
  if (manualRate && manualRate > 0) {
    const usd = computeUsd(ars, manualRate);
    $("usd").textContent = fmtMoney(usd, "USD");
    $("usdMeta").textContent = `Manual · ${casa} · ${lado}`;
    $("rateValue").textContent = fmtMoney(manualRate);
    $("rateMeta").textContent = `Manual · ${new Date().toLocaleString("es-AR")}`;
    setMsg("Convertido con cotización manual.");
    return;
  }

  // Si no hay manual, intentamos API (convert endpoint) para consistencia
  setMsg("Convirtiendo con API…");
  try {
    const res = await fetch(`/api/convert?ars=${encodeURIComponent(ars)}&casa=${encodeURIComponent(casa)}&lado=${encodeURIComponent(lado)}`, { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data?.error ?? `API error (${res.status})`);

    $("usd").textContent = fmtMoney(Number(data.usd), "USD");
    $("usdMeta").textContent = `${data.nombre ?? casa} · ${data.lado} · ${data.fechaActualizacion ?? "sin fecha"}`;

    $("rateValue").textContent = fmtMoney(Number(data.rate));
    $("rateMeta").textContent = `${data.casa ?? casa} · ${data.fechaActualizacion ?? "sin fecha"}`;

    setApiStatus("OK");
    setMsg("Listo. Convertido con cotización en vivo.");
  } catch (e) {
    setApiStatus("ERROR");
    setMsg(`Falló la conversión por API: ${e.message}. Tip: tocá “Traer cotización” o cargala manual.`, "error");
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

  $("ars").addEventListener("keydown", (e) => {
    if (e.key === "Enter") convert();
  });

  // mini auto-sync al cambiar casa/lado si ya hay algo escrito
  ["casa", "lado"].forEach((id) => {
    $(id).addEventListener("change", () => {
      if ($("ars").value || $("manualRate").value) {
        // no forzamos; solo si el usuario ya estaba usando la app
        syncQuote().catch(() => {});
      }
    });
  });
});
