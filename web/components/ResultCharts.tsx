"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { inr, num } from "@/lib/format";

const TICK = { fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-plex-mono)" };

type Item = { name: string; value: number; chosen?: boolean };

function inrLabel(v: unknown) {
  return typeof v === "number" ? inr(v) : "";
}

function distLabel(v: unknown) {
  return typeof v === "number" ? num(v, 2) : "";
}

function short(s: unknown) {
  const t = String(s);
  return t.length > 30 ? `${t.slice(0, 28)}…` : t;
}

export function PersonaChart({ data }: { data: Item[] }) {
  return (
    <div className="mt-4 h-[280px]" role="img" aria-label="Distance from your profile to each persona; the chosen persona is highlighted">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 48, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={TICK} stroke="var(--rule)" />
          <YAxis type="category" dataKey="name" width={170} tick={TICK} tickFormatter={short} stroke="var(--rule)" />
          <Bar dataKey="value" isAnimationActive={false} barSize={14}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.chosen ? "var(--ink)" : "var(--rule)"} />
            ))}
            <LabelList dataKey="value" position="right" formatter={distLabel} style={TICK} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LossChart({ data }: { data: Item[] }) {
  return (
    <div className="mt-4 h-[280px]" role="img" aria-label="Expected yearly loss for each attack type in rupees">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 64, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="var(--grid)" />
          <XAxis type="number" tick={TICK} tickFormatter={inrLabel} stroke="var(--rule)" />
          <YAxis type="category" dataKey="name" width={130} tick={TICK} stroke="var(--rule)" />
          <Bar dataKey="value" fill="var(--risk)" isAnimationActive={false} barSize={16}>
            <LabelList dataKey="value" position="right" formatter={inrLabel} style={TICK} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
