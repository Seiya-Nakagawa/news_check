# CLAUDE.md

このファイルは、本リポジトリ固有の事情を記録したものです。

基本方針・機密情報の取り扱い・Git 運用・コーディング規約・Markdown 記法などの共通規約は
グローバル規約（`~/.claude/CLAUDE.md`、`~/.gemini/GEMINI.md`、`~/.claude/rules/`）に従います。
**本ファイルに共通規約を重複定義しないこと。**

## 1. プロジェクト概要

OCI（Oracle Cloud Infrastructure）上の Compute インスタンスを Ansible で構成管理するリポジトリ。
インスタンスそのものの構築は `infra-oci-terraform` リポジトリが担う。

| ディレクトリ | 内容 |
| ------------ | ---- |
| `ansible/` | Playbook（`site.yml`）、インベントリ（`hosts.yml`）、`group_vars/`、`roles/` |
| `scripts/` | Bastion セッション管理と SSH 接続の補助スクリプト |
| `docs/` | 要件定義書・設計書・構築手順書 |
| `04_保守・運用/` | 運用作業の記録 |

`ansible/site.yml` は `os` → `kubernetes` → `mysql` の順に 3 つのロールを適用する。
ロール単位で流す場合は同名のタグ（`--tags os` など）を使用する。

## 2. Ansible の実行

対象ホストへは OCI Bastion 経由で接続するため、`ansible-playbook` を直接実行せず
`./scripts/run_ansible.sh` を使用する。

| コマンド | 内容 |
| -------- | ---- |
| `./scripts/run_ansible.sh [ansible-playbook のオプション]` | Bastion セッション（TTL 3 時間）を作成・再利用したうえで `ansible-playbook` を実行する。引数はそのまま `ansible-playbook` へ渡る |
| `./scripts/bastion_ssh.sh` | Bastion 経由で対象ホストへ SSH 接続する |
| `./scripts/ssh_connect.sh` | パブリック IP で直接 SSH 接続する |

`run_ansible.sh` は接続情報を Terraform の出力から取得するため、
`infra-oci-terraform` の `terraform/` ディレクトリを以下の順に探索する。

1. 本リポジトリ直下の `terraform/`
2. 同階層の `../infra-oci-terraform/terraform/`
3. `~/git/infra-oci-terraform/terraform/`

本番環境への変更を伴う実行は、事前に `--check`（ドライラン）で影響範囲を確認する。

## 3. サーバー作業

対象ホストへの SSH 操作および証跡の記録は `~/.claude/rules/ssh-operations.md` に従う。
証跡ログは `04_保守・運用/` 配下へ保存する。
