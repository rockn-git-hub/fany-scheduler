# Windows常駐ランナーの導入と移行

Cloudflareが定時にGitHub Actionsを起動し、指定したWindows PCで公演情報を取得する構成
取得後はHTMLと前回データをリポジトリへ保存し、GitHub Pagesで公開、LINEへ一覧URLを送信
水飲み通知はGitHubのクラウド環境で実行

## 前提

- Windows x64、実行時に起動・インターネット接続されているPC
- 管理者権限、Git、GitHub CLI、Python 3.11、全ユーザー向けChrome
- このPCのChromeからFANYの検索・詳細ページへアクセスできること
- GitHub CLIで私用アカウント`rockn-git-hub`にログイン済みであること
- スリープ中は実行できないため、電源・スリープ設定を運用に合わせて確認

ランナーは外部へ接続して実行要求を待つため、外部からPCへのポート開放は不要
ランナー登録情報はインストール先に保存し、Gitには保存しない
LINEトークンはGitHub Secretsの既存設定を利用

## 導入

リポジトリを`C:\Codex\Git\Private\fany-scheduler`へ取得し、管理者PowerShellで実行
すでに存在するリポジトリは再cloneせず、未コミット変更を確認してから更新

```powershell
gh auth status
python --version
& C:\Codex\Git\Private\fany-scheduler\scripts\Install-FanyRunner.ps1 `
  -RunnerDirectory C:\Codex\Runners\fany `
  -RunnerName fany-always-on `
  -RunnerLabel fany-windows `
  -PythonExecutable (Get-Command python.exe).Source
```

公式GitHubランナーを取得し、公開チェックサムを確認して展開
指定Pythonのインストールディレクトリをランナー配下へコピーし、サービスから利用
サービスアカウントは`NT AUTHORITY\NETWORK SERVICE`、起動種類は自動
Pythonの依存ライブラリは最初のジョブで専用の仮想環境へインストール
ChromeとGitはサービスから利用できる全ユーザー向けインストールを使用
ワークフローのPowerShellプロセスだけに`RemoteSigned`を指定し、PC全体の実行ポリシーは変更しない構成
インストール先に既存フォルダーがある場合は停止し、上書きしない構成

## 動作確認

以下は実際に公演取得、HTML公開、LINE通知を行うため、通知が1通届くことを確認して実行

```powershell
gh workflow run fany_schedule.yml --repo rockn-git-hub/fany-scheduler --ref main -f runner_label=fany-windows
gh run list --repo rockn-git-hub/fany-scheduler --workflow fany_schedule.yml --limit 3
```

検証用ラベルが`fany-windows-test`の場合は`runner_label`も同じ値に変更
テスト中も公演更新ジョブは共通のconcurrencyグループで直列実行
main以外のブランチから本ワークフローのジョブは実行しない構成

## 定期実行先の切り替え

移行先PCでの成功確認後、GitHubのリポジトリ変数`FANY_RUNNER_LABEL`を設定

```powershell
gh variable set FANY_RUNNER_LABEL --repo rockn-git-hub/fany-scheduler --body fany-windows
```

Cloudflareの時刻設定は変更不要
公演通知は毎日日本時間8:27・20:27に起動し、処理完了後に送信
変数が未設定の場合は既存のUbuntu環境、手動入力がある場合はそのラベルを優先
Ubuntu環境はFANYから403で拒否された実績があり、復旧先ではなく未切り替え状態

同じ本番ラベルを複数PCに付けると、どちらで実行されるか固定されない
検証用PCを停止し、常時稼働PCだけに本番ラベルを付けて切り替えること

## サービス管理

状態確認以外は管理者PowerShellで実行

```powershell
$script = 'C:\Codex\Git\Private\fany-scheduler\scripts\Manage-FanyRunner.ps1'
& $script -RunnerDirectory C:\Codex\Runners\fany -Action Status
& $script -RunnerDirectory C:\Codex\Runners\fany -Action Restart
& $script -RunnerDirectory C:\Codex\Runners\fany -Action Stop
& $script -RunnerDirectory C:\Codex\Runners\fany -Action Start
```

ランナー本体の診断ログはインストール先の`_diag`、ジョブのログはGitHub Actionsで確認
サービスの起動アカウント、起動種類はWindowsのサービス管理画面でも確認可能
自動起動設定の確認と、実際のPC再起動後の確認は別の検証

## 登録解除

ジョブ実行中でないことを確認して、サービス停止とGitHub登録解除を実行
フォルダーとログは削除せず保持

```powershell
& C:\Codex\Git\Private\fany-scheduler\scripts\Manage-FanyRunner.ps1 `
  -RunnerDirectory C:\Codex\Runners\fany -Action Remove
```

## 公開リポジトリでの運用

ランナーはリポジトリ内のコードをPCで実行するため、ワークフロー変更を確認してから反映
現在の起動イベントは`workflow_dispatch`のみで、pull_requestから自動実行しない構成
管理者アカウントの常用、個人用認証情報のランナーへの追加は不要
診断・試験用ブランチのワークフローも含め、任意コードを実行可能なためGitHub書き込み権限を管理

## 公式資料

- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application
