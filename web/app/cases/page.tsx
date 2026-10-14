import type { Metadata } from "next";
import Link from "next/link";
import Panel from "@/components/Panel";
import { caseRuns } from "@/lib/cases";
import { inr, num } from "@/lib/format";
import { categoryLabel, featureLabel } from "@/lib/labels";

export const metadata: Metadata = { title: "Indian cases", description: "Documented Indian cyber incidents replayed through the CyCRS engine." };

const TONE: Record<string, string> = { covered: "var(--safe-ink)", missed: "var(--risk-ink)", "partially covered": "var(--risk-ink)" };

const LEARN = [
  { href: "/models/case-replay/", label: "Case replay" },
  { href: "/models/attack-likelihood/", label: "Attack likelihood" },
  { href: "/models/budget-optimiser/", label: "Budget optimiser" },
];

export default function CasesPage() {
  const runs = caseRuns();
  const budget = runs[0]?.budget ?? 0;
  return (
    <div className="wrap py-10">
      <p className="label">Cases</p>
      <h1 className="text-4xl md:text-5xl mt-2 max-w-3xl">Indian incidents, replayed through CyCRS</h1>
      <p className="mt-3 text-muted max-w-2xl">
        Each case is run through the same engine as your plan, with no controls in place and a budget of <span className="num">{inr(budget)}</span>. Facts are limited to what the
        linked source states.
      </p>
      <ol className="mt-8 grid grid-cols-1 gap-6">
        {runs.map((r, i) => (
          <li key={r.c.name} className="rule pt-6" data-case={r.c.name}>
            <div className="grid12 gap-y-4">
              <p className="col-span-12 md:col-span-1 num text-muted">{String(i + 1).padStart(2, "0")}</p>
              <div className="col-span-12 md:col-span-7 min-w-0">
                <h2 className="text-2xl">
                  {r.c.name} <span className="num text-muted text-lg">{r.c.year}</span>
                </h2>
                <p className="label mt-3">What happened</p>
                <p className="mt-1">{r.c.summary}</p>
                <p className="mt-2 text-sm">
                  <a href={r.c.source_url} rel="noopener noreferrer">
                    Source
                  </a>{" "}
                  <span className="text-muted">(accessed {r.c.accessed})</span>
                </p>
                <p className="label mt-4">CyCRS top 3 at this budget</p>
                <ol className="mt-1 list-decimal pl-5 text-sm">
                  {r.top3.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ol>
              </div>
              <div className="col-span-12 md:col-span-4 text-sm">
                <p className="label">Verdict</p>
                <p className="display text-2xl mt-1" style={{ color: TONE[r.verdict] ?? "var(--muted)" }}>
                  {r.verdict}
                </p>
                <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1">
                  <dt className="label">Sector</dt>
                  <dd>{r.profile.sector}</dd>
                  <dt className="label">Size</dt>
                  <dd>{r.profile.size}</dd>
                  <dt className="label">Assets</dt>
                  <dd>{r.profile.assets.map(featureLabel).join(", ") || "not stated"}</dd>
                  <dt className="label">Attack</dt>
                  <dd>{r.c.actual_categories.map(categoryLabel).join(", ") || "not stated"}</dd>
                </dl>
              </div>
            </div>
            <Panel learn={LEARN} testId={`panel-case-${i}`}>
              <div className="scroll-x">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Attack type</th>
                      <th className="n">z</th>
                      <th className="n">p</th>
                      <th className="n">Records</th>
                      <th className="n">Impact</th>
                      <th className="n">Expected loss</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.rec.categories.map((c) => (
                      <tr key={c.category}>
                        <td>{categoryLabel(c.category)}</td>
                        <td className="n">{num(c.z, 3)}</td>
                        <td className="n">{num(c.p_c, 3)}</td>
                        <td className="n">{num(c.records, 0)}</td>
                        <td className="n">{inr(c.impact_inr)}</td>
                        <td className="n">{inr(c.expected_loss_inr)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {r.rec.greedy_steps.map((s, k) => (
                <div key={`${s.pick}-${k}`} className="mt-3 scroll-x">
                  <p className="font-medium">
                    Step {k + 1}: picked {s.pick}; expected loss now <span className="num">{inr(s.loss_after)}</span>
                  </p>
                  <table className="data mt-1">
                    <thead>
                      <tr>
                        <th>Candidate</th>
                        <th className="n">Loss cut</th>
                        <th className="n">Cost</th>
                        <th className="n">Cut per rupee</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.candidates.map((q) => (
                        <tr key={q.control} className={q.control === s.pick ? "font-semibold" : undefined}>
                          <td>{q.control}</td>
                          <td className="n">{inr(q.reduction)}</td>
                          <td className="n">{q.cost === 0 ? "Free" : inr(q.cost)}</td>
                          <td className="n">{q.ratio === null ? "free, picked first" : num(q.ratio, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </Panel>
          </li>
        ))}
      </ol>
      <p className="mt-8 text-sm">
        <Link href="/models/case-replay/">How the verdicts are decided</Link>
      </p>
    </div>
  );
}
