"use client";

import dynamic from "next/dynamic";

function Space() {
  return <div className="h-[240px]" aria-hidden="true" />;
}

const FunnelChart = dynamic(() => import("@/components/FunnelChart"), { ssr: false, loading: Space });

export default function LazyFunnel({ steps }: { steps: { step: string; rows: number }[] }) {
  return <FunnelChart steps={steps} />;
}
