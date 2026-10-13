"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { num } from "@/lib/format";

type Chart = { type: string; title: string; x_label: string; y_label: string; data: unknown[] };
type Rec = Record<string, unknown>;

const TICK = { fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-plex-mono)" };
const SERIES = ["var(--ink)", "var(--risk)", "var(--safe)", "#8c8780", "#c9a227", "#6b8f71", "#a05a4c", "#4f6d7a"];

export function isRec(v: unknown): v is Rec {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function numericKeys(rows: Rec[], skip: string[]) {
  const first = rows[0] ?? {};
  return Object.keys(first).filter((k) => !skip.includes(k) && typeof first[k] === "number");
}

function tick(v: unknown) {
  return typeof v === "number" ? num(v, 3) : String(v).length > 18 ? `${String(v).slice(0, 16)}…` : String(v);
}

function tip(v: unknown) {
  return typeof v === "number" ? num(v, 4) : String(v);
}

export default function CardChart({ chart }: { chart: Chart }) {
  const rows = chart.data.filter(isRec);
  if (rows.length === 0) return null;
  const grid = <CartesianGrid stroke="var(--grid)" vertical={false} />;
  const tooltip = <Tooltip formatter={tip} contentStyle={{ background: "var(--surface)", border: "1px solid var(--rule)", fontSize: 12 }} />;

  if (chart.type === "histogram") {
    const d = rows.map((r) => ({ x: `${num(Number(r.x0), 2)}`, y: Number(r.y) }));
    return (
      <>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={d} barCategoryGap={1}>
            {grid}
            <XAxis dataKey="x" tick={TICK} stroke="var(--rule)" />
            <YAxis tick={TICK} stroke="var(--rule)" />
            {tooltip}
            <Bar dataKey="y" fill="var(--ink)" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </>
    );
  }

  if (chart.type === "scatter") {
    return (
      <>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid stroke="var(--grid)" />
            <XAxis type="number" dataKey="x" tick={TICK} stroke="var(--rule)" tickFormatter={tick} />
            <YAxis type="number" dataKey="y" tick={TICK} stroke="var(--rule)" tickFormatter={tick} />
            {tooltip}
            <Scatter data={rows} fill="var(--ink)" fillOpacity={0.35} isAnimationActive={false} />
          </ScatterChart>
        </ResponsiveContainer>
      </>
    );
  }

  if (chart.type === "pie") {
    return (
      <>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={rows} dataKey="y" nameKey="x" outerRadius="75%" isAnimationActive={false} label={tick}>
              {rows.map((r, i) => (
                <Cell key={String(r.x)} fill={SERIES[i % SERIES.length]} />
              ))}
            </Pie>
            {tooltip}
          </PieChart>
        </ResponsiveContainer>
      </>
    );
  }

  if (chart.type === "line") {
    const roc = "fpr" in (rows[0] ?? {});
    const xk = roc ? "fpr" : "x";
    const ys = roc ? ["tpr"] : numericKeys(rows, [xk]);
    return (
      <>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            {grid}
            <XAxis dataKey={xk} type={roc || typeof rows[0]?.[xk] === "number" ? "number" : "category"} domain={roc ? [0, 1] : ["auto", "auto"]} tick={TICK} stroke="var(--rule)" tickFormatter={tick} />
            <YAxis tick={TICK} stroke="var(--rule)" tickFormatter={tick} domain={roc ? [0, 1] : ["auto", "auto"]} />
            {tooltip}
            {ys.length > 1 ? <Legend wrapperStyle={{ fontSize: 11 }} /> : null}
            {ys.map((k, i) => (
              <Line key={k} dataKey={k} stroke={SERIES[i % SERIES.length]} strokeWidth={1.5} dot={false} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </>
    );
  }

  const ys = "y" in (rows[0] ?? {}) ? ["y"] : numericKeys(rows, ["x"]);
  return (
    <>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows}>
          {grid}
          <XAxis dataKey="x" tick={TICK} stroke="var(--rule)" tickFormatter={tick} interval={0} angle={rows.length > 6 ? -30 : 0} textAnchor={rows.length > 6 ? "end" : "middle"} height={rows.length > 6 ? 70 : 30} />
          <YAxis tick={TICK} stroke="var(--rule)" tickFormatter={tick} />
          {tooltip}
          {ys.length > 1 ? <Legend wrapperStyle={{ fontSize: 11 }} /> : null}
          {ys.map((k, i) => (
            <Bar key={k} dataKey={k} fill={SERIES[i % SERIES.length]} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </>
  );
}
