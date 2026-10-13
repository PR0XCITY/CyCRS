import type { CardEntry } from "@/lib/schema";

type Node = { id: string; label: string; href: string; x: number; y: number; live: boolean; w: number };

const W = 168;
const H = 34;
const GAP = 8;
const HEAD = 22;
const MID_GROUPS = [
  ["explore", "Explore"],
  ["impact", "Impact"],
  ["likelihood", "Likelihood"],
  ["segment", "Segment"],
] as const;

function short(s: string) {
  return s.length > 26 ? `${s.slice(0, 24)}…` : s;
}

function edge(a: Node, b: Node, key: string, dashed = false) {
  const x1 = a.x + a.w;
  const y1 = a.y + H / 2;
  const x2 = b.x;
  const y2 = b.y + H / 2;
  const mx = (x1 + x2) / 2;
  return <path key={key} d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`} fill="none" stroke="var(--rule)" strokeWidth={1} strokeDasharray={dashed ? "4 3" : undefined} />;
}

export default function Pipeline({ cards }: { cards: CardEntry[] }) {
  function by(s: string) {
    return cards.filter((c) => c.stage === s);
  }
  function mk(c: CardEntry, x: number, y: number): Node {
    return { id: c.id, label: c.title, href: `/models/${c.id}/`, x, y, live: c.used_live, w: W };
  }
  const srcs: Node[] = ["VCDB incidents", "NCRB Crime in India", "Web sources"].map((l, i) => ({ id: `src-${i}`, label: l, href: "/data/", x: 0, y: 40 + i * (H + GAP), live: false, w: 140 }));
  const prep = by("prepare").map((c, i) => mk(c, 190, 40 + i * (H + GAP)));
  const mid: Node[] = [];
  const heads: { label: string; y: number }[] = [];
  let y = 18;
  for (const [s, lab] of MID_GROUPS) {
    heads.push({ label: lab, y });
    y += HEAD;
    for (const c of by(s)) {
      mid.push(mk(c, 400, y));
      y += H + GAP;
    }
    y += 6;
  }
  const height = Math.max(y, 260);
  const cy = height / 2 - H / 2;
  const loss = by("decide").filter((c) => c.id === "expected-loss").map((c) => mk(c, 620, cy - 40));
  const opt = by("decide").filter((c) => c.id !== "expected-loss").map((c) => mk(c, 820, cy - 40));
  const evalN = by("evaluate").map((c, i) => mk(c, 820, cy + 30 + i * (H + GAP)));
  const plan: Node = { id: "plan", label: "Your plan", href: "/results/", x: 1010, y: cy - 40, live: true, w: 110 };
  const nodes = [...srcs, ...prep, ...mid, ...loss, ...opt, ...evalN, plan];
  const edges: React.ReactNode[] = [];
  for (const s of srcs) for (const p of prep) edges.push(edge(s, p, `${s.id}-${p.id}`));
  for (const p of prep) for (const m of mid) edges.push(edge(p, m, `${p.id}-${m.id}`));
  for (const m of mid.filter((n) => n.live)) for (const l of loss.length ? loss : [plan]) edges.push(edge(m, m.id.startsWith("personas") ? plan : l, `${m.id}-x`));
  for (const l of loss) for (const o of opt) edges.push(edge(l, o, `${l.id}-${o.id}`));
  for (const o of opt) edges.push(edge(o, plan, `${o.id}-plan`));
  for (const o of opt) for (const e of evalN) edges.push(edge(o, e, `${o.id}-${e.id}`, true));
  return (
    <div className="scroll-x panel p-3">
      <svg viewBox={`-4 0 1130 ${height}`} className="min-w-[900px] w-full h-auto" role="img" aria-labelledby="pipe-title">
        <title id="pipe-title">CyCRS pipeline from data sources through models to your plan; live models marked with a dot</title>
        {edges}
        {heads.map((h) => (
          <text key={h.label} x={400} y={h.y + 14} className="label" fill="var(--muted)" fontSize={10} letterSpacing="0.08em">
            {h.label.toUpperCase()}
          </text>
        ))}
        {nodes.map((n) => (
          <a key={n.id} href={n.href} aria-label={`${n.label}${n.live ? " (live)" : ""}`}>
            <rect x={n.x} y={n.y} width={n.w} height={H} rx={5} fill="var(--surface)" stroke={n.live ? "var(--risk)" : "var(--rule)"} />
            {n.live ? <circle cx={n.x + 10} cy={n.y + H / 2} r={3.5} fill="var(--risk)" /> : null}
            <text x={n.x + (n.live ? 20 : 10)} y={n.y + H / 2 + 4} fontSize={11} fill="var(--ink)">
              {short(n.label)}
            </text>
          </a>
        ))}
      </svg>
      <p className="mt-2 text-xs text-muted">
        <span className="inline-block size-2 rounded-full align-middle mr-1" style={{ background: "var(--risk)" }} />
        runs live on your answers · dashed line: offline evaluation
      </p>
    </div>
  );
}
