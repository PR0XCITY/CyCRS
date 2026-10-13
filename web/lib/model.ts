import type { Model } from "@/lib/schema";
import { type Controls, expectedLoss, greedy } from "@/lib/plan";

export const CATEGORIES = ["hacking", "malware", "social", "error", "misuse", "physical"] as const;

export type EngineProfile = {
  sector: string;
  size: string;
  assets: string[];
  controls: string[];
  budget_inr: number;
  name?: string;
};

export type Contribution = { feature: string; contribution: number };
export type CategoryTrace = {
  category: string;
  intercept: number;
  top_contributions: Contribution[];
  z: number;
  p_c: number;
  log_records: number;
  records: number;
  impact_inr: number;
  expected_loss_inr: number;
};

export function slug(s: string) {
  return s
    .toLowerCase()
    .split("")
    .map((c) => (/[\p{L}\p{N}]/u.test(c) ? c : "_"))
    .join("")
    .replace(/^_+|_+$/g, "");
}

export function encodeProfile(p: EngineProfile, order: readonly string[], sectors: readonly string[]) {
  const a = new Set(p.assets);
  const x: Record<string, number> = {};
  for (const f of order) {
    if (f.startsWith("sector_")) x[f] = sectors.includes(p.sector) && f === `sector_${slug(p.sector)}` ? 1 : 0;
    else if (f.startsWith("size_")) x[f] = f === `size_${p.size}` ? 1 : 0;
    else if (f.startsWith("asset_")) x[f] = a.has(f) ? 1 : 0;
    else x[f] = 0;
  }
  return x;
}

function byAbsDesc(a: Contribution, b: Contribution) {
  return Math.abs(b.contribution) - Math.abs(a.contribution);
}

export function logitTrace(m: { intercept: number; coefficients: Record<string, number> }, x: Record<string, number>, n = 5) {
  const cs: Contribution[] = Object.entries(m.coefficients).map(([f, b]) => ({ feature: f, contribution: b * (x[f] ?? 0) }));
  const z = m.intercept + cs.reduce((s, c) => s + c.contribution, 0);
  const top = cs.filter((c) => c.contribution !== 0).sort(byAbsDesc).slice(0, n);
  return { z, p: 1 / (1 + Math.exp(-z)), top };
}

export function impactRecords(imp: Model["impact"], x: Record<string, number>, cat: string) {
  let y = imp.intercept;
  for (const [f, b] of Object.entries(imp.coefficients)) {
    if (f.startsWith("action_")) y += b * (f === `action_${cat}` ? 1 : 0);
    else y += b * (x[f] ?? 0);
  }
  return { y, records: Math.max(10 ** y - 1, 0) };
}

export function personaTrace(per: Model["personas"], x: Record<string, number>) {
  const v = per.feature_order.map((f) => x[f] ?? 0);
  const d = per.centroids.map((c) => c.reduce((s, ci, i) => s + (ci - (v[i] ?? 0)) ** 2, 0));
  let i = 0;
  for (let j = 1; j < d.length; j++) if ((d[j] as number) < (d[i] as number)) i = j;
  return {
    distances: d.map((dist, j) => ({ persona: per.names[j] as string, distance: dist })),
    chosen: per.names[i] as string,
    index: i,
  };
}

export function scorable(model: Model) {
  const out: Controls = {};
  const skipped: { control: string; reason: string }[] = [];
  for (const c of model.controls) {
    if (c.effectiveness === null || c.annual_cost_inr === null) {
      const miss: string[] = [];
      if (c.effectiveness === null) miss.push("effectiveness");
      if (c.annual_cost_inr === null) miss.push("cost");
      skipped.push({ control: c.control, reason: `${miss.join(" and ")} MISSING` });
      continue;
    }
    out[c.control] = { effectiveness: c.effectiveness, cost: c.annual_cost_inr, coverage: c.coverage };
  }
  return { controls: out, skipped };
}

export type Options = { pScale?: number };

function cfgValue(model: Model, k: string) {
  const e = model.config[k];
  if (!e) throw new Error(`config ${k} missing`);
  return e.value;
}

export function recommend(profile: EngineProfile, model: Model, opt: Options = {}) {
  const att = model.attack;
  const x = encodeProfile(profile, att.feature_order, att.sectors);
  const pi = cfgValue(model, "annual_incident_prob");
  const cpr = cfgValue(model, "per_record_cost_inr");
  const scale = opt.pScale ?? 1;
  const cats: CategoryTrace[] = [];
  const base: Record<string, number> = {};
  for (const c of CATEGORIES) {
    const m = att.models[c];
    if (!m) throw new Error(`attack model ${c} missing`);
    const t = logitTrace(m, x);
    const p = Math.min(t.p * scale, 1);
    const r = impactRecords(model.impact, x, c);
    const ic = r.records * cpr;
    const lc = pi * p * ic;
    base[c] = lc;
    cats.push({
      category: c,
      intercept: m.intercept,
      top_contributions: t.top,
      z: t.z,
      p_c: p,
      log_records: r.y,
      records: r.records,
      impact_inr: ic,
      expected_loss_inr: lc,
    });
  }
  const { controls: ctl, skipped } = scorable(model);
  const start = profile.controls.filter((k) => k in ctl);
  const budget = Number(profile.budget_inr);
  const g = greedy(base, ctl, start, budget);
  const l0 = expectedLoss(base, [], ctl);
  const l1 = expectedLoss(base, g.plan, ctl);
  const lin = expectedLoss(base, start, ctl);
  const inputs: Record<string, { value: number; fallback_level: string }> = {};
  for (const [k, v] of Object.entries(model.config)) inputs[k] = { value: v.value, fallback_level: v.fallback_level };
  return {
    estimate: true,
    profile,
    features: att.feature_order.map((f) => ({ name: f, value: x[f] ?? 0 })),
    categories: cats,
    persona: personaTrace(model.personas, x),
    plan: g.plan.map((k) => ({ control: k, cost: ctl[k]?.cost ?? 0, already_in_place: start.includes(k) })),
    not_scored: skipped,
    greedy_steps: g.steps,
    totals: {
      loss_no_controls_inr: l0,
      loss_with_current_controls_inr: lin,
      loss_after_plan_inr: l1,
      spent_inr: g.spent,
      budget_inr: budget,
      residual_risk_pct: l0 ? (100 * l1) / l0 : 0,
    },
    inputs,
    base,
  };
}

export type Recommendation = ReturnType<typeof recommend>;
