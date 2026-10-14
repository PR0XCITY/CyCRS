"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Panel from "@/components/Panel";
import { budgetToSlider, SLIDER_STEPS, sliderToBudget } from "@/lib/budget";
import { model } from "@/lib/modelData";
import { inr, inrFull, num, pct } from "@/lib/format";
import { categoryLabel, featureLabel, tokenLabel } from "@/lib/labels";
import { recommend, type Recommendation } from "@/lib/model";
import { parseProfile, PROFILE_KEY, removeStored, sizeBucket, toEngine, writeStored } from "@/lib/profile";
import type { ProfileForm } from "@/lib/profileSchema";
import { useStoredRaw } from "@/lib/useStored";

function ChartSpace() {
  return <div className="mt-4 h-[280px]" aria-hidden="true" />;
}

const PersonaChart = dynamic(() => import("@/components/ResultCharts").then((m) => m.PersonaChart), { ssr: false, loading: ChartSpace });
const LossChart = dynamic(() => import("@/components/ResultCharts").then((m) => m.LossChart), { ssr: false, loading: ChartSpace });

type TexKey = "logit" | "sigmoid" | "impact" | "loss" | "combine" | "greedy" | "distance";
type Props = { tex: Record<TexKey, React.ReactNode> };

const LEARN = {
  persona: [{ href: "/models/personas-kmeans/", label: "Business personas (K-means)" }],
  risk: [
    { href: "/models/attack-likelihood/", label: "Attack likelihood (logistic regression)" },
    { href: "/models/mlr-impact/", label: "Breach size (multiple regression)" },
    { href: "/models/expected-loss/", label: "Expected loss" },
  ],
  plan: [{ href: "/models/budget-optimiser/", label: "Budget optimiser" }],
  totals: [{ href: "/models/expected-loss/", label: "Expected loss" }, { href: "/models/coverage-hit-rate/", label: "Coverage hit rate" }],
};

const SCALES = [0.8, 1, 1.2];

function Section({ n, title, children, id }: { n: string; title: string; children: React.ReactNode; id: string }) {
  return (
    <section className="rule py-8 print-tight" aria-labelledby={id}>
      <p className="label">{n}</p>
      <h2 id={id} className="text-2xl md:text-3xl mt-1">
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Row({ k, v }: { k: React.ReactNode; v: React.ReactNode }) {
  return (
    <tr>
      <td>{k}</td>
      <td className="n">{v}</td>
    </tr>
  );
}

function controlOf(name: string) {
  return model.controls.find((c) => c.control === name);
}

function coverageText(name: string) {
  const c = controlOf(name);
  if (!c) return "";
  const parts = Object.entries(c.coverage)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([k, v]) => `${pct(100 * v, 0)} of ${categoryLabel(k).toLowerCase()} incidents`);
  return `Stops ${c.mitigates.map(tokenLabel).join(", ")}; addresses ${parts.join(" and ")}`;
}

function pickReduction(rec: Recommendation, name: string) {
  for (const s of rec.greedy_steps) if (s.pick === name) return s.candidates.find((q) => q.control === name);
  return undefined;
}

export default function Results({ tex }: Props) {
  const router = useRouter();
  const raw = useStoredRaw(PROFILE_KEY);
  const profile = useMemo<ProfileForm | null>(() => (raw === undefined ? null : parseProfile(raw)), [raw]);
  const [sens, setSens] = useState(false);

  useEffect(() => {
    if (raw === undefined || profile) return;
    removeStored(PROFILE_KEY);
    router.replace("/assess/");
  }, [raw, profile, router]);

  const budget = profile?.budget ?? 0;
  const rec = useMemo(() => (profile ? recommend(toEngine(profile), model) : null), [profile]);
  const robust = useMemo(() => {
    if (!profile || !sens) return null;
    const plans = SCALES.map((s) => new Set(recommend(toEngine(profile), model, { pScale: s }).plan.map((x) => x.control)));
    return new Set([...(plans[1] ?? [])].filter((k) => plans.every((p) => p.has(k))));
  }, [profile, sens]);

  function changeBudget(b: number) {
    if (profile) writeStored(PROFILE_KEY, { ...profile, budget: b });
  }

  if (!profile || !rec) return <section className="wrap pb-10 min-h-[60vh]" aria-busy="true" />;

  const cpr = rec.inputs.per_record_cost_inr?.value ?? 0;
  const pi = rec.inputs.annual_incident_prob?.value ?? 0;
  const t = rec.totals;
  const cats = [...rec.categories].sort((a, b) => b.expected_loss_inr - a.expected_loss_inr);

  return (
    <div className="wrap pb-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-muted">
            {profile.sector}, {sizeBucket(profile.employees)} business ({profile.employees} staff), {profile.city}. Budget <span className="num">{inr(budget)}</span> a year.
          </p>
        </div>
        <div className="flex gap-2 no-print">
          <button type="button" className="btn btn-ghost" onClick={() => window.print()}>
            Print plan
          </button>
          <Link href="/assess/" className="btn btn-ghost">
            Edit answers
          </Link>
        </div>
      </div>


      <Section n="01" id="sec-persona" title={`You look most like: ${rec.persona.chosen}`}>
        <p className="text-sm text-muted max-w-2xl">Closest group of past incidents by sector, size and the IT you rely on. Shorter bar means more similar.</p>
        <PersonaChart data={rec.persona.distances.map((d, i) => ({ name: d.persona, value: d.distance, chosen: i === rec.persona.index }))} />
        <Panel learn={LEARN.persona} testId="panel-persona">
          {tex.distance}
          <p className="mt-2">Your answers become these model inputs (1 = yes):</p>
          <div className="scroll-x">
            <table className="data mt-2">
              <tbody>
                {rec.features.map((f) => (
                  <Row key={f.name} k={featureLabel(f.name)} v={f.value} />
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3">Squared distance to each persona centre:</p>
          <table className="data mt-2">
            <tbody>
              {rec.persona.distances.map((d, i) => (
                <Row key={d.persona} k={i === rec.persona.index ? <strong>{d.persona} (chosen)</strong> : d.persona} v={num(d.distance, 4)} />
              ))}
            </tbody>
          </table>
        </Panel>
      </Section>

      <Section n="02" id="sec-risk" title="Expected yearly loss by attack type">
        <p className="text-sm text-muted max-w-2xl">
          Chance of an incident this year, times the chance it is this kind of attack, times what it would cost. Total{" "}
          <span className="num text-ink">{inr(t.loss_no_controls_inr)}</span> a year before any controls.
        </p>
        <LossChart data={cats.map((c) => ({ name: categoryLabel(c.category), value: c.expected_loss_inr }))} />
        <Panel learn={LEARN.risk} testId="panel-risk">
          <div className="grid gap-1">
            {tex.logit}
            {tex.sigmoid}
            {tex.impact}
            {tex.loss}
          </div>
          {cats.map((c) => {
            const shown = c.top_contributions.reduce((s, q) => s + q.contribution, 0);
            const rest = c.z - c.intercept - shown;
            return (
              <div key={c.category} className="mt-4 pt-3 border-t border-rule">
                <p className="font-medium">{categoryLabel(c.category)}</p>
                <p className="num mt-1 break-words">
                  z = {num(c.intercept, 4)}
                  {c.top_contributions.map((q) => ` ${q.contribution < 0 ? "-" : "+"} ${num(Math.abs(q.contribution), 4)} (${featureLabel(q.feature)})`).join("")}
                  {Math.abs(rest) > 1e-12 ? ` ${rest < 0 ? "-" : "+"} ${num(Math.abs(rest), 4)} (other terms)` : ""} = {num(c.z, 4)}
                </p>
                <p className="num">
                  p = 1 / (1 + e^-({num(c.z, 4)})) = {num(c.p_c, 4)}
                </p>
                <p className="num">
                  records = 10^{num(c.log_records, 4)} - 1 = {num(c.records, 0)};{" "}
                  {c.impact_cap_inr === null
                    ? `I = records x ${inrFull(cpr)} = ${inr(c.impact_inr)}`
                    : `I = min(records x ${inrFull(cpr)}, cap ${inr(c.impact_cap_inr)}) = min(${inr(c.impact_uncapped_inr)}, ${inr(c.impact_cap_inr)}) = ${inr(c.impact_inr)}${c.capped ? " (capped)" : ""}`}
                </p>
                <p className="num">
                  L = {num(pi, 3)} x {num(c.p_c, 4)} x {inr(c.impact_inr)} = {inr(c.expected_loss_inr)}
                </p>
              </div>
            );
          })}
        </Panel>
      </Section>

      <Section n="03" id="sec-plan" title="What to do first">
        <div className="no-print panel px-4 py-4 grid12 gap-y-4 items-end">
          <div className="col-span-12 md:col-span-8">
            <label htmlFor="live-budget" className="text-sm font-medium">
              Yearly budget: <span className="num">{inr(budget)}</span>
            </label>
            <input
              id="live-budget"
              type="range"
              className="w-full mt-2 accent-[var(--ink)]"
              min={0}
              max={SLIDER_STEPS}
              value={budgetToSlider(budget)}
              aria-valuetext={inr(budget)}
              onChange={(e) => changeBudget(sliderToBudget(Number(e.target.value)))}
            />
          </div>
          <label className="col-span-12 md:col-span-4 flex items-center gap-2 text-sm">
            <input type="checkbox" className="size-4 accent-[var(--ink)]" checked={sens} onChange={(e) => setSens(e.target.checked)} />
            Test probabilities 20% lower and higher
          </label>
        </div>
        <ol className="mt-4 grid gap-3">
          {rec.plan.map((p, i) => {
            const r = pickReduction(rec, p.control);
            const isRobust = robust ? robust.has(p.control) : null;
            return (
              <li key={p.control} className="panel px-4 py-3 grid12 gap-y-2 items-start">
                <span className="col-span-2 md:col-span-1 num text-muted">{String(i + 1).padStart(2, "0")}</span>
                <div className="col-span-10 md:col-span-7">
                  <p className="font-medium">
                    {p.control}
                    {p.already_in_place ? <span className="label ml-2">already in place</span> : null}
                    {isRobust === true ? <span className="label ml-2 text-safe-ink">robust to +/-20%</span> : null}
                    {isRobust === false ? <span className="label ml-2 text-risk-ink">changes with +/-20%</span> : null}
                  </p>
                  <p className="text-sm text-muted mt-0.5">{coverageText(p.control)}.</p>
                  <p className="text-sm mt-0.5">
                    {p.already_in_place
                      ? "You already do this, so it counts from the start."
                      : r && r.ratio === null
                        ? `Free to adopt and removes ${inr(r.reduction)} of expected loss a year.`
                        : r
                          ? `Removes ${num(r.ratio ?? 0, 1)} rupees of expected loss for every rupee spent.`
                          : ""}
                  </p>
                </div>
                <div className="col-span-12 md:col-span-4 md:text-right text-sm">
                  <p>
                    Cost <span className="num">{p.cost === 0 ? "Free" : inr(p.cost)}</span>
                  </p>
                  {r ? (
                    <p className="text-safe-ink">
                      Loss cut <span className="num">{inr(r.reduction)}</span>
                    </p>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
        {rec.plan.length === 0 ? <p className="text-sm text-muted">No scored control is affordable or useful at this budget.</p> : null}
        <div className="mt-5" data-testid="not-scored">
          <p className="label">Not ranked yet</p>
          <ul className="mt-2 grid gap-2 text-sm">
            {rec.not_scored.map((s) => {
              const c = controlOf(s.control);
              const free = c?.annual_cost_inr === 0;
              return (
                <li key={s.control} className="border-l-2 border-rule pl-3">
                  <span className="font-medium">{s.control}</span>
                  {free ? <span className="label ml-2 text-safe-ink">free</span> : null}
                  <span className="text-muted"> · {c?.effectiveness_note ? c.effectiveness_note.charAt(0).toUpperCase() + c.effectiveness_note.slice(1) : s.reason}</span>
                </li>
              );
            })}
          </ul>
        </div>
        <Panel learn={LEARN.plan} testId="panel-plan">
          {tex.combine}
          {tex.greedy}
          {rec.greedy_steps.map((s, i) => (
            <div key={`${s.pick}-${i}`} className="mt-3 scroll-x">
              <p className="font-medium">
                Step {i + 1}: picked {s.pick}; expected loss now <span className="num">{inr(s.loss_after)}</span>
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
          {rec.greedy_steps.length === 0 ? <p className="mt-2">No affordable control reduces expected loss further.</p> : null}
        </Panel>
      </Section>

      <Section n="04" id="sec-totals" title="Before and after">
        <div className="grid12 gap-y-6">
          <div className="col-span-12 sm:col-span-4 border-t border-ink pt-3">
            <p className="label">No controls</p>
            <p className="num text-3xl text-risk-ink">{inr(t.loss_no_controls_inr)}</p>
          </div>
          <div className="col-span-12 sm:col-span-4 border-t border-ink pt-3">
            <p className="label">After this plan</p>
            <p className="num text-3xl text-safe-ink">{inr(t.loss_after_plan_inr)}</p>
          </div>
          <div className="col-span-12 sm:col-span-4 border-t border-ink pt-3">
            <p className="label">Residual risk</p>
            <p className="num text-3xl">{pct(t.residual_risk_pct)}</p>
          </div>
        </div>
        <Panel learn={LEARN.totals} testId="panel-totals">
          <table className="data">
            <tbody>
              <Row k="Expected loss with no controls" v={inrFull(t.loss_no_controls_inr)} />
              <Row k="With the controls you already have" v={inrFull(t.loss_with_current_controls_inr)} />
              <Row k="After the plan" v={inrFull(t.loss_after_plan_inr)} />
              <Row k="Spent on new controls" v={inrFull(t.spent_inr)} />
              <Row k="Residual risk = after / no controls" v={pct(t.residual_risk_pct, 2)} />
            </tbody>
          </table>
        </Panel>
      </Section>
    </div>
  );
}
