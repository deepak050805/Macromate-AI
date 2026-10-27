import assert from "node:assert/strict";
import { after, test } from "node:test";

const originalDocument = globalThis.document;
globalThis.document = {
  querySelector: (selector) =>
    selector === 'meta[name="csrf-token"]' ? { content: "test-csrf-token" } : null,
};
const { api, requestKey } = await import("../../app/static/js/common.js");
after(() => {
  if (originalDocument === undefined) delete globalThis.document;
  else globalThis.document = originalDocument;
});

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("GET returns parsed objects and keeps same-origin credentials", async (t) => {
  t.mock.method(globalThis, "fetch", async (path, options) => {
    assert.equal(path, "/api/test");
    assert.equal(options.method, "GET");
    assert.equal(options.credentials, "same-origin");
    assert.equal(options.headers.Accept, "application/json");
    assert.ok(options.signal instanceof AbortSignal);
    return jsonResponse({ calories: 2310 });
  });
  assert.deepEqual(await api("/api/test"), { calories: 2310 });
});

test("POST retains JSON serialization and CSRF protection", async (t) => {
  t.mock.method(globalThis, "fetch", async (path, options) => {
    assert.equal(path, "/api/test");
    assert.equal(options.method, "POST");
    assert.equal(options.headers["X-CSRFToken"], "test-csrf-token");
    assert.equal(options.headers["Content-Type"], "application/json");
    assert.deepEqual(JSON.parse(options.body), { weight: 70 });
    return jsonResponse({ message: "Saved" });
  });
  assert.deepEqual(await api("/api/test", { method: "POST", body: { weight: 70 } }), {
    message: "Saved",
  });
});

test("structured API errors preserve useful server feedback", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    jsonResponse({ message: "Weight must be valid" }, 400),
  );
  await assert.rejects(api("/api/test"), { message: "Weight must be valid" });
});

test("HTML upstream failures produce readable feedback", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response("<html>private proxy diagnostic</html>", { status: 502 }),
  );
  await assert.rejects(api("/api/test"), {
    message: "The server returned an unreadable response. Try again.",
  });
});

for (const body of [null, [], "unexpected text", 42]) {
  test(`unexpected JSON shape (${JSON.stringify(body)}) produces readable feedback`, async (t) => {
    t.mock.method(globalThis, "fetch", async () => jsonResponse(body));
    await assert.rejects(api("/api/test"), {
      message: "The server returned an unreadable response. Try again.",
    });
  });
}

test("non-string error messages use a safe fallback", async (t) => {
  t.mock.method(globalThis, "fetch", async () =>
    jsonResponse({ message: { internal: "diagnostic" } }, 500),
  );
  await assert.rejects(api("/api/test"), { message: "The request could not be completed." });
});

for (const message of ["", "   ", "\t\n"]) {
  test(`blank error feedback ${JSON.stringify(message)} retains an actionable fallback`, async (t) => {
    t.mock.method(globalThis, "fetch", async () => jsonResponse({ message }, 503));
    await assert.rejects(api("/api/test"), { message: "The request could not be completed." });
  });
}

test("fetch connection failures keep actionable feedback", async (t) => {
  t.mock.method(globalThis, "fetch", async () => {
    throw new TypeError("private network diagnostic");
  });
  await assert.rejects(api("/api/test"), {
    message: "Connection failed. Check your connection and try again.",
  });
});

test("body-read aborts retain timeout feedback", async (t) => {
  t.mock.method(globalThis, "fetch", async () => ({
    ok: true,
    json: async () => {
      throw new DOMException("aborted", "AbortError");
    },
  }));
  await assert.rejects(api("/api/test"), { message: "The request timed out. Try again." });
});

test('CSV requests retain authentication and validate the download content type', async (t) => {
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(options.headers.Accept, 'text/csv');
    assert.equal(options.credentials, 'same-origin');
    return new Response('date_utc,weight_kg,calories_kcal\r\n', {
      headers: { 'Content-Type': 'text/csv; charset=utf-8' },
    });
  });
  const blob = await api('/api/tracker/export.csv', { responseFormat: 'csv' });
  assert.equal(await blob.text(), 'date_utc,weight_kg,calories_kcal\r\n');
});

test('CSV failures keep useful JSON validation feedback', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => jsonResponse({ message: 'Narrow the date range.' }, 400));
  await assert.rejects(api('/api/tracker/export.csv', { responseFormat: 'csv' }), {
    message: 'Narrow the date range.',
  });
});

test('CSV downloads reject a successful response with the wrong content type', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => jsonResponse({ message: 'Not a CSV file' }));
  await assert.rejects(api('/api/tracker/export.csv', { responseFormat: 'csv' }), {
    message: 'The server returned an unreadable response. Try again.',
  });
});

test('request identities use native UUID generation when available', () => {
  const expected = '12345678-1234-4234-8234-123456789abc';
  assert.equal(requestKey({ randomUUID: () => expected }), expected);
});

test('request identity fallback retains canonical UUID version and variant bits', () => {
  const key = requestKey({ getRandomValues: (bytes) => bytes.fill(0) });
  assert.equal(key, '00000000-0000-4000-8000-000000000000');
});
