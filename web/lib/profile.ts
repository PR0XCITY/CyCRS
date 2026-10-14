import { model } from "@/lib/modelData";
import type { EngineProfile } from "@/lib/model";
import { makeProfileSchema, type ProfileForm } from "@/lib/profileSchema";
import { STORAGE_EVENT } from "@/lib/events";

export const PROFILE_KEY = "cycrs.profile.v1";
export const DRAFT_KEY = "cycrs.draft.v1";
export const CONTROL_NAMES = model.controls.map((c) => c.control);
export const SECTORS = model.sectors;
export const STATES = model.states.map((s) => s.name);
export const schemas = makeProfileSchema(SECTORS, CONTROL_NAMES, STATES);

export function stateOf(name: string) {
  return model.states.find((s) => s.name === name);
}

export const ASSET_RULES = [
  { asset: "asset_user_device", answer: "Uses one or more computers, phones or tablets" },
  { asset: "asset_server", answer: "Has a website or uses cloud tools" },
  { asset: "asset_network", answer: "Takes UPI or online payments" },
  { asset: "asset_media", answer: "Stores customer data" },
] as const;

export function sizeBucket(employees: number) {
  if (employees <= model.size_bands.small_max_employees) return "small";
  if (employees <= model.size_bands.medium_max_employees) return "medium";
  return "large";
}

export function assetsOf(p: ProfileForm) {
  const a: string[] = [];
  if (p.devices > 0) a.push("asset_user_device");
  if (p.website || p.cloud) a.push("asset_server");
  if (p.payments) a.push("asset_network");
  if (p.customerData) a.push("asset_media");
  return a;
}

export function toEngine(p: ProfileForm, budget = p.budget): EngineProfile {
  return { sector: p.sector, size: sizeBucket(p.employees), assets: assetsOf(p), controls: p.controls, budget_inr: budget };
}

export function readStored(key: string): unknown {
  try {
    const s = window.localStorage.getItem(key);
    return s === null ? null : JSON.parse(s);
  } catch {
    return null;
  }
}

function notify() {
  window.dispatchEvent(new Event(STORAGE_EVENT));
}

export function writeStored(key: string, v: unknown) {
  try {
    window.localStorage.setItem(key, JSON.stringify(v));
    notify();
    return true;
  } catch {
    return false;
  }
}

export function removeStored(key: string) {
  try {
    window.localStorage.removeItem(key);
    notify();
  } catch {
    return;
  }
}

export function parseJson(raw: string | null | undefined): unknown {
  if (raw === null || raw === undefined) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function parseProfile(raw: string | null | undefined): ProfileForm | null {
  const r = schemas.profile.safeParse(parseJson(raw));
  return r.success ? r.data : null;
}

export function loadProfile(): ProfileForm | null {
  const r = schemas.profile.safeParse(readStored(PROFILE_KEY));
  if (r.success) return r.data;
  removeStored(PROFILE_KEY);
  return null;
}
