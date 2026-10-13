"use client";

import dynamic from "next/dynamic";
import { Heatmap, Matrix } from "@/components/TableCharts";

type Chart = { type: string; title: string; x_label: string; y_label: string; data: unknown[] };

function Placeholder() {
  return <div className="h-full w-full" aria-hidden="true" />;
}

const CardChart = dynamic(() => import("@/components/CardChart"), { ssr: false, loading: Placeholder });

export default function LazyCardChart({ chart }: { chart: Chart }) {
  if (chart.type === "matrix") return <Matrix chart={chart} />;
  if (chart.type === "heatmap") return <Heatmap chart={chart} />;
  return (
    <figure className="panel p-3">
      <figcaption className="text-sm font-medium">{chart.title}</figcaption>
      <p className="label mt-0.5">
        {chart.x_label} / {chart.y_label}
      </p>
      <div className="mt-2 h-[280px]" role="img" aria-label={`${chart.title}: ${chart.y_label} by ${chart.x_label}`}>
        <CardChart chart={chart} />
      </div>
    </figure>
  );
}
