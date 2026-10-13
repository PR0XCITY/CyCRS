import { BUDGET_MAX, BUDGET_MIN } from "@/lib/profileSchema";

export const SLIDER_STEPS = 1000;

export function sliderToBudget(v: number) {
  const b = BUDGET_MIN * (BUDGET_MAX / BUDGET_MIN) ** (v / SLIDER_STEPS);
  return Math.min(BUDGET_MAX, Math.max(BUDGET_MIN, Math.round(b / 100) * 100));
}

export function budgetToSlider(b: number) {
  const c = Math.min(BUDGET_MAX, Math.max(BUDGET_MIN, b));
  return Math.round((SLIDER_STEPS * Math.log(c / BUDGET_MIN)) / Math.log(BUDGET_MAX / BUDGET_MIN));
}
