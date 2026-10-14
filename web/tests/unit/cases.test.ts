import { describe, expect, it } from "vitest";
import { caseRuns } from "@/lib/cases";

describe("case replay in the browser engine", () => {
  const runs = caseRuns();

  it("replays at least four cases", () => {
    expect(runs.length).toBeGreaterThanOrEqual(4);
    expect(runs[0]?.budget).toBeGreaterThan(0);
  });

  for (const r of runs) {
    it(`${r.c.name}: top 3 matches the Python replay card`, () => {
      expect(r.top3).toEqual(r.cardTop3);
      expect(r.verdict).not.toBe("not replayed");
      expect(r.rec.greedy_steps.length).toBeGreaterThan(0);
    });
  }
});
