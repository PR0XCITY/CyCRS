import cardsJson from "@/public/model/cards.json";
import lineageJson from "@/public/model/lineage.json";
import sourcesJson from "@/public/model/sources.json";
import modelJson from "@/public/model/model.json";
import { cardsSchema, lineageSchema, modelSchema, sourcesSchema } from "@/lib/schema";

export const model = modelSchema.parse(modelJson);
export const cards = cardsSchema.parse(cardsJson);
export const sources = sourcesSchema.parse(sourcesJson);
export const lineage = lineageSchema.parse(lineageJson);

export function cardById(id: string) {
  return cards.find((c) => c.id === id)?.card;
}

export function keyNumber(id: string, key: string): number | undefined {
  const v = cardById(id)?.results.key_numbers[key];
  return typeof v === "number" ? v : undefined;
}
