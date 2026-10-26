import assert from "node:assert/strict";
import { test } from "node:test";
import { validateProgressPage } from "../../app/static/js/responses.js";

const message = "The server returned an unreadable response. Try again.";
const record = { id: 1, date: "2024-02-29", weight: 70, calories: 2000 };
const page = (overrides = {}) => ({
  page: 1, pages: 3, total: 45, records: [{ ...record }], ...overrides,
});

for (const [name, overrides] of [
  ["missing record list", { records: undefined }],
  ["non-array record list", { records: {} }],
  ["string page count", { pages: "3" }],
  ["negative page count", { pages: -1 }],
  ["unsafe page count", { pages: Number.MAX_SAFE_INTEGER + 1 }],
  ["fractional page", { page: 1.5 }],
  ["wrong echoed page", { page: 2 }],
  ["unrequestable page", { page: 10001 }],
  ["negative total", { total: -1 }],
  ["non-finite total", { total: Infinity }],
  ["too many records", { records: Array.from({ length: 21 }, () => ({ ...record })) }],
]) {
  test(`history response rejects ${name}`, () => {
    assert.throws(() => validateProgressPage(page(overrides), 1), { message });
  });
}

for (const [name, invalid] of [
  ["null record", null],
  ["unsafe identity", { ...record, id: Number.MAX_SAFE_INTEGER + 1 }],
  ["zero identity", { ...record, id: 0 }],
  ["numeric text weight", { ...record, weight: "70" }],
  ["infinite weight", { ...record, weight: Infinity }],
  ["out-of-range weight", { ...record, weight: 501 }],
  ["fractional calories", { ...record, calories: 2000.5 }],
  ["out-of-range calories", { ...record, calories: -1 }],
  ["missing date", { id: 1, weight: 70, calories: 2000 }],
  ["impossible calendar date", { ...record, date: "2024-02-30" }],
  ["unrepresentable year zero", { ...record, date: "0000-01-01" }],
  ["non-canonical date", { ...record, date: "2024-2-1" }],
  ["numeric date", { ...record, date: 20240201 }],
]) {
  test(`history response rejects ${name}`, () => {
    assert.throws(() => validateProgressPage(page({ records: [invalid] }), 1), { message });
  });
}

test("history response preserves valid sparse pages without inventing total consistency", () => {
  const response = page();
  assert.equal(validateProgressPage(response, 1), response);
});

test("history response permits an empty out-of-range page for normal fallback", () => {
  const response = page({ page: 3, pages: 1, total: 1, records: [] });
  assert.equal(validateProgressPage(response, 3), response);
});

test("history response retains undated and historical legacy records", () => {
  const response = page({ records: [
    { ...record, date: null },
    { ...record, id: 2, date: "1999-12-31", weight: 0.5, calories: 0 },
    { ...record, id: 3, date: "0001-01-01" },
  ] });
  assert.equal(validateProgressPage(response, 1), response);
});
