const FANY_CRONS = new Set(["27 23 * * *", "27 11 * * *"]);
const WATER_CRONS = new Set(["0 1,2,5,6,7,8 * * 1-5"]);

/** 公演通知または水飲み通知ワークフローの起動要求 */
export async function dispatchWorkflow(env, fetcher = fetch, workflow = "fany_schedule.yml") {
  if (!["fany_schedule.yml", "water_reminder.yml"].includes(workflow)) {
    throw new Error("Unsupported workflow");
  }
  if (!env.GITHUB_TOKEN) {
    throw new Error("GITHUB_TOKEN is not configured");
  }
  const response = await fetcher(`https://api.github.com/repos/rockn-git-hub/fany-scheduler/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "fany-scheduler-cloudflare",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ ref: "main" }),
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    throw new Error(`GitHub dispatch failed: HTTP ${response.status}`);
  }
  console.log(JSON.stringify({ event: "dispatch_accepted", workflow, time: new Date().toISOString() }));
}

export default {
  /** Cloudflareの定期実行からの起動 */
  async scheduled(controller, env) {
    const workflow = FANY_CRONS.has(controller.cron) ? "fany_schedule.yml"
      : WATER_CRONS.has(controller.cron) ? "water_reminder.yml" : null;
    if (!workflow) {
      throw new Error("Unsupported cron");
    }
    console.log(JSON.stringify({
      event: "scheduled_start",
      workflow,
      scheduledTime: new Date(controller.scheduledTime).toISOString(),
      actualTime: new Date().toISOString(),
    }));
    // 起動済みか不明な通信失敗での再送による二重通知の防止
    await dispatchWorkflow(env, fetch, workflow);
  },

  /** 秘密鍵で保護した動作確認用の手動起動 */
  async fetch(request, env) {
    if (new URL(request.url).pathname !== "/dispatch" || request.method !== "POST") {
      return new Response("Not found", { status: 404 });
    }
    if (!env.TRIGGER_SECRET || request.headers.get("Authorization") !== `Bearer ${env.TRIGGER_SECRET}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    try {
      const workflow = new URL(request.url).searchParams.get("workflow") || "fany_schedule.yml";
      await dispatchWorkflow(env, fetch, workflow);
      return Response.json({ accepted: true }, { status: 202 });
    } catch {
      console.error("Manual dispatch failed; check GitHub credentials and availability");
      return Response.json({ accepted: false }, { status: 502 });
    }
  },
};
