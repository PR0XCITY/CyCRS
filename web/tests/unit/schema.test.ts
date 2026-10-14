import { afterEach, describe, expect, it } from "vitest";
import modelJson from "@/public/model/model.json";
import { CONTROL_NAMES, loadProfile, PROFILE_KEY, schemas, SECTORS } from "@/lib/profile";
import { modelSchema } from "@/lib/schema";

const GOOD = {
  sector: SECTORS[0] as string,
  employees: 12,
  country: "India",
  state: "Maharashtra",
  city: "Pune",
  devices: 6,
  website: true,
  payments: true,
  customerData: true,
  cloud: false,
  controls: [CONTROL_NAMES[0] as string],
  budget: 25000,
};

afterEach(() => {
  window.localStorage.clear();
});

describe("profile validation", () => {
  it("accepts a valid profile", () => {
    expect(schemas.profile.safeParse(GOOD).success).toBe(true);
  });

  const BAD: [string, Record<string, unknown>][] = [
    ["unknown sector", { sector: "Hackers Inc" }],
    ["negative employees", { employees: -3 }],
    ["fractional employees", { employees: 2.5 }],
    ["budget below minimum", { budget: 100 }],
    ["budget above maximum", { budget: 9e9 }],
    ["budget as string", { budget: "25000" }],
    ["unknown control", { controls: ["Magic shield"] }],
    ["duplicate control", { controls: [CONTROL_NAMES[0], CONTROL_NAMES[0]] }],
    ["script in city", { city: "<script>alert(1)</script>" }],
    ["empty city", { city: " " }],
    ["boolean as string", { website: "yes" }],
  ];
  for (const [name, patch] of BAD) {
    it(`rejects ${name}`, () => {
      expect(schemas.profile.safeParse({ ...GOOD, ...patch }).success).toBe(false);
    });
  }

  it("rejects extra keys added by tampering", () => {
    expect(schemas.profile.safeParse({ ...GOOD, isAdmin: true }).success).toBe(false);
  });

  it("loadProfile discards tampered storage", () => {
    window.localStorage.setItem(PROFILE_KEY, JSON.stringify({ ...GOOD, budget: -1 }));
    expect(loadProfile()).toBeNull();
    expect(window.localStorage.getItem(PROFILE_KEY)).toBeNull();
  });

  it("loadProfile discards malformed JSON", () => {
    window.localStorage.setItem(PROFILE_KEY, "{not json");
    expect(loadProfile()).toBeNull();
  });

  it("loadProfile returns a valid stored profile", () => {
    window.localStorage.setItem(PROFILE_KEY, JSON.stringify(GOOD));
    expect(loadProfile()).toEqual(GOOD);
  });
});

describe("model validation", () => {
  it("accepts the exported model", () => {
    expect(modelSchema.safeParse(modelJson).success).toBe(true);
  });

  it("rejects a tampered coefficient", () => {
    const m = structuredClone(modelJson) as { attack: { models: Record<string, { coefficients: Record<string, unknown> }> } };
    const first = Object.values(m.attack.models)[0];
    if (first) first.coefficients[Object.keys(first.coefficients)[0] as string] = "1e9";
    expect(modelSchema.safeParse(m).success).toBe(false);
  });
});
