import Link from "next/link";

export default function NotFound() {
  return (
    <section className="wrap py-20">
      <p className="label">404</p>
      <h1 className="text-4xl mt-2">This page is not here</h1>
      <p className="mt-4 max-w-xl text-muted">The link may be old or mistyped. Your saved answers, if any, are still on this device.</p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link className="btn" href="/">
          Go home
        </Link>
        <Link className="btn btn-ghost" href="/assess/">
          Start an assessment
        </Link>
      </div>
    </section>
  );
}
