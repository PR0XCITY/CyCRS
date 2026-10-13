import Link from "next/link";
import { cards, keyNumber, model } from "@/lib/data";
import { count, num } from "@/lib/format";

function Headline({ value, text, href }: { value: string; text: string; href: string }) {
  return (
    <div className="col-span-12 sm:col-span-4 border-t border-ink pt-4">
      <p className="num text-4xl md:text-5xl">{value}</p>
      <p className="mt-2 text-sm text-muted max-w-xs">{text}</p>
      <Link href={href} className="mt-2 inline-block text-xs label">
        Source model
      </Link>
    </div>
  );
}

const STRIP = [
  { n: "01", t: "Profile", d: "Sector, size, the IT you rely on, what you already do and your yearly budget." },
  { n: "02", t: "Risk", d: "Chance of each attack type and what it could cost, in rupees, with every step shown." },
  { n: "03", t: "Plan", d: "Controls to buy first for your budget, ranked by loss removed per rupee." },
];

export default function Home() {
  const incidents = keyNumber("data-preparation", "flattened_rows");
  const days = keyNumber("descriptive", "median_discovery_days");
  const scored = model.controls.filter((c) => c.effectiveness !== null && c.annual_cost_inr !== null).length;
  return (
    <>
      <section className="wrap pt-14 pb-12">
        <p className="label">Cyber Security Control Recommendation System</p>
        <h1 className="mt-4 text-4xl md:text-6xl max-w-4xl leading-[1.05]">
          Which cyber attacks your business is most exposed to, what to fix first for your budget, and the statistics behind every number.
        </h1>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link className="btn" href="/assess/">
            Assess my business
          </Link>
          <Link className="btn btn-ghost" href="/models/">
            How it works
          </Link>
        </div>
      </section>
      <section className="wrap rule py-10" aria-label="Headline numbers">
        <div className="grid12 gap-y-8">
          <Headline value={incidents !== undefined ? count(incidents) : "n/a"} text="public breach reports analysed from the VERIS Community Database" href="/models/data-preparation/" />
          <Headline value={days !== undefined ? num(days, 0) : "n/a"} text="days a typical breach goes unnoticed (median)" href="/models/descriptive/" />
          <Headline value={String(cards.length)} text={`statistical models behind the advice, ${scored} controls scored from published sources`} href="/models/" />
        </div>
      </section>
      <section className="wrap rule py-10" aria-labelledby="how">
        <h2 id="how" className="label">How CyCRS works</h2>
        <ol className="grid12 gap-y-6 mt-6">
          {STRIP.map((s, i) => (
            <li key={s.n} className="col-span-12 md:col-span-4 flex gap-4">
              <span className="num text-muted">{s.n}</span>
              <div>
                <p className="display text-2xl">
                  {s.t}
                  {i < STRIP.length - 1 ? <span className="text-faint" aria-hidden="true"> &rsaquo;</span> : null}
                </p>
                <p className="mt-1 text-sm text-muted">{s.d}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
