import modelJson from "@/public/model/model.json";
import type { Model } from "@/lib/schema";

export const model = modelJson as unknown as Model;
