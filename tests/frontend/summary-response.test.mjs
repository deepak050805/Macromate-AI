import assert from "node:assert/strict";
import { test } from "node:test";
import { validateProgressSummary } from "../../app/static/js/responses.js";

const summary = { total: 2, dated: 2, average_weight: 70, average_calories: 2000,
  first_date: "2024-02-01", last_date: "2024-02-21", weight_change: 1 };
for (const invalid of [
  { total: Number.MAX_SAFE_INTEGER + 1 }, { dated: 3 }, { average_weight: 501 },
  { average_calories: 20001 }, { weight_change: -501 }, { first_date: "2024-02-30" },
  { first_date: "2024-02-22" }, { last_date: undefined }, { dated: 1, weight_change: 0 },
]) test(`summary response rejects ${JSON.stringify(invalid)}`, () => {
  assert.throws(() => validateProgressSummary({ ...summary, ...invalid }), /unreadable response/);
});
test("empty summaries retain null values rather than invented zero measurements", () => {
  const empty = { total: 0, dated: 0, average_weight: null, average_calories: null,
    first_date: null, last_date: null, weight_change: null };
  assert.equal(validateProgressSummary(empty), empty);
  assert.throws(() => validateProgressSummary({ ...empty, average_weight: 0 }), /unreadable response/);
});
test("unfiltered legacy summaries can contain undated entries and rounded tiny weights", () => {
  const legacy = { ...summary, dated: 1, weight_change: null, average_weight: 0 };
  assert.equal(validateProgressSummary(legacy), legacy);
  assert.throws(() => validateProgressSummary(legacy, { date_from: "2024-01-01" }), /unreadable response/);
});
test("filtered summaries cannot describe records outside the requested dates", () => {
  assert.throws(() => validateProgressSummary(summary, { date_from: "2024-02-02" }), /unreadable response/);
  assert.throws(() => validateProgressSummary(summary, { date_to: "2024-02-20" }), /unreadable response/);
  assert.equal(validateProgressSummary(summary, { date_from: "2024-02-01", date_to: "2024-02-21" }), summary);
});
