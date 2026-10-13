const IN = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function trim(n: number, d: number) {
  return n.toFixed(d).replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1");
}

export function inr(v: number) {
  const a = Math.abs(v);
  const s = v < 0 ? "-" : "";
  if (a >= 1e7) return `${s}₹${trim(a / 1e7, a >= 1e9 ? 0 : 1)}Cr`;
  if (a >= 1e5) return `${s}₹${trim(a / 1e5, 1)}L`;
  return `${s}₹${IN.format(a)}`;
}

export function inrFull(v: number) {
  return `₹${IN.format(Math.round(v))}`;
}

export function pct(v: number, d = 1) {
  return `${v.toFixed(d)}%`;
}

export function num(v: number, d = 3) {
  if (!Number.isFinite(v)) return "n/a";
  const a = Math.abs(v);
  if (a !== 0 && (a < 1e-3 || a >= 1e6)) return v.toExponential(2);
  return trim(v, d);
}

export function count(v: number) {
  return IN.format(v);
}

export function label(s: string) {
  return s
    .replace(/^(action|asset|sector|size|actor)_/, "")
    .replace(/_+/g, " ")
    .replace(/\b\w/, (c) => c.toUpperCase());
}
