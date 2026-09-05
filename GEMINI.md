# GEMINI.md

このファイルは、本リポジトリ固有の事情を記録したものです。

基本方針・機密情報の取り扱い・Git 運用・コーディング規約・Markdown 記法などの共通規約は
グローバル規約（`~/.claude/CLAUDE.md`、`~/.gemini/GEMINI.md`、`~/.claude/rules/`）に従います。
**本ファイルに共通規約を重複定義しないこと。**

## 1. プロジェクト概要

OCI（Oracle Cloud Infrastructure）上の個人開発基盤を、インフラのプロビジョニング（Terraform）から
サーバの構成管理（Ansible）まで一元管理するリポジトリ。

| ディレクトリ | 内容 |
| ------------ | ---- |
| `terraform/` | Terraform 構成ファイル一式（`main.tf`、`network.tf`、`compute.tf` など） |
| `ansible/` | Playbook（`site.yml`）、インベントリ（`hosts.yml`）、`group_vars/`、`roles/` |
| `scripts/` | plan / apply / Ansible 実行 / SSH 接続の補助スクリプト |
| `docs/` | 要件定義書・設計書・構築手順書・運用証跡 |

インフラのライフサイクルは `terraform/` でインスタンスを作成 → `ansible/` で OS・ミドルウェアを
構成する、という 2 段構成になっている。`ansible/site.yml` は `os` → `kubernetes` → `mysql` の順に
3 つのロールを適用する。ロール単位で流す場合は同名のタグ（`--tags os` など）を使用する。

Terraform Cloud（CLI-driven workflow）をリモートバックエンドとして利用し、
ローカルから `terraform` コマンドで操作・実行する。
セットアップ手順は [TERRAFORM_CLOUD_SETUP.md](TERRAFORM_CLOUD_SETUP.md) を参照する。

## 2. Terraform 操作

補助スクリプトはリポジトリルートから実行する（内部で `terraform/` へ移動する）。

| コマンド | 内容 |
| -------- | ---- |
| `./scripts/plan_tf.sh` | `terraform fmt` → `init` → `plan` を実行し、実行計画を `terraform/tfplan` に保存する |
| `./scripts/apply_tf.sh` | `terraform/tfplan` を適用する。計画ファイルが無い場合は中断する |

- **`apply` はユーザーが実施する。** AI は `plan` までを実行し、変更内容を提示して判断を仰ぐ
- コード修正後は `terraform fmt -check` および `terraform validate` で構文と構成の妥当性を確認する

## 3. Ansible 操作

| コマンド | 内容 |
| -------- | ---- |
| `./scripts/run_ansible.sh [ansible-playbook のオプション]` | `terraform output` から接続先を解決したうえで `ansible-playbook` を実行する。引数はそのまま `ansible-playbook` へ渡る |
| `./scripts/ssh_connect.sh` | 作成した Compute インスタンスへパブリック IP で SSH 接続する（`-i` で秘密鍵を指定） |

- 本番環境への変更を伴う実行は、事前に `--check`（ドライラン）で影響範囲を確認する
- 対象ホストへは OCI Bastion を経由せず、許可された IP からパブリック IP へ直接 SSH 接続する
- MySQL のパスワード等の機密情報は Ansible Vault で暗号化し、Vault パスワードは
  `ansible/.vault_password`（Git 管理外）に置く。`ansible/ansible.cfg` の
  `vault_password_file` で参照するため、実行時にオプションを指定する必要はない

## 4. サーバー作業

対象ホストへの SSH 操作および証跡の記録は `~/.claude/rules/ssh-operations.md` に従う。
証跡ログは `docs/04.保守・運用/` 配下へ保存する。

## 5. 機密情報

グローバル規約の一般方針に加え、本リポジトリでは以下を守る。

- `*.tfvars`、`*.pem`、`ansible/.vault_password` など機密情報を含むファイルは絶対にコミットしない
  （テンプレートは `terraform/terraform.tfvars.example` を使用する）
- 認証情報は環境変数、または Terraform Cloud の Variable（Sensitive）として管理する
- セキュリティ・リストや IAM ポリシーの変更時は、必要最小限の権限付与にとどめる

## 6. 命名規則

リソース名はケバブケース（`kebab-case`）またはスネークケース（`snake_case`）で一貫性を持たせる。

## 7. 作業の流れ

1. `docs/` 配下のドキュメント（要件定義書・設計書・構築手順書）を必要に応じて更新する
   （`~/.claude/rules/docs-sync.md`）
2. `./scripts/plan_tf.sh` で実行計画を確認し、ユーザーの判断のもとインフラへ反映する
3. Ansible の変更は `./scripts/run_ansible.sh --check` で影響範囲を確認してから適用する
4. Git 操作は `~/.claude/rules/git-workflow.md` に従う（Issue → 作業ブランチ → PR）。
   インフラ構成の変更は影響範囲が大きいため、コミット本文に「何を変更し、なぜ変更したか」を明記する
