import js from "@eslint/js";
import globals from "globals";
export default [
  {
    files: ["app/static/js/**/*.js"],
    ...js.configs.recommended,
    languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: globals.browser },
  },
  {
    files: ["tests/frontend/**/*.mjs", "tests/browser/**/*.mjs", "playwright.config.mjs"],
    ...js.configs.recommended,
    languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: globals.node },
  },
];
