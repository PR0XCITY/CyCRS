import type { Metadata } from "next";
import FunnelChart from "@/components/FunnelChart";
import { lineage, sources } from "@/lib/data";
import { count, inr, num } from "@/lib/format";

export const metadata: Metadata = { title: "Data and sources", description: "Every dataset and external value behind CyCRS, with links and excerpts." };

function Head({ n, id, title }: { n: string; id: string; title: string }) {
  return (
    <>
      <p className="label">{n}</p>
      <h2 id={id} className="text-2xl mt-1">
        {title}
      </h2>
    </>
  );
}

function show(v: unknown) {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") return num(v, 4);
  if (typeof v === "boolean") return v ? "true" : "false";
  return typeof v === "object" ? JSON.stringify(v) : String(v);
}

function rate(key: string) {
  return sources.values.find((x) => x.key === key)?.value;
}

function inRupees(value: number, unit: string) {
  if (unit.startsWith("INR")) return inr(value);
  const r = unit.startsWith("USD") ? rate("usd_inr") : unit.startsWith("GBP") ? rate("gbp_inr") : undefined;
  return r === undefined ? "" : inr(value * r);
}

function level(s: string) {
  return s ? s.replace(/^\d+_/, "").replace(/_/g, " ") : "direct value";
}

export default function DataPage() {
  const ex = lineage.example_incident;
  return (
    <div className="wrap py-10">
      <p className="label">Data</p>
      <h1 className="text-4xl md:text-5xl mt-2 max-w-3xl">Where every number comes from</h1>
      <p className="mt-3 text-muted max-w-2xl">All inputs are public. Datasets are downloaded by script and fingerprinted; every external value carries the page it was read from.</p>

      <section className="rule mt-8 pt-6" aria-labelledby="d1">
        <Head n="01" id="d1" title="Datasets" />
        <div className="scroll-x mt-4">
          <table className="data">
            <thead>
              <tr>
                <th>Source</th>
                <th>Publisher</th>
                <th>Version</th>
                <th className="n">Files</th>
                <th>Accessed</th>
                <th>SHA-256</th>
              </tr>
            </thead>
            <tbody>
              {lineage.datasets.map((d) => (
                <tr key={d.dataset}>
                  <td>
                    <a href={d.url} rel="noopener noreferrer">
                      {d.dataset}
                    </a>
                  </td>
                  <td>{d.publisher}</td>
                  <td className="num break-all">{d.version}</td>
                  <td className="n">{count(Number(d.files))}</td>
                  <td className="num">{d.access_date}</td>
                  <td className="num break-all text-xs">{d.sha256}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="d2">
        <Head n="02" id="d2" title="Cleaning funnel" />
        <div className="mt-4 panel p-3">
          <FunnelChart steps={lineage.steps} />
          <ul className="mt-2 text-sm text-muted list-disc pl-5">
            {lineage.steps.map((s) => (
              <li key={s.step}>
                {s.step}: {s.rule}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="d3">
        <Head n="03" id="d3" title="One incident, before and after" />
        <p className="mt-2 text-sm text-muted">{ex.source}. Free text and victim names are removed before export.</p>
        <div className="grid12 gap-y-4 mt-4">
          <div className="col-span-12 md:col-span-6 panel p-3 min-w-0">
            <p className="label">Raw VERIS JSON (trimmed)</p>
            <pre className="num text-xs mt-2 overflow-x-auto max-h-[520px]">{JSON.stringify(ex.incident, null, 2)}</pre>
          </div>
          <div className="col-span-12 md:col-span-6 panel p-3 min-w-0">
            <p className="label">Flattened row used by the models</p>
            <div className="scroll-x max-h-[520px] overflow-y-auto">
              <table className="data mt-2">
                <tbody>
                  {Object.entries(ex.flattened).map(([k, v]) => (
                    <tr key={k}>
                      <th scope="row" className="num">
                        {k}
                      </th>
                      <td className={typeof v === "number" ? "n" : undefined}>{show(v)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="d4">
        <Head n="04" id="d4" title="External values" />
        <div className="scroll-x mt-4">
          <table className="data">
            <thead>
              <tr>
                <th>Key</th>
                <th className="n">Value</th>
                <th>Unit</th>
                <th className="n">In rupees</th>
                <th>Publisher</th>
                <th>Excerpt</th>
                <th>Fallback level</th>
              </tr>
            </thead>
            <tbody>
              {sources.values.map((v) => (
                <tr key={v.key}>
                  <td className="num">{v.key}</td>
                  <td className="n">{num(v.value, 4)}</td>
                  <td>{v.unit}</td>
                  <td className="n">{inRupees(v.value, v.unit)}</td>
                  <td>
                    <a href={v.url} rel="noopener noreferrer">
                      {v.publisher}
                    </a>
                  </td>
                  <td className="italic">&ldquo;{v.excerpt}&rdquo;</td>
                  <td>{level(v.fallback_level)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="d5">
        <Head n="05" id="d5" title="Bibliography" />
        <ul className="mt-4 space-y-1 text-sm">
          {sources.bibliography.map((b) => (
            <li key={b.url}>
              {b.publisher ? `${b.publisher}. ` : ""}
              <a href={b.url} rel="noopener noreferrer">
                {b.title}
              </a>{" "}
              ({b.year}). <span className="text-muted">Used for {b.used_for}.</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
