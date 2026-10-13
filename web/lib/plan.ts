export type ScoredControl = { effectiveness: number; cost: number; coverage: Record<string, number> };
export type Controls = Record<string, ScoredControl>;
export type Candidate = { control: string; reduction: number; cost: number; ratio: number | null };
export type GreedyStep = { candidates: Candidate[]; pick: string; loss_after: number };

export function combinedFactor(chosen: readonly string[], cat: string, controls: Controls) {
  let f = 1;
  for (const k of chosen) {
    const c = controls[k];
    if (c) f *= 1 - c.effectiveness * (c.coverage[cat] ?? 0);
  }
  return f;
}

export function expectedLoss(base: Record<string, number>, chosen: readonly string[], controls: Controls) {
  let s = 0;
  for (const [c, v] of Object.entries(base)) s += v * combinedFactor(chosen, c, controls);
  return s;
}

function ratioValue(q: Candidate) {
  return q.ratio === null ? Infinity : q.ratio;
}

function firstMax(qs: Candidate[], score: (q: Candidate) => number) {
  let best = qs[0] as Candidate;
  for (const q of qs) if (score(q) > score(best)) best = q;
  return best;
}

function reductionScore(q: Candidate) {
  return q.reduction;
}

export function greedy(base: Record<string, number>, controls: Controls, start: readonly string[], budget: number) {
  const s = [...start];
  let spent = 0;
  const steps: GreedyStep[] = [];
  for (;;) {
    const cur = expectedLoss(base, s, controls);
    const cand: Candidate[] = [];
    for (const [k, c] of Object.entries(controls)) {
      if (s.includes(k) || c.cost > budget - spent) continue;
      const red = cur - expectedLoss(base, [...s, k], controls);
      cand.push({ control: k, reduction: red, cost: c.cost, ratio: c.cost === 0 ? null : red / c.cost });
    }
    const useful = cand.filter((q) => q.reduction > 0);
    if (useful.length === 0) return { plan: s, spent, steps };
    const free = useful.filter((q) => q.cost === 0);
    const pick = free.length > 0 ? firstMax(free, reductionScore) : firstMax(useful, ratioValue);
    s.push(pick.control);
    spent += pick.cost;
    steps.push({ candidates: useful, pick: pick.control, loss_after: expectedLoss(base, s, controls) });
  }
}

export function exhaustive(base: Record<string, number>, controls: Controls, start: readonly string[], budget: number) {
  const free = Object.keys(controls).filter((k) => !start.includes(k));
  let best = expectedLoss(base, start, controls);
  let plan = [...start];
  const n = free.length;
  for (let m = 1; m < 1 << n; m++) {
    const pick = free.filter((_, i) => (m >> i) & 1);
    const cost = pick.reduce((a, k) => a + (controls[k]?.cost ?? 0), 0);
    if (cost > budget) continue;
    const v = expectedLoss(base, [...start, ...pick], controls);
    if (v < best - 1e-9) {
      best = v;
      plan = [...start, ...pick];
    }
  }
  return { plan, loss: best };
}
