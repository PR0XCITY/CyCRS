import type { Metadata } from "next";
import { Suspense } from "react";
import Results from "@/components/Results";
import Tex from "@/components/Tex";

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
    <Suspense fallback={<section className="wrap py-10 min-h-[60vh]" aria-busy="true" />}>
      <Results tex={tex} />
    </Suspense>
  );
}
