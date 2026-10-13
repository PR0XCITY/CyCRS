import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const config = [
  ...nextVitals,
  ...nextTs,
  { ignores: [".next/**", "out/**", "node_modules/**", "playwright-report/**", "test-results/**", "next-env.d.ts"] },
  {
    settings: { react: { version: "19.3" } },
    rules: {
      "no-console": "error",
      "func-style": ["error", "declaration"],
      "react/no-danger": "error",
    },
  },
  { files: ["components/Tex.tsx"], rules: { "react/no-danger": "off" } },
];

export default config;
