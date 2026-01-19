# news_check プロジェクト規約

本ファイルは、news_check リポジトリ特有のコーディング規約およびワークフローを定めたものです。グローバルな規約（`user_global`）を補完し、本プロジェクトにおいて優先的に適用されます。

## 1. ワークフロー自動化規約（補足）

グローバルなワークフローに加え、本プロジェクトでは以下の点に注意してください。

1. **認証確認**:
   * OCI上での動作確認やデプロイを伴う場合は、必要に応じて `oci iam region-subscription list` 等で認証状態を確認してください。
2. **動作確認・検証**:
   * Docker環境の修正を行った場合は、必ず `docker compose -f docker-compose.yml -f docker-compose.dev.yml config` 等で設定の妥当性を確認してください。
   * インフラ構成に関わる変更（Container起動設定等）の場合は、ローカルでの起動確認を推奨します。
3. **デプロイ**:
   * 本番環境への反映は、PRのマージ後に GitHub Actions または Ansible を通じて行われます。

## 2. 開発環境の操作

* **コンテナ起動**:

  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
  ```

* **コンテナ停止**:

  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml down
  ```
