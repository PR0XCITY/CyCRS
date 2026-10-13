import { renderTex } from "@/lib/tex";

type Props = { tex: string; display?: boolean; label?: string };

export default function Tex({ tex, display = true, label }: Props) {
  const html = renderTex(tex, display);
  return <span className="tex" role="math" aria-label={label ?? tex} dangerouslySetInnerHTML={{ __html: html }} />;
}
