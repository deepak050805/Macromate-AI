import assert from "node:assert/strict";
import { test } from "node:test";
import { utcDateRange } from "../../app/static/js/date-ranges.js";

for (const [days, date, expected] of [
  [7, "2024-03-01T00:30:00+05:30", { date_from: "2024-02-23", date_to: "2024-02-29" }],
  [30, "2024-03-01T12:00:00Z", { date_from: "2024-02-01", date_to: "2024-03-01" }],
  [7, "2024-01-02T12:00:00Z", { date_from: "2023-12-27", date_to: "2024-01-02" }],
  [30, "2000-01-02T12:00:00Z", { date_from: "2000-01-01", date_to: "2000-01-02" }],
  [1, "2024-05-01T12:00:00Z", { date_from: "2024-05-01", date_to: "2024-05-01" }],
]) test(`UTC presets include exactly the requested interval at ${date}`, () => {
  assert.deepEqual(utcDateRange(days, new Date(date)), expected);
});
for (const days of [0, -1, 367, 1.5, "7", null]) test(`invalid interval ${JSON.stringify(days)} is rejected`, () => {
  assert.throws(() => utcDateRange(days), RangeError);
});
test("an invalid clock cannot produce a malformed filter", () => {
  assert.throws(() => utcDateRange(7, new Date("invalid")), RangeError);
});
