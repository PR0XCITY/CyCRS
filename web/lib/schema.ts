import { z } from "zod";

const num = z.number().finite();
const logit = z.object({ intercept: num, coefficients: z.record(z.string(), num) });

export const modelSchema = z.object({
  version: z.string(),
  sectors: z.array(z.string()),
  sizes: z.array(z.string()),
  assets: z.array(z.string()),
  categories: z.array(z.string()),
  attack: z.object({
    feature_order: z.array(z.string()),
    sectors: z.array(z.string()),
    reference_levels: z.object({ sector: z.string(), size: z.string() }),
    models: z.record(z.string(), logit),
  }),
  impact: z.object({
    target: z.string(),
    features: z.array(z.string()),
    intercept: num,
    coefficients: z.record(z.string(), num),
    residual_sd: num,
    reference_levels: z.object({ sector: z.string(), size: z.string() }),
    sectors: z.array(z.string()),
  }),
  personas: z.object({
    feature_order: z.array(z.string()),
    scaler: z.object({ type: z.string(), mean: z.array(num), scale: z.array(num), reason: z.string() }),
    centroids: z.array(z.array(num)),
    names: z.array(z.string()),
    attack_mix: z.record(z.string(), z.record(z.string(), num)),
  }),
  controls: z.array(
    z.object({
      control: z.string(),
      mitigates: z.array(z.string()),
      effectiveness: num.nullable(),
      effectiveness_key: z.string(),
      effectiveness_url: z.string(),
      effectiveness_fallback_level: z.string(),
      annual_cost_inr: num.nullable(),
      cost_basis: z.string(),
      cost_url: z.string(),
      cost_excerpt: z.string(),
      coverage: z.record(z.string(), num),
    }),
  ),
  config: z.record(
    z.string(),
    z.object({ value: num, unit: z.string(), fallback_level: z.string(), source_key: z.string() }),
  ),
});

const tableSchema = z.object({ title: z.string(), columns: z.array(z.string()), rows: z.array(z.array(z.unknown())) });
const chartSchema = z.object({
  type: z.string(),
  title: z.string(),
  x_label: z.string(),
  y_label: z.string(),
  data: z.array(z.unknown()),
});

export const cardSchema = z.object({
  id: z.string(),
  title: z.string(),
  module: z.string(),
  stage: z.string(),
  used_live: z.boolean(),
  order: z.number(),
  question: z.string(),
  data_in: z.object({
    dataset: z.string(),
    n_rows: z.number(),
    variables: z.array(z.object({ name: z.string(), type: z.string(), scale: z.string(), transform: z.string() })),
    prep_steps: z.array(z.string()),
    sample_rows: z.array(z.record(z.string(), z.unknown())),
  }),
  why: z.string(),
  data_properties: z.array(z.object({ name: z.string(), value: z.unknown(), implication: z.string() })),
  alternatives: z.array(z.object({ model: z.string(), why_not: z.string() })),
  formula_tex: z.array(z.object({ label: z.string(), tex: z.string() })),
  assumptions: z.array(
    z.object({
      check: z.string(),
      statistic: z.unknown(),
      p_value: z.unknown(),
      verdict: z.string(),
      action_taken: z.string(),
    }),
  ),
  results: z.object({
    key_numbers: z.record(z.string(), z.unknown()),
    tables: z.array(tableSchema),
    charts: z.array(chartSchema),
  }),
  yields: z.string(),
  feeds: z.array(z.string()),
  limitations: z.array(z.string()),
});

export const cardsSchema = z.array(
  z.object({
    id: z.string(),
    order: z.number(),
    stage: z.string(),
    used_live: z.boolean(),
    title: z.string(),
    card: cardSchema,
  }),
);

export const sourcesSchema = z.object({
  values: z.array(
    z.object({
      key: z.string(),
      value: num,
      unit: z.string(),
      publisher: z.string(),
      url: z.string(),
      excerpt: z.string(),
      fallback_level: z.string(),
    }),
  ),
  bibliography: z.array(
    z.object({ publisher: z.string(), title: z.string(), year: z.string(), url: z.string(), used_for: z.string() }),
  ),
  cases: z.array(
    z.object({
      name: z.string(),
      year: z.string(),
      sector: z.string(),
      size_bucket: z.string(),
      assets: z.string(),
      actual_actions: z.string(),
      summary: z.string(),
      source_url: z.string(),
      accessed: z.string(),
    }),
  ),
});

export const lineageSchema = z.object({
  steps: z.array(z.object({ step: z.string(), rows: z.number(), rule: z.string() })),
  example_incident: z.object({
    source: z.string(),
    incident: z.record(z.string(), z.unknown()),
    flattened: z.record(z.string(), z.unknown()),
  }),
  datasets: z.array(
    z.object({
      dataset: z.string(),
      publisher: z.string(),
      url: z.string(),
      version: z.string(),
      access_date: z.string(),
      sha256: z.string(),
      files: z.string(),
      notes: z.string(),
    }),
  ),
});

export type Model = z.infer<typeof modelSchema>;
export type Card = z.infer<typeof cardSchema>;
export type CardEntry = z.infer<typeof cardsSchema>[number];
export type Sources = z.infer<typeof sourcesSchema>;
export type Lineage = z.infer<typeof lineageSchema>;

export const BUDGET_MIN = 5000;
export const BUDGET_MAX = 500000;

export function makeProfileSchema(sectors: readonly string[], controls: readonly string[]) {
  const sectorEnum = z.enum(["Other", ...sectors]);
  const controlEnum = z.enum(controls as [string, ...string[]]);
  const business = z.object({
    sector: sectorEnum,
    employees: z.number().int("Enter a whole number").min(1, "At least 1 person").max(1000000, "Too large"),
    city: z
      .string()
      .trim()
      .min(2, "Enter your city")
      .max(60, "Keep it under 60 characters")
      .regex(/^[\p{L} .'-]+$/u, "Letters, spaces, dots and hyphens only"),
  });
  const footprint = z.object({
    devices: z.number().int("Enter a whole number").min(0, "Cannot be negative").max(100000, "Too large"),
    website: z.boolean(),
    payments: z.boolean(),
    customerData: z.boolean(),
    cloud: z.boolean(),
  });
  const current = z.object({
    controls: z
      .array(controlEnum)
      .max(controls.length)
      .refine((a) => new Set(a).size === a.length, "Duplicate control"),
  });
  const budget = z.object({
    budget: z.number().min(BUDGET_MIN, "Minimum is ₹5,000").max(BUDGET_MAX, "Maximum is ₹5,00,000"),
  });
  const profile = z.strictObject({ ...business.shape, ...footprint.shape, ...current.shape, ...budget.shape });
  return { business, footprint, current, budget, profile };
}

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
