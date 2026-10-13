"use client";

import Link from "next/link";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <section className="wrap py-20">
      <p className="label">Something went wrong</p>
      <h1 className="text-4xl mt-2">We could not show this page</h1>
      <p className="mt-4 max-w-xl text-muted">Nothing was sent anywhere; CyCRS runs entirely in your browser. Try again, or start over.</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <button type="button" className="btn" onClick={reset}>
          Try again
        </button>
        <Link className="btn btn-ghost" href="/assess/">
          Start over
        </Link>
      </div>
    </section>
  );
}
