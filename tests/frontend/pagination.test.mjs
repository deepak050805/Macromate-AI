import assert from "node:assert/strict";
import { setImmediate } from "node:timers/promises";
import { test } from "node:test";

class Element {
  listeners = {};
  disabled = false;
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
  },
  {
    module: "admin",
    previous: "#admin-previous",
    next: "#admin-next",
    label: "#admin-page",
    rows: "#users-rows",
    feedback: "#admin-status",
  },
];

let sequence = 0;
async function setup(t, view) {
  const nodes = new Map();
  function element(selector) {
    if (!nodes.has(selector)) nodes.set(selector, new Element());
    return nodes.get(selector);
  }
  const originalDocument = globalThis.document;
  t.after(() => {
    if (originalDocument === undefined) delete globalThis.document;
    else globalThis.document = originalDocument;
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
    if (options.method !== "GET") return new Response(JSON.stringify({ message: "Saved" }));
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
