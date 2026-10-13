import { array, boolean, enum as zenum, int, maxLength, maximum, minLength, minimum, number, object, partial, refine, regex, strictObject, string, trim } from "zod/mini";

export const BUDGET_MIN = 5000;
export const BUDGET_MAX = 500000;

export type ProfileForm = {
  sector: string;
  employees: number;
  city: string;
  devices: number;
  website: boolean;
  payments: boolean;
  customerData: boolean;
  cloud: boolean;
  controls: string[];
  budget: number;
};

function unique(a: unknown) {
  return Array.isArray(a) && new Set(a).size === a.length;
}

export function makeProfileSchema(sectors: readonly string[], controls: readonly string[]) {
  const businessShape = {
    sector: zenum(["Other", ...sectors], { error: "Choose a sector" }),
    employees: int({ error: "Enter a whole number" }).check(minimum(1, { error: "At least 1 person" }), maximum(1000000, { error: "Too large" })),
    city: string({ error: "Enter your city" })
      .check(
        trim(),
        minLength(2, { error: "Enter your city" }),
        maxLength(60, { error: "Keep it under 60 characters" }),
        regex(/^[\p{L} .'-]+$/u, { error: "Letters, spaces, dots and hyphens only" }),
      ),
  };
  const footprintShape = {
    devices: int({ error: "Enter a whole number" }).check(minimum(0, { error: "Cannot be negative" }), maximum(100000, { error: "Too large" })),
    website: boolean(),
    payments: boolean(),
    customerData: boolean(),
    cloud: boolean(),
  };
  const currentShape = {
    controls: array(zenum(controls as [string, ...string[]], { error: "Unknown control" }))
      .check(maxLength(controls.length), refine(unique, { error: "Duplicate control" })),
  };
  const budgetShape = {
    budget: number({ error: "Choose a budget" }).check(minimum(BUDGET_MIN, { error: "Minimum is ₹5,000" }), maximum(BUDGET_MAX, { error: "Maximum is ₹5,00,000" })),
  };
  const profile = strictObject({ ...businessShape, ...footprintShape, ...currentShape, ...budgetShape });
  return {
    business: object(businessShape),
    footprint: object(footprintShape),
    current: object(currentShape),
    budget: object(budgetShape),
    profile,
    draft: strictObject({ step: int().check(minimum(0), maximum(3)), form: partial(profile) }),
  };
}
