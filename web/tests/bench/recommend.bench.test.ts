import { writeFileSync } from "node:fs";
import { Bench } from "tinybench";
import { expect, it } from "vitest";
import ref from "@/tests/fixtures/reference.json";
import { type EngineProfile, recommend } from "@/lib/model";
import { model } from "@/lib/modelData";

const profiles = ref.profiles.map((r) => r.profile as EngineProfile);
const RUNS = 1000;

function quantile(xs: number[], q: number) {
  const s = [...xs].sort((a, b) => a - b);
  const i = (s.length - 1) * q;
  const lo = Math.floor(i);
  const hi = Math.ceil(i);
  return (s[lo] as number) + ((s[hi] as number) - (s[lo] as number)) * (i - lo);
}

it(`recommend() latency over ${RUNS} runs`, async () => {
  let i = 0;
  const b = new Bench({ iterations: RUNS, time: 0, warmupIterations: 50, warmupTime: 0, retainSamples: true });
  b.add("recommend", function runOne() {
    recommend(profiles[i++ % profiles.length] as EngineProfile, model);
  });
  await b.run();
  const r = b.tasks[0]?.result as unknown as { latency: { samples?: number[]; mean: number } };
  const xs = r.latency.samples ?? [];
  expect(xs.length).toBeGreaterThanOrEqual(RUNS);
  const out = { runs: xs.length, mean_ms: r.latency.mean, p50_ms: quantile(xs, 0.5), p95_ms: quantile(xs, 0.95), p99_ms: quantile(xs, 0.99) };
  if (process.env.BENCH_OUT) writeFileSync(process.env.BENCH_OUT, JSON.stringify(out, null, 2));
  expect(out.p95_ms).toBeLessThan(50);
});
