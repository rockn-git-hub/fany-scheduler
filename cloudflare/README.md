# 公演通知の時刻管理

Cloudflare WorkersからGitHub Actionsの`fany_schedule.yml`を起動する構成
公演取得とLINE送信は既存のGitHub Actionsで実行
水飲み通知は移行対象外

## 配信時刻

- 起動予定: 毎日、日本時間8:27・20:27
- LINE送信の目標: 8:30・20:30前後
- 有効化するUTC cron: `27 23 * * *`、`27 11 * * *`
- GitHub側の待ち時間と処理時間による配信時刻の変動あり

## 初期設定と切り替え

1. GitHubのfine-grained personal access tokenを作成
   対象を`rockn-git-hub/fany-scheduler`だけに限定し、ActionsのRead and write権限を付与
2. Cloudflareの`fany-scheduler-trigger`のSecretsへ`GITHUB_TOKEN`として登録
   トークンをソースコードやチャットへ貼り付けない
3. 手動確認用のランダムな秘密鍵を`TRIGGER_SECRET`として登録
4. `/dispatch`へAuthorizationヘッダー付きPOSTを1回送り、ActionsとLINE送信を確認
5. `wrangler.jsonc`の`triggers.crons`を上記2時刻に変更して公開
6. GitHub側の`fany_schedule.yml`から`on.schedule`を削除し、mainへ反映
7. GitHub側に既に作成された定期実行が残っていないか確認

公開例: `wrangler deploy --config cloudflare/wrangler.jsonc`
テスト: `node --test cloudflare/worker.test.mjs`
初期公開ではcronを空にし、移行完了までGitHub側の定期実行を維持
Cloudflareのcron設定変更は反映まで最大15分かかる場合あり

## ログの確認

- Cloudflare: WorkerのLogsで`scheduled_start`と`dispatch_accepted`を確認
- GitHub Actions: 実行開始時刻と`[TIME] before line send`を確認
- `dispatch_accepted`は起動要求の受付であり、公演取得やLINE送信の完了ではない
- `GITHUB_TOKEN`の期限切れでは起動できないため、期限前にSecretを更新
- 起動要求の自動再送は行わない構成

## 公式資料

- [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
- [GitHubのワークフロー起動API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
