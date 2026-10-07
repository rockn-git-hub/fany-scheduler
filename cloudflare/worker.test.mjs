import assert from "node:assert/strict";
import { test } from "node:test";
import worker, { dispatchWorkflow } from "./worker.mjs";

test("dispatch targets only the FANY workflow on main", async () => {
  let called = false;
  await dispatchWorkflow({ GITHUB_TOKEN: "test-token" }, async (url, options) => {
    called = true;
    assert.equal(url, "https://api.github.com/repos/rockn-git-hub/fany-scheduler/actions/workflows/fany_schedule.yml/dispatches");
    assert.equal(options.method, "POST");
    assert.equal(options.headers.Authorization, "Bearer test-token");
    assert.deepEqual(JSON.parse(options.body), { ref: "main" });
    return new Response(null, { status: 204 });
  });
  assert.equal(called, true);
});

test("missing token does not dispatch", async () => {
  await assert.rejects(dispatchWorkflow({}, () => assert.fail("unexpected request")), /not configured/);
});

test("GitHub rejection is reported without exposing credentials", async () => {
  await assert.rejects(
    dispatchWorkflow({ GITHUB_TOKEN: "secret-value" }, async () => new Response(null, { status: 403 })),
    { message: "GitHub dispatch failed: HTTP 403" },
  );
});

test("network failure does not retry a potentially accepted dispatch", async () => {
  let requests = 0;
  await assert.rejects(dispatchWorkflow({ GITHUB_TOKEN: "test-token" }, async () => {
    requests += 1;
    throw new Error("network failure");
  }), /network failure/);
  assert.equal(requests, 1);
});

test("manual endpoint rejects unauthenticated requests", async () => {
  const response = await worker.fetch(new Request("https://example.com/dispatch", { method: "POST" }), {});
  assert.equal(response.status, 401);
});

test("other paths and methods cannot dispatch", async () => {
  const response = await worker.fetch(new Request("https://example.com/dispatch"), { TRIGGER_SECRET: "test-secret" });
  assert.equal(response.status, 404);
});

test("scheduled handler dispatches the configured workflow", async (context) => {
  let requests = 0;
  context.mock.method(globalThis, "fetch", async () => {
    requests += 1;
    return new Response(null, { status: 204 });
  });
  await worker.scheduled({ scheduledTime: Date.UTC(2026, 9, 7, 23, 27) }, { GITHUB_TOKEN: "test-token" });
  assert.equal(requests, 1);
});

test("authenticated manual dispatch returns acceptance", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response(null, { status: 204 }));
  const response = await worker.fetch(new Request("https://example.com/dispatch", {
    method: "POST",
    headers: { Authorization: "Bearer test-secret" },
  }), { TRIGGER_SECRET: "test-secret", GITHUB_TOKEN: "test-token" });
  assert.equal(response.status, 202);
  assert.deepEqual(await response.json(), { accepted: true });
});
