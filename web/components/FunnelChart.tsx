"use client";

import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { count } from "@/lib/format";

const TICK = { fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-plex-mono)" };

function rowsLabel(v: unknown) {
  return typeof v === "number" ? count(v) : "";
}

export default function FunnelChart({ steps }: { steps: { step: string; rows: number }[] }) {
  return (
    <div className="h-[240px]" role="img" aria-label="Rows kept at each cleaning step">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={steps} layout="vertical" margin={{ left: 8, right: 64, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={TICK} stroke="var(--rule)" tickFormatter={rowsLabel} />
          <YAxis type="category" dataKey="step" width={190} tick={TICK} stroke="var(--rule)" />
          <Bar dataKey="rows" fill="var(--ink)" isAnimationActive={false} barSize={18}>
            <LabelList dataKey="rows" position="right" formatter={rowsLabel} style={TICK} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
