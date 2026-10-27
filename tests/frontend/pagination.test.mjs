import assert from "node:assert/strict";
import { setImmediate } from "node:timers/promises";
import { test } from "node:test";

class Element {
  listeners = {};
  disabled = false;
  value = "";
  textContent = "";
  children = [];
  addEventListener(event, callback) {
    this.listeners[event] = callback;
  }
  setAttribute() {}
  querySelectorAll() {
    return [];
  }
  reset() {}
  append(...children) {
    this.children.push(...children);
  }
  replaceChildren(...children) {
    this.children = children;
  }
}

const views = [
  {
    module: "tracking",
    previous: "#previous-page",
    next: "#next-page",
    label: "#page-label",
    rows: "#history-rows",
    feedback: "#history-status",
    retry: "#retry-history",
  },
  {
    module: "admin",
    previous: "#admin-previous",
    next: "#admin-next",
    label: "#admin-page",
    rows: "#users-rows",
    feedback: "#admin-status",
    retry: "#retry-users",
  },
];

let sequence = 0;
async function setup(t, view) {
  const nodes = new Map();
  function element(selector) {
    if (!nodes.has(selector)) nodes.set(selector, new Element());
    return nodes.get(selector);
  }
  element("#tracking-form").elements = {
    weight: element("#record-weight"),
    calories: element("#record-calories"),
  };
  const originalDocument = globalThis.document;
  const originalWindow = globalThis.window;
  globalThis.window = { addEventListener() {}, removeEventListener() {} };
  t.after(() => {
    if (originalDocument === undefined) delete globalThis.document;
    else globalThis.document = originalDocument;
    if (originalWindow === undefined) delete globalThis.window;
    else globalThis.window = originalWindow;
  });
  globalThis.document = {
    addEventListener() {},
    querySelector: (selector) => (selector === "#logout" ? null : element(selector)),
    createElement: () => new Element(),
    createTextNode: (value) => value,
  };
  const requests = [];
  let fail = false;
  let empty = false;
  t.mock.method(globalThis, "fetch", async (path, options) => {
    if (options.method !== "GET") {
      const submitted = JSON.parse(options.body);
      return new Response(JSON.stringify({ message: "Saved", record: {
        id: 99, date: submitted.date, weight: Number(submitted.weight), calories: Number(submitted.calories),
      } }));
    }
    const page = Number(new URL(path, "https://example.test").searchParams.get("page"));
    requests.push(page);
    if (fail) {
      fail = false;
      throw new TypeError("offline");
    }
    const record = { id: page, date: "2026-01-01", weight: 70, calories: 2000 };
    const records = empty ? [] : [record];
    empty = false;
    return new Response(
      JSON.stringify({
        page,
        pages: 3,
        total: 45,
        records,
        users: [{ id: page, email: `person${page}@example.test`, verified: true }],
      }),
      { headers: { "Content-Type": "application/json" } },
    );
  });
  await import(`../../app/static/js/${view.module}.js?pagination=${sequence++}`);
  await setImmediate();
  return {
    element,
    requests,
    failNext: () => {
      fail = true;
    },
    emptyNext: () => {
      empty = true;
    },
    click: async (selector) => {
      element(selector).listeners.click();
      await setImmediate();
    },
  };
}

test("tracking: an empty destination still falls back to the previous page", async (t) => {
  const view = views[0];
  const ui = await setup(t, view);
  ui.emptyNext();
  await ui.click(view.next);
  assert.deepEqual(ui.requests, [1, 2, 1]);
  assert.equal(ui.element(view.label).textContent, "Page 1 of 3");
  assert.equal(ui.element(view.previous).disabled, true);
});

test("tracking: failed history refresh after saving retains the displayed page", async (t) => {
  const view = views[0];
  const ui = await setup(t, view);
  await ui.click(view.next);
  t.mock.method(globalThis, "FormData", function () {
    return new Map([
      ["date", "2026-01-01"],
      ["weight", "70"],
      ["calories", "2000"],
    ]);
  });
  ui.failNext();
  await ui.element("#tracking-form").listeners.submit({ preventDefault() {} });
  assert.equal(ui.element(view.label).textContent, "Page 2 of 3");
  assert.equal(ui.element(view.previous).disabled, false);
  await ui.click(view.previous);
  assert.deepEqual(ui.requests, [1, 2, 1, 1]);
  assert.equal(ui.element(view.label).textContent, "Page 1 of 3");
});

for (const view of views) {
  test(`${view.module}: failed next page keeps current rows and retries the same destination`, async (t) => {
    const ui = await setup(t, view);
    const rows = [...ui.element(view.rows).children];
    ui.failNext();
    await ui.click(view.next);
    assert.equal(ui.element(view.label).textContent, "Page 1 of 3");
    assert.deepEqual(ui.element(view.rows).children, rows);
    assert.equal(ui.element(view.previous).disabled, true);
    assert.equal(ui.element(view.next).disabled, false);
    assert.match(ui.element(view.feedback).textContent, /Connection failed/);
    await ui.click(view.next);
    assert.deepEqual(ui.requests, [1, 2, 2]);
    assert.equal(ui.element(view.label).textContent, "Page 2 of 3");
  });

  test(`${view.module}: failed previous page can be retried`, async (t) => {
    const ui = await setup(t, view);
    await ui.click(view.next);
    ui.failNext();
    await ui.click(view.previous);
    assert.equal(ui.element(view.label).textContent, "Page 2 of 3");
    assert.equal(ui.element(view.previous).disabled, false);
    await ui.click(view.previous);
    assert.deepEqual(ui.requests, [1, 2, 1, 1]);
    assert.equal(ui.element(view.label).textContent, "Page 1 of 3");
  });
}

for (const view of views) {
  for (const oldOutcome of ['success', 'failure']) {
    test(`${view.module}: an outdated ${oldOutcome} cannot overwrite the newest page`, async (t) => {
      const ui = await setup(t, view);
      const older = Promise.withResolvers();
      let calls = 0;
      t.mock.method(globalThis, 'fetch', async () => {
        calls += 1;
        if (calls === 1) return older.promise;
        return new Response(JSON.stringify({
          page: 2, pages: 3, total: 46,
          records: [{ id: 2, date: '2024-01-01', weight: 70, calories: 2000 }],
          users: [{ id: 2, email: 'new@example.test', verified: true }],
        }));
      });
      await ui.click(view.next);
      await ui.click(view.next);
      assert.match(ui.element(view.feedback).textContent, /46/);
      if (oldOutcome === 'failure') older.reject(new TypeError('old request failed'));
      else older.resolve(new Response(JSON.stringify({
        page: 2, pages: 3, total: 45,
        records: [{ id: 1, date: '2024-01-01', weight: 70, calories: 2000 }],
        users: [{ id: 1, email: 'old@example.test', verified: true }],
      })));
      await setImmediate();
      assert.match(ui.element(view.feedback).textContent, /46/);
      assert.equal(ui.element(view.label).textContent, 'Page 2 of 3');
    });
  }
}

for (const view of views) {
  test(`${view.module}: a collapsed dataset jumps directly to the last available page`, async (t) => {
    const ui = await setup(t, view);
    const requestedPages = [];
    t.mock.method(globalThis, 'fetch', async (path) => {
      const requested = Number(new URL(path, 'https://example.test').searchParams.get('page'));
      requestedPages.push(requested);
      const collapsed = requested === 3;
      return new Response(JSON.stringify({
        page: requested, pages: collapsed ? 1 : 3, total: collapsed ? 1 : 45,
        records: collapsed ? [] : [{ id: 1, date: '2024-01-01', weight: 70, calories: 2000 }],
        users: collapsed ? [] : [{ id: 1, email: 'person@example.test', verified: true }],
      }));
    });
    await ui.click(view.next);
    await ui.click(view.next);
    assert.deepEqual(requestedPages, [2, 3, 1]);
    assert.equal(ui.element(view.label).textContent, 'Page 1 of 3');
  });
}

for (const view of views) {
  test(`${view.module}: Retry requests the failed destination rather than the displayed page`, async (t) => {
    const ui = await setup(t, view);
    ui.failNext();
    await ui.click(view.next);
    await ui.click(view.retry);
    assert.deepEqual(ui.requests, [1, 2, 2]);
    assert.equal(ui.element(view.label).textContent, "Page 2 of 3");
  });
}
