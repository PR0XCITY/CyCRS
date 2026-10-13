import type { Metadata } from "next";
import { sources } from "@/lib/data";

export const metadata: Metadata = { title: "Indian cases", description: "Documented Indian cyber incidents and how they map to the attack categories CyCRS models." };

export default function CasesPage() {
  return (
    <div className="wrap py-10">
      <p className="label">Cases</p>
      <h1 className="text-4xl md:text-5xl mt-2 max-w-3xl">Indian incidents, in the same categories CyCRS uses</h1>
      <p className="mt-3 text-muted max-w-2xl">Facts are limited to what the linked source states; summaries are written for this project.</p>
      <ol className="mt-8 grid gap-4">
        {sources.cases.map((c, i) => (
          <li key={c.name} className="rule pt-5 grid12 gap-y-2">
            <p className="col-span-12 md:col-span-1 num text-muted">{String(i + 1).padStart(2, "0")}</p>
            <div className="col-span-12 md:col-span-8">
              <h2 className="text-2xl">
                {c.name} <span className="num text-muted text-lg">{c.year}</span>
              </h2>
              <p className="mt-2">{c.summary}</p>
              <p className="mt-2 text-sm">
                <a href={c.source_url} rel="noopener noreferrer">
                  Source
                </a>{" "}
                <span className="text-muted">(accessed {c.accessed})</span>
              </p>
            </div>
            <dl className="col-span-12 md:col-span-3 text-sm grid grid-cols-2 gap-x-3 gap-y-1">
              <dt className="label">Sector</dt>
              <dd>{c.sector}</dd>
              <dt className="label">Size</dt>
              <dd>{c.size_bucket}</dd>
              <dt className="label">Assets</dt>
              <dd>{c.assets}</dd>
              <dt className="label">Actions</dt>
              <dd>{c.actual_actions}</dd>
            </dl>
          </li>
        ))}
      </ol>
    </div>
  );
}
