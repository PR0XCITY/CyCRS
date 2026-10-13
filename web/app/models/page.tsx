import type { Metadata } from "next";
import Link from "next/link";
import Pipeline from "@/components/Pipeline";
import { cards } from "@/lib/data";

export const metadata: Metadata = { title: "How it works", description: "Every model behind CyCRS, why it was chosen and what it feeds." };

const SYLLABUS: [string, string[]][] = [
  ["Descriptive statistics", ["descriptive", "data-preparation"]],
  ["Probability distributions", ["distribution-fit", "conditional-probability"]],
  ["Hypothesis tests", ["hypothesis-tests", "coverage-hit-rate"]],
  ["Simple linear regression", ["slr"]],
  ["Multiple linear regression", ["mlr-impact"]],
  ["Logistic regression", ["breach-classifiers", "attack-likelihood"]],
  ["Decision tree", ["breach-classifiers"]],
  ["K-nearest neighbours", ["breach-classifiers"]],
  ["Naive Bayes", ["breach-classifiers"]],
  ["Linear discriminant analysis", ["breach-classifiers"]],
  ["ROC curve and AUC", ["breach-classifiers", "attack-likelihood"]],
  ["Confusion matrix", ["breach-classifiers"]],
  ["K-means clustering", ["personas-kmeans"]],
  ["Hierarchical clustering", ["hierarchical"]],
  ["Principal component analysis", ["pca"]],
  ["Factor analysis", ["factor-analysis"]],
];

function firstSentence(s: string) {
  const i = s.search(/\.\s/);
  return i < 0 ? s : s.slice(0, i + 1);
}

export default function ModelsPage() {
  const title = new Map(cards.map((c) => [c.id, c]));
  return (
    <div className="wrap py-10">
      <p className="label">How it works</p>
      <h1 className="text-4xl md:text-5xl mt-2 max-w-3xl">From public breach records to a plan for your budget</h1>
      <p className="mt-3 text-muted max-w-2xl">Each box is a model with its own page: the question, the data, why it was chosen, the maths, the result and its limits.</p>

      <section className="rule mt-8 pt-6" aria-labelledby="m1">
        <p className="label">01</p>
        <h2 id="m1" className="text-2xl mt-1">
          Pipeline
        </h2>
        <div className="mt-4">
          <Pipeline cards={cards} />
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="m2">
        <p className="label">02</p>
        <h2 id="m2" className="text-2xl mt-1">
          Every model
        </h2>
        <div className="scroll-x mt-4">
          <table className="data">
            <thead>
              <tr>
                <th>Model</th>
                <th>Syllabus module</th>
                <th>Question</th>
                <th>Why chosen</th>
                <th>Used live</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link href={`/models/${c.id}/`}>{c.title}</Link>
                  </td>
                  <td>{c.card.module}</td>
                  <td>{c.card.question}</td>
                  <td>{firstSentence(c.card.why)}</td>
                  <td>{c.used_live ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="m3">
        <p className="label">03</p>
        <h2 id="m3" className="text-2xl mt-1">
          Syllabus coverage
        </h2>
        <div className="scroll-x mt-4">
          <table className="data">
            <thead>
              <tr>
                <th>Technique</th>
                <th>Module</th>
                <th>Card</th>
              </tr>
            </thead>
            <tbody>
              {SYLLABUS.map(([t, ids]) => (
                <tr key={t}>
                  <td>{t}</td>
                  <td>{ids.map((i) => title.get(i)?.card.module ?? "").filter(Boolean)[0]}</td>
                  <td>
                    {ids
                      .filter((i) => title.has(i))
                      .map((i, k) => (
                        <span key={i}>
                          {k > 0 ? ", " : ""}
                          <Link href={`/models/${i}/`}>{title.get(i)?.title}</Link>
                        </span>
                      ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rule mt-10 pt-6" aria-labelledby="m4">
        <p className="label">04</p>
        <h2 id="m4" className="text-2xl mt-1">
          Assumptions and limitations
        </h2>
        <div className="mt-4 grid gap-3">
          {cards.map((c) => (
            <details key={c.id} className="panel">
              <summary className="cursor-pointer px-4 py-3 text-sm font-medium">{c.title}</summary>
              <div className="px-4 pb-4 text-sm">
                <ul className="list-disc pl-5 space-y-1">
                  {c.card.assumptions.map((a) => (
                    <li key={a.check}>
                      {a.check}: <strong>{a.verdict}</strong>. {a.action_taken}
                    </li>
                  ))}
                </ul>
                <ul className="list-disc pl-5 space-y-1 mt-3 text-muted">
                  {c.card.limitations.map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              </div>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
