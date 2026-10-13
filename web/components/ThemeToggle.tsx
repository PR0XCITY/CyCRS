"use client";

import { useEffect } from "react";
import { STORAGE_EVENT } from "@/lib/events";
import { useStoredRaw } from "@/lib/useStored";

const KEY = "cycrs.theme";
const MODES = ["system", "light", "dark"] as const;
type Mode = (typeof MODES)[number];

function toMode(v: string | null | undefined): Mode {
  return MODES.includes(v as Mode) ? (v as Mode) : "system";
}

function applyDom(m: Mode) {
  const el = document.documentElement;
  if (m === "system") el.removeAttribute("data-theme");
  else el.setAttribute("data-theme", m);
}

function store(m: Mode) {
  try {
    if (m === "system") window.localStorage.removeItem(KEY);
    else window.localStorage.setItem(KEY, m);
  } catch {
    applyDom(m);
    return;
  }
  window.dispatchEvent(new Event(STORAGE_EVENT));
}

export default function ThemeToggle() {
  const mode = toMode(useStoredRaw(KEY));
  useEffect(() => {
    applyDom(mode);
  }, [mode]);
  function next() {
    store(MODES[(MODES.indexOf(mode) + 1) % MODES.length] as Mode);
  }
  return (
    <button type="button" onClick={next} className="label border border-rule rounded-[5px] px-2 py-1" aria-label={`Colour theme: ${mode}. Change theme`}>
      Theme: {mode}
    </button>
  );
}
