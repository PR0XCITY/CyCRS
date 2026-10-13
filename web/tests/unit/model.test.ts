import { describe, expect, it } from "vitest";
import ref from "@/tests/fixtures/reference.json";
import { model } from "@/lib/data";
import { type EngineProfile, recommend } from "@/lib/model";

const TOL = 1e-6;

function close(a: unknown, b: unknown, path: string) {
  if (typeof b === "number") {
    expect(typeof a, path).toBe("number");
    const d = Math.abs((a as number) - b);
    expect(d, `${path}: ${String(a)} vs ${b}`).toBeLessThanOrEqual(TOL * Math.max(1, Math.abs(b)));
    return;
  }
  if (b === null) {
    expect(a, path).toBeNull();
    return;
  }
  if (Array.isArray(b)) {
    expect(Array.isArray(a), path).toBe(true);
    expect((a as unknown[]).length, `${path} length`).toBe(b.length);
    b.forEach((x, i) => close((a as unknown[])[i], x, `${path}[${i}]`));
    return;
  }
  if (typeof b === "object") {
    for (const [k, v] of Object.entries(b as Record<string, unknown>)) close((a as Record<string, unknown>)[k], v, `${path}.${k}`);
    return;
  }
  expect(a, path).toEqual(b);
}

describe("model.ts reproduces recommend() from Python", () => {
  it("has five reference profiles", () => {
    expect(ref.profiles).toHaveLength(5);
  });
  for (const r of ref.profiles) {
    it(`matches plan and full trace: ${String((r.profile as { name?: string }).name)}`, () => {
      const out = recommend(r.profile as EngineProfile, model);
      close(out.plan, r.plan, "plan");
      close(out.features, r.features, "features");
      close(out.categories, r.categories, "categories");
      close(out.persona, r.persona, "persona");
      close(out.greedy_steps, r.greedy_steps, "greedy_steps");
      close(out.not_scored, r.not_scored, "not_scored");
      close(out.totals, r.totals, "totals");
      close(out.inputs, r.inputs, "inputs");
      expect(out.estimate).toBe(true);
    });
  }
});
