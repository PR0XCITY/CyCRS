import { num } from "@/lib/format";

type Chart = { type: string; title: string; x_label: string; y_label: string; data: unknown[] };
type Rec = Record<string, unknown>;

function isRec(v: unknown): v is Rec {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function Matrix({ chart }: { chart: Chart }) {
  const m = chart.data as number[][];
  return (
    <figure className="panel p-3">
      <figcaption className="text-sm font-medium">{chart.title}</figcaption>
      <table className="data mt-2 max-w-xs">
        <thead>
          <tr>
            <th />
            <th className="n">Pred No</th>
            <th className="n">Pred Yes</th>
          </tr>
        </thead>
        <tbody>
          {m.map((r, i) => (
            <tr key={i}>
              <th>{i === 0 ? "Actual No" : "Actual Yes"}</th>
              {r.map((v, j) => (
                <td key={j} className="n">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

export function Heatmap({ chart }: { chart: Chart }) {
  const rows = chart.data.filter(isRec);
  const xs = [...new Set(rows.map((r) => String(r.x)))];
  const ys = [...new Set(rows.map((r) => String(r.y)))];
  const vals = rows.map((r) => Number(r.value));
  const mx = Math.max(...vals.map(Math.abs), 1e-12);
  const at = new Map(rows.map((r) => [`${String(r.y)}|${String(r.x)}`, Number(r.value)]));
  return (
    <figure className="panel p-3">
      <figcaption className="text-sm font-medium">{chart.title}</figcaption>
      <div className="scroll-x mt-2">
        <table className="data">
          <thead>
            <tr>
              <th>{chart.y_label}</th>
              {xs.map((x) => (
                <th key={x} className="n">
                  {x}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ys.map((y) => (
              <tr key={y}>
                <th>{y}</th>
                {xs.map((x) => {
                  const v = at.get(`${y}|${x}`) ?? 0;
                  const c = v >= 0 ? "var(--risk)" : "var(--safe)";
                  return (
                    <td key={x} className="n" style={{ background: `color-mix(in srgb, ${c} ${Math.round((70 * Math.abs(v)) / mx)}%, transparent)` }}>
                      {num(v, 2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

