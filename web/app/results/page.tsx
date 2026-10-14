import "katex/dist/katex.min.css";
import type { Metadata } from "next";
import { Suspense } from "react";
import Results from "@/components/Results";
import Link from "next/link";
import Tex from "@/components/Tex";
import { num } from "@/lib/format";
import { model } from "@/lib/modelData";

export const metadata: Metadata = { title: "Your risk and plan" };

const F = {
  logit: String.raw`z_c = \beta_{0c} + \sum_j \beta_{jc}\,x_j`,
  sigmoid: String.raw`p_c = \frac{1}{1+e^{-z_c}}`,
  impact: String.raw`I_c = \left(10^{\hat y_c}-1\right)\times \text{cost per record}`,
  loss: String.raw`L_c = \pi \, p_c \, I_c`,
  combine: String.raw`L_c(S) = L_c \prod_{k\in S}\left(1-e_k\,s_{kc}\right)`,
  greedy: String.raw`k^{*}=\arg\max_{k:\,c_k\le B}\ \frac{L(S)-L(S\cup\{k\})}{c_k}`,
  distance: String.raw`d_m = \sum_j \left(x_j-\mu_{mj}\right)^2`,
};

function prettyLevel(s: string) {
  if (!s) return "direct value";
  return s.replace(/^\d+_/, "").replace(/_/g, " ");
}

function Disclaimer() {
  return (
    <aside className="wrap mb-6" aria-label="Estimates disclaimer">
      <div className="panel px-4 py-3 text-sm border-l-4" style={{ borderLeftColor: "var(--risk)" }}>
        <p>
          <strong>These are estimates.</strong> They combine public breach records with published averages. Because breach records and costs come mostly from large
          organisations, the cost of one incident is capped for small and medium businesses using a UK government survey of small-business breach costs; treat the
          rupee figures as an upper range and trust the ranking of risks and controls most.
        </p>
        <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-muted">
          {Object.entries(model.config).map(([k, v]) => (
            <li key={k}>
              {k.replace(/_/g, " ")}: <span className="num">{num(v.value, 4)}</span> ({prettyLevel(v.fallback_level)})
            </li>
          ))}
        </ul>
        <p className="mt-2">
          <Link href="/data/">See every source and its fallback level</Link>
        </p>
      </div>
    </aside>
  );
}

export default function ResultsPage() {
  const tex = {
    logit: <Tex tex={F.logit} label="z equals intercept plus the sum of coefficient times feature" />,
    sigmoid: <Tex tex={F.sigmoid} label="p equals one over one plus e to the minus z" />,
    impact: <Tex tex={F.impact} label="impact equals ten to the power y minus one, times cost per record" />,
    loss: <Tex tex={F.loss} label="expected loss equals pi times p times impact" />,
    combine: <Tex tex={F.combine} label="loss with controls equals loss times product of one minus effectiveness times coverage" />,
    greedy: <Tex tex={F.greedy} label="pick the affordable control with the largest loss reduction per rupee" />,
    distance: <Tex tex={F.distance} label="distance equals sum of squared differences from the persona centre" />,
  };
  return (
    <>
      <header className="wrap pt-10 pb-4">
        <p className="label">Your risk report</p>
        <h1 className="text-4xl md:text-5xl mt-2">Action plan</h1>
      </header>
      <Disclaimer />
      <Suspense fallback={<section className="wrap pb-10 min-h-[60vh]" aria-busy="true" />}>
        <Results tex={tex} />
      </Suspense>
    </>
  );
}
