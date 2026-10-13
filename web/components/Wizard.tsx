"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import type { ZodMiniType } from "zod/mini";
import { budgetToSlider, SLIDER_STEPS, sliderToBudget } from "@/lib/budget";
import { inr } from "@/lib/format";
import { CONTROL_NAMES, DRAFT_KEY, PROFILE_KEY, readStored, removeStored, schemas, SECTORS, writeStored } from "@/lib/profile";
import type { ProfileForm } from "@/lib/profileSchema";
import { useIsClient } from "@/lib/useStored";

const STEPS = ["Business", "Digital footprint", "Current controls", "Budget"] as const;
const STEP_SCHEMAS: ZodMiniType[] = [schemas.business, schemas.footprint, schemas.current, schemas.budget];
const EMPTY: ProfileForm = {
  sector: "",
  employees: 0,
  city: "",
  devices: 0,
  website: false,
  payments: false,
  customerData: false,
  cloud: false,
  controls: [],
  budget: 25000,
};
const draftSchema = schemas.draft;

type Errors = Partial<Record<keyof ProfileForm, string>>;

function errorsOf(e: { issues: { path: PropertyKey[]; message: string }[] }): Errors {
  const out: Errors = {};
  for (const i of e.issues) {
    const k = i.path[0] as keyof ProfileForm | undefined;
    if (k && !out[k]) out[k] = i.message;
  }
  return out;
}

type FieldProps = { id: string; label: string; error?: string; hint?: string; children: React.ReactNode };

function Field({ id, label, error, hint, children }: FieldProps) {
  return (
    <div className="col-span-12 md:col-span-6">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      {hint ? <p className="text-xs text-muted mt-0.5">{hint}</p> : null}
      <div className="mt-1.5">{children}</div>
      {error ? (
        <p id={`${id}-err`} role="alert" className="mt-1 text-sm text-risk-ink">
          {error}
        </p>
      ) : null}
    </div>
  );
}

type CheckProps = { id: string; label: string; checked: boolean; onChange: (v: boolean) => void };

function Check({ id, label, checked, onChange }: CheckProps) {
  return (
    <label htmlFor={id} className="col-span-12 md:col-span-6 flex items-start gap-3 panel px-3 py-2.5 cursor-pointer">
      <input id={id} type="checkbox" className="mt-1 size-4 accent-[var(--ink)]" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="text-sm">{label}</span>
    </label>
  );
}

type Draft = { step: number; form: ProfileForm; valid: boolean };

function readDraft(): Draft {
  const raw = readStored(DRAFT_KEY);
  const d = draftSchema.safeParse(raw);
  if (d.success) return { step: d.data.step, form: { ...EMPTY, ...d.data.form }, valid: true };
  return { step: 0, form: EMPTY, valid: raw === null };
}

export default function Wizard() {
  const client = useIsClient();
  if (!client) return <div className="mt-8 min-h-[30rem]" aria-busy="true" />;
  return <WizardForm initial={readDraft()} />;
}

function WizardForm({ initial }: { initial: Draft }) {
  const router = useRouter();
  const uid = useId();
  const [step, setStep] = useState(initial.step);
  const [form, setForm] = useState<ProfileForm>(initial.form);
  const [errors, setErrors] = useState<Errors>({});

  useEffect(() => {
    if (!initial.valid) removeStored(DRAFT_KEY);
  }, [initial.valid]);

  useEffect(() => {
    writeStored(DRAFT_KEY, { step, form });
  }, [step, form]);

  function set<K extends keyof ProfileForm>(k: K, v: ProfileForm[K]) {
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
  }

  function toggleControl(c: string, on: boolean) {
    set("controls", on ? [...form.controls, c] : form.controls.filter((x) => x !== c));
  }

  function validateStep() {
    const s = STEP_SCHEMAS[step];
    if (!s) return false;
    const r = s.safeParse(form);
    if (r.success) {
      setErrors({});
      return true;
    }
    setErrors(errorsOf(r.error));
    return false;
  }

  function nextStep() {
    if (!validateStep()) return;
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    const r = schemas.profile.safeParse(form);
    if (!r.success) {
      setErrors(errorsOf(r.error));
      return;
    }
    writeStored(PROFILE_KEY, r.data);
    removeStored(DRAFT_KEY);
    router.push("/results/");
  }

  function fid(k: string) {
    return `${uid}-${k}`;
  }

  function inv(k: keyof ProfileForm) {
    return { "aria-invalid": errors[k] ? true : undefined, "aria-describedby": errors[k] ? `${fid(k)}-err` : undefined };
  }

  const pctDone = ((step + 1) / STEPS.length) * 100;

  return (
    <form
      className="mt-8"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        nextStep();
      }}
    >
      <div className="flex items-center justify-between text-sm">
        <span className="label">
          Step {step + 1} of {STEPS.length}: {STEPS[step]}
        </span>
        <span className="num text-muted">{Math.round(pctDone)}%</span>
      </div>
      <div className="mt-2 h-1.5 w-full bg-[var(--grid)] rounded-full" role="progressbar" aria-label="Assessment progress" aria-valuemin={1} aria-valuemax={STEPS.length} aria-valuenow={step + 1}>
        <div className="h-full bg-ink rounded-full transition-[width]" style={{ width: `${pctDone}%` }} />
      </div>

      <fieldset className="mt-8 grid12 gap-y-5 min-h-[18rem]">
        <legend className="sr-only">{STEPS[step]}</legend>
        {step === 0 ? (
          <>
            <Field id={fid("sector")} label="Sector" error={errors.sector} hint="Pick the closest. Other uses the average of all remaining sectors.">
              <select id={fid("sector")} className="field" value={form.sector} onChange={(e) => set("sector", e.target.value)} {...inv("sector")}>
                <option value="">Choose a sector</option>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
                <option value="Other">Other</option>
              </select>
            </Field>
            <Field id={fid("employees")} label="Number of employees" error={errors.employees}>
              <input id={fid("employees")} className="field num" type="number" inputMode="numeric" min={1} value={form.employees || ""} onChange={(e) => set("employees", Number(e.target.value))} {...inv("employees")} />
            </Field>
            <Field id={fid("city")} label="City" error={errors.city} hint="Shown on your plan only; it does not change the numbers.">
              <input id={fid("city")} className="field" type="text" autoComplete="address-level2" value={form.city} onChange={(e) => set("city", e.target.value)} {...inv("city")} />
            </Field>
          </>
        ) : null}
        {step === 1 ? (
          <>
            <Field id={fid("devices")} label="Computers, phones and tablets used for work" error={errors.devices}>
              <input id={fid("devices")} className="field num" type="number" inputMode="numeric" min={0} value={Number.isFinite(form.devices) ? form.devices : ""} onChange={(e) => set("devices", Number(e.target.value))} {...inv("devices")} />
            </Field>
            <div className="col-span-12" />
            <Check id={fid("website")} label="We have a website" checked={form.website} onChange={(v) => set("website", v)} />
            <Check id={fid("payments")} label="We take UPI or online payments" checked={form.payments} onChange={(v) => set("payments", v)} />
            <Check id={fid("customerData")} label="We store customer data (records, documents, drives)" checked={form.customerData} onChange={(v) => set("customerData", v)} />
            <Check id={fid("cloud")} label="We use cloud tools (email, office suites, accounting)" checked={form.cloud} onChange={(v) => set("cloud", v)} />
          </>
        ) : null}
        {step === 2 ? (
          <>
            <p className="col-span-12 text-sm text-muted">Tick what you already have in place. These start in your plan at no extra cost.</p>
            {CONTROL_NAMES.map((c, i) => (
              <Check key={c} id={fid(`ctl-${i}`)} label={c} checked={form.controls.includes(c)} onChange={(v) => toggleControl(c, v)} />
            ))}
            {errors.controls ? (
              <p role="alert" className="col-span-12 text-sm text-risk-ink">
                {errors.controls}
              </p>
            ) : null}
          </>
        ) : null}
        {step === 3 ? (
          <Field id={fid("budget")} label="Yearly budget for security" error={errors.budget} hint="Drag to set; the scale is logarithmic from ₹5,000 to ₹5,00,000.">
            <input
              id={fid("budget")}
              type="range"
              className="w-full accent-[var(--ink)]"
              min={0}
              max={SLIDER_STEPS}
              value={budgetToSlider(form.budget)}
              onChange={(e) => set("budget", sliderToBudget(Number(e.target.value)))}
              aria-valuetext={inr(form.budget)}
              {...inv("budget")}
            />
            <p className="num text-3xl mt-3" aria-live="polite">
              {inr(form.budget)}
              <span className="text-sm text-muted"> per year</span>
            </p>
          </Field>
        ) : null}
      </fieldset>

      <div className="mt-8 flex flex-wrap gap-3 rule pt-6">
        <button type="button" className="btn btn-ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>
          Back
        </button>
        <button type="submit" className="btn">
          {step === STEPS.length - 1 ? "See my plan" : "Next"}
        </button>
      </div>
    </form>
  );
}
