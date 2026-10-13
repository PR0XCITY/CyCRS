import type { Metadata } from "next";
import Wizard from "@/components/Wizard";

export const metadata: Metadata = { title: "Assess your business" };

export default function AssessPage() {
  return (
    <section className="wrap py-10">
      <p className="label">Assessment</p>
      <h1 className="text-4xl mt-2">Tell us about your business</h1>
      <p className="mt-3 text-muted max-w-2xl">Four short steps. Your answers stay in this browser; nothing is sent to a server.</p>
      <Wizard />
    </section>
  );
}
