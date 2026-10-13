import { describe, expect, it } from "vitest";
import ref from "@/tests/fixtures/reference.json";
import { model } from "@/lib/data";
import { type EngineProfile, recommend, scorable } from "@/lib/model";
import { combinedFactor, type Controls, exhaustive, expectedLoss, greedy } from "@/lib/plan";

const CTL: Controls = {
  free_a: { effectiveness: 0.5, cost: 0, coverage: { a: 1 } },
  cheap_b: { effectiveness: 0.5, cost: 100, coverage: { b: 1 } },
  dear_ab: { effectiveness: 0.9, cost: 1000, coverage: { a: 0.5, b: 0.5 } },
};
const BASE = { a: 100, b: 50 };

describe("plan.ts optimiser", () => {
  it("combines controls independently", () => {
    expect(combinedFactor(["free_a"], "a", CTL)).toBeCloseTo(0.5);
    expect(combinedFactor(["free_a", "dear_ab"], "a", CTL)).toBeCloseTo(0.5 * 0.55);
    expect(expectedLoss(BASE, [], CTL)).toBeCloseTo(150);
  });

  it("budget 0 takes only free controls", () => {
    const g = greedy(BASE, CTL, [], 0);
    expect(g.plan).toEqual(["free_a"]);
    expect(g.spent).toBe(0);
  });

  it("budget below the cheapest paid control takes only free controls", () => {
    expect(greedy(BASE, CTL, [], 99).plan).toEqual(["free_a"]);
  });

  it("budget above all costs takes every useful control, free first", () => {
    const g = greedy(BASE, CTL, [], 1e9);
    expect(g.plan[0]).toBe("free_a");
    expect(new Set(g.plan)).toEqual(new Set(Object.keys(CTL)));
    expect(g.spent).toBe(1100);
  });

  it("keeps controls already in place and never spends on them", () => {
    const g = greedy(BASE, CTL, ["cheap_b"], 0);
    expect(g.plan[0]).toBe("cheap_b");
    expect(g.spent).toBe(0);
  });

  it("free candidates have null ratio", () => {
    const g = greedy(BASE, CTL, [], 1e9);
    const c = g.steps[0]?.candidates.find((q) => q.control === "free_a");
    expect(c?.ratio).toBeNull();
  });

  it("greedy matches exhaustive search on the reference profiles", () => {
    const { controls } = scorable(model);
    for (const r of ref.profiles) {
      const out = recommend(r.profile as EngineProfile, model);
      const start = out.plan.filter((p) => p.already_in_place).map((p) => p.control);
      const ex = exhaustive(out.base, controls, start, out.totals.budget_inr);
      expect(out.totals.loss_after_plan_inr).toBeLessThanOrEqual(ex.loss * (1 + 1e-9) + 1e-9);
    }
  });
});
