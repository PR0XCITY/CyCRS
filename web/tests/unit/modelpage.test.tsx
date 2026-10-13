import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import ModelPage, { SECTIONS } from "@/components/ModelPage";
import { cards } from "@/lib/data";

afterEach(() => {
  cleanup();
});

describe("ModelPage renders every card", () => {
  it("has cards in pipeline order", () => {
    const o = cards.map((c) => c.order);
    expect(o).toEqual([...o].sort((a, b) => a - b));
    expect(cards.length).toBeGreaterThan(0);
  });

  for (const c of cards) {
    it(`${c.id} has all seven sections and content`, () => {
      const { container, getByRole } = render(<ModelPage card={c.card} all={cards} />);
      for (let i = 0; i < SECTIONS.length; i++) {
        const s = container.querySelector(`[data-section="${i + 1}"]`);
        expect(s, `section ${i + 1}`).not.toBeNull();
        expect(s?.querySelector("h2")?.textContent).toBe(SECTIONS[i]);
        expect(s?.textContent?.length ?? 0, `section ${i + 1} empty`).toBeGreaterThan(SECTIONS[i]?.length ?? 0);
      }
      expect(getByRole("heading", { level: 1 }).textContent).toBe(c.card.title);
      expect(container.querySelectorAll('[data-section="2"] table').length).toBeGreaterThanOrEqual(2);
      expect(container.querySelectorAll('[data-section="4"] .katex').length).toBe(c.card.formula_tex.length);
      if (c.used_live) expect(container.querySelector('a[href^="/assess"]')).not.toBeNull();
      for (const f of c.card.feeds) {
        if (cards.some((x) => x.id === f)) expect(container.querySelector(`a[href="/models/${f}/"], a[href="/models/${f}"]`), f).not.toBeNull();
      }
    });
  }
});
