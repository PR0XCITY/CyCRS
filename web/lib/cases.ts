import { cardById, keyNumber, model, sources } from "@/lib/data";
import { type EngineProfile, recommend } from "@/lib/model";

function replayRows() {
  const t = cardById("case-replay")?.results.tables.find((x) => x.columns.includes("verdict"));
  if (!t) return new Map<string, Record<string, unknown>>();
  return new Map(t.rows.map((r) => [String(r[t.columns.indexOf("case")]), Object.fromEntries(t.columns.map((c, i) => [c, r[i]]))]));
}

export function caseRuns() {
  const budget = keyNumber("case-replay", "budget_inr") ?? 0;
  const rows = replayRows();
  return sources.cases.map((c) => {
    const profile: EngineProfile = { name: c.name, sector: c.profile.sector, size: c.profile.size, assets: c.profile.assets, controls: [], budget_inr: budget };
    const rec = recommend(profile, model);
    const row = rows.get(c.name);
    return {
      c,
      profile,
      rec,
      budget,
      top3: rec.plan.slice(0, 3).map((p) => p.control),
      verdict: row ? String(row.verdict) : "not replayed",
      cardTop3: row ? String(row.top3).split("; ").filter(Boolean) : [],
    };
  });
}
