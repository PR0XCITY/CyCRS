import Link from "next/link";
import LazyCardChart from "@/components/LazyCardChart";
import Tex from "@/components/Tex";
import { num } from "@/lib/format";
import type { Card, CardEntry } from "@/lib/schema";

export const SECTIONS = ["The question", "The data going in", "Why this model", "The math", "The result", "What it yields", "Limitations"] as const;

function cell(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") return num(v, 4);
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function isNum(v: unknown) {
  return typeof v === "number";
}

function Sec({ i, children }: { i: number; children: React.ReactNode }) {
  const id = `s${i + 1}`;
  return (
    <section className="rule py-8" aria-labelledby={id} data-section={i + 1}>
      <div className="grid12 gap-y-4">
        <div className="col-span-12 md:col-span-3">
          <p className="label">{String(i + 1).padStart(2, "0")}</p>
          <h2 id={id} className="text-2xl mt-1">
            {SECTIONS[i]}
          </h2>
        </div>
        <div className="col-span-12 md:col-span-9 min-w-0">{children}</div>
      </div>
    </section>
  );
}

function Table({ columns, rows, caption }: { columns: string[]; rows: unknown[][]; caption?: string }) {
  return (
    <div className="scroll-x">
      <table className="data">
        {caption ? <caption className="text-left text-sm font-medium pb-2">{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((v, j) => (
                <td key={j} className={isNum(v) ? "n" : undefined}>
                  {cell(v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type Props = { card: Card; all: CardEntry[] };

export default function ModelPage({ card, all }: Props) {
  const ix = all.findIndex((c) => c.id === card.id);
  const prev = ix > 0 ? all[ix - 1] : undefined;
  const next = ix >= 0 && ix < all.length - 1 ? all[ix + 1] : undefined;
  const titles = new Map(all.map((c) => [c.id, c.title]));
  const sampleCols = [...new Set(card.data_in.sample_rows.flatMap((r) => Object.keys(r)))];
  const kn = Object.entries(card.results.key_numbers);
  return (
    <article className="wrap py-10" data-card={card.id}>
      <p className="label">
        Module {card.module} · stage {card.stage}
        {card.used_live ? " · runs live on your business" : ""}
      </p>
      <h1 className="text-4xl md:text-5xl mt-2 max-w-4xl">{card.title}</h1>

      <Sec i={0}>
        <p className="display text-2xl leading-snug">{card.question}</p>
      </Sec>

      <Sec i={1}>
        <dl className="grid12 gap-y-3 text-sm">
          <div className="col-span-12 md:col-span-8">
            <dt className="label">Dataset</dt>
            <dd className="mt-1">{card.data_in.dataset}</dd>
          </div>
          <div className="col-span-12 md:col-span-4">
            <dt className="label">Rows used</dt>
            <dd className="mt-1 num text-2xl">{num(card.data_in.n_rows, 0)}</dd>
          </div>
        </dl>
        <div className="mt-6">
          <Table caption="Variables" columns={["name", "type", "scale", "transform"]} rows={card.data_in.variables.map((v) => [v.name, v.type, v.scale, v.transform])} />
        </div>
        <h3 className="text-lg mt-6">Preparation steps</h3>
        <ol className="mt-2 list-decimal pl-5 text-sm space-y-1">
          {card.data_in.prep_steps.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
        <div className="mt-6">
          <Table caption="Eight real sample rows (seed 42)" columns={sampleCols} rows={card.data_in.sample_rows.map((r) => sampleCols.map((c) => r[c]))} />
        </div>
      </Sec>

      <Sec i={2}>
        <p className="max-w-3xl leading-relaxed">{card.why}</p>
        <div className="mt-6">
          <Table caption="Measured data properties" columns={["property", "value", "implication"]} rows={card.data_properties.map((d) => [d.name, d.value, d.implication])} />
        </div>
        <h3 className="text-lg mt-6">Alternatives rejected</h3>
        <ul className="mt-2 space-y-2 text-sm">
          {card.alternatives.map((a) => (
            <li key={a.model}>
              <strong>{a.model}</strong>: {a.why_not}
            </li>
          ))}
        </ul>
      </Sec>

      <Sec i={3}>
        <div className="grid grid-cols-1 gap-3">
          {card.formula_tex.map((f) => (
            <div key={f.label} className="panel px-4 py-2">
              <p className="label">{f.label}</p>
              <Tex tex={f.tex} label={f.label} />
            </div>
          ))}
        </div>
        <div className="mt-6">
          <Table
            caption="Assumption checks"
            columns={["check", "statistic", "p", "verdict", "action taken"]}
            rows={card.assumptions.map((a) => [a.check, a.statistic, a.p_value, a.verdict, a.action_taken])}
          />
        </div>
      </Sec>

      <Sec i={4}>
        <div className="grid12 gap-y-4">
          {kn.map(([k, v]) => (
            <div key={k} className="col-span-6 md:col-span-3 border-t border-ink pt-2">
              <p className="label">{k.replace(/_/g, " ")}</p>
              <p className="num text-xl mt-1 break-words">{cell(v)}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          {card.results.charts.map((c, i) => (
            <LazyCardChart key={`${c.title}-${i}`} chart={c} />
          ))}
        </div>
        <div className="mt-6 grid grid-cols-1 gap-6">
          {card.results.tables.map((t) => (
            <Table key={t.title} caption={t.title} columns={t.columns} rows={t.rows} />
          ))}
        </div>
      </Sec>

      <Sec i={5}>
        <p className="display text-xl leading-snug max-w-3xl">{card.yields}</p>
        {card.feeds.length > 0 ? (
          <p className="mt-4 text-sm">
            <span className="label mr-2">Used by</span>
            {card.feeds.map((f, i) => (
              <span key={f}>
                {i > 0 ? ", " : ""}
                {titles.has(f) ? <Link href={`/models/${f}/`}>{titles.get(f)}</Link> : <Link href="/results/">{f.replace(/-/g, " ")}</Link>}
              </span>
            ))}
          </p>
        ) : null}
        {card.used_live ? (
          <p className="mt-4">
            <Link className="btn" href="/assess/">
              See it on your business
            </Link>
          </p>
        ) : null}
      </Sec>

      <Sec i={6}>
        <ul className="list-disc pl-5 space-y-1 text-sm">
          {card.limitations.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Sec>

      <nav aria-label="Model pages" className="rule pt-6 flex flex-wrap justify-between gap-4 text-sm">
        {prev ? <Link href={`/models/${prev.id}/`}>&larr; {prev.title}</Link> : <span />}
        {next ? <Link href={`/models/${next.id}/`}>{next.title} &rarr;</Link> : <span />}
      </nav>
    </article>
  );
}
