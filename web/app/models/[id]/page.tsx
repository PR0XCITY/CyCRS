import "katex/dist/katex.min.css";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ModelPage from "@/components/ModelPage";
import { cardById, cards } from "@/lib/data";

export const dynamicParams = false;

export function generateStaticParams() {
  return cards.map((c) => ({ id: c.id }));
}

type Params = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { id } = await params;
  const c = cardById(id);
  return { title: c ? c.title : "Model", description: c?.question };
}

export default async function ModelRoute({ params }: Params) {
  const { id } = await params;
  const card = cardById(id);
  if (!card) notFound();
  return <ModelPage card={card} all={cards} />;
}
