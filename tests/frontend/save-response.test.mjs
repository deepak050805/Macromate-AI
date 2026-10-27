import assert from "node:assert/strict";
import { test } from "node:test";
import { validateSavedProgress } from "../../app/static/js/responses.js";

const submitted = { date: "2024-05-01", weight: "70.00", calories: "2000" };
const record = { id: 12, date: submitted.date, weight: 70, calories: 2000 };
for (const saved of [undefined, {}, { ...record, id: 13 }, { ...record, weight: 71 }, { ...record, date: "2024-05-02" }, { ...record, calories: 2001 }]) {
  test(`saved update rejects missing or mismatched record ${JSON.stringify(saved)}`, () => {
    assert.throws(() => validateSavedProgress({ record: saved }, submitted, "12"), /unreadable response/);
  });
}
test("saved create and update accept semantic numeric normalization", () => {
  assert.equal(validateSavedProgress({ record }, submitted), record);
  assert.equal(validateSavedProgress({ record }, submitted, "12"), record);
});
