# Terraform Cloud セットアップガイド

このガイドでは、Terraform Cloud をリモートバックエンドとして利用し、ローカルから `terraform` コマンドで OCI 上にインフラをデプロイする **CLI-driven workflow** の手順を説明します。

## 📋 前提条件

- GitHubアカウント
- Terraform Cloudアカウント（無料で作成可能）
- OCIアカウントとAPI認証情報

## 🚀 セットアップ手順

### 1. OCI API認証情報の準備

#### 1.1. API鍵の生成

```bash
# ディレクトリ作成
mkdir -p ~/.oci

# 秘密鍵の生成
openssl genrsa -out ~/.oci/oci_api_key.pem 2048

# 公開鍵の生成
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem

# パーミッション設定
chmod 600 ~/.oci/oci_api_key.pem
```

#### 1.2. OCIコンソールでAPI鍵を登録

1. [OCI Console](https://cloud.oracle.com/) にログイン
2. 右上のプロファイルアイコン → **User Settings**
3. 左メニューの **API Keys** → **Add API Key**
4. `~/.oci/oci_api_key_public.pem` の内容を貼り付け
5. **Fingerprint** をメモ（後で使用）

#### 1.3. 必要なOCIDの取得

以下の情報をOCI Consoleから取得してメモしておきます：

- **Tenancy OCID**: プロファイル → Tenancy → OCID
- **User OCID**: プロファイル → User Settings → OCID
- **Compartment OCID**: Identity → Compartments → 使用するCompartment → OCID
- **Fingerprint**: 上記1.2で取得

### 2. Terraform Cloud の設定

#### 2.1. Organization の作成

1. [Terraform Cloud](https://app.terraform.io/) にログイン
2. **Create Organization** をクリック
3. Organization名を入力（例: `your-organization-name`）
4. 作成完了

#### 2.2. Workspace の作成

1. **New Workspace** をクリック
2. **CLI-driven workflow** を選択
3. Workspace名を入力: `news-check-production` (※既存のWorkspaceがある場合はそれを利用し、versions.tfの記載に合わせます)
4. **Create workspace** をクリック

#### 2.3. Variables の設定

Workspaceの **Variables** タブで以下を設定します。

##### Terraform Variables

| 変数名 | 値 | Sensitive | 説明 |
| -------- | ----- | --------- | ------ |
| `tenancy_ocid` | `ocid1.tenancy.oc1..aaaaaaaa...` | ✓ | Tenancy OCID |
| `user_ocid` | `ocid1.user.oc1..aaaaaaaa...` | ✓ | User OCID |
| `fingerprint` | `aa:bb:cc:dd:ee:ff:...` | ✓ | API Key Fingerprint |
| `private_key` | `-----BEGIN RSA PRIVATE KEY-----\n...` | ✓ | 秘密鍵の内容（後述） |
| `region` | `ap-tokyo-1` | | OCI Region |
| `compartment_ocid` | `ocid1.compartment.oc1..aaaaaaaa...` | ✓ | Compartment OCID |
| `ssh_public_key` | `ssh-rsa AAAAB3NzaC1yc2E...` | ✓ | インスタンス用SSH公開鍵 |

##### `private_key` の設定方法

秘密鍵ファイルの内容をそのまま貼り付けます：

```bash
# 秘密鍵の内容を表示
cat ~/.oci/oci_api_key.pem
```

出力をコピーして、Terraform Cloudの `private_key` 変数に貼り付けます。
**必ず "Sensitive" にチェックを入れてください。**

##### (オプション) その他の変数

| 変数名 | 値 | 説明 |
| -------- | ----- | ------ |
| `project_name` | `news-check` | プロジェクト名 |
| `environment` | `production` | 環境名 |
| `instance_display_name` | `news-check-app-server` | インスタンス表示名 |
| `allowed_ssh_cidr` | `0.0.0.0/0` | SSH接続許可CIDR |

### 3. versions.tf の編集

`terraform/versions.tf` の `cloud` ブロックを自分のOrganization名に変更します：

```hcl
terraform {
  cloud {
    organization = "your-organization-name"  # ← 自分のOrganizationに変更
    workspaces {
      name = "news-check-production"
    }
  }
  # ...
}
```

### 4. ローカルからの実行 (CLI-driven)

CLI-driven workflow では、GitHubへのPushで自動適用されることはありません。手動で以下の手順を実行します。

#### 4.1. Terraform Cloud へのログイン

```bash
terraform login
```

※ブラウザが開く（またはURLが表示される）ので、Terraform Cloud のトークンを発行してターミナルに貼り付けます。

#### 4.2. 初期化

```bash
cd terraform
terraform init
```

#### 4.3. 実行計画の確認 (Plan)

```bash
terraform plan
```

※このコマンドを実行すると、Terraform Cloud 上で処理が行われ、結果がローカルのターミナルに表示されます。

#### 4.4. デプロイの実行 (Apply)

```bash
terraform apply
```

※Plan の結果が問題なければ `yes` を入力して適用します。

### 6. 出力値の確認

デプロイ完了後、**Outputs** タブで以下の情報を確認できます：

- `instance_public_ip`: インスタンスの公開IPアドレス
- `ssh_connection_command`: SSH接続コマンド
- `application_url`: アプリケーションURL

## 🔒 セキュリティのベストプラクティス

### Variable Sets の活用

複数のWorkspaceで共通の変数（OCI認証情報など）を使用する場合、**Variable Sets** を作成して一元管理できます：

1. Organization Settings → **Variable sets** → **Create variable set**
2. 名前: `oci-credentials`
3. 共通の変数（`tenancy_ocid`, `user_ocid`, `fingerprint`, `private_key`）を追加
4. **Apply to workspaces** で対象Workspaceを選択

### SSH接続の制限

本番環境では、`allowed_ssh_cidr` を自分のIPアドレスに制限することを推奨します：

```hcl
allowed_ssh_cidr = "123.456.789.0/32"  # 自分のIPアドレス
```

### State の暗号化

Terraform Cloudでは、Stateファイルは自動的に暗号化され、安全に管理されます。ローカルにStateファイルを保存する必要はありません。

## 🔄 運用フロー

### 通常の変更

1. ローカルで Terraform コードを編集
2. `terraform plan` を実行して変更内容を確認
3. `terraform apply` を実行して反映
4. 変更が完了したら、Git にコミットして Push（変更の履歴管理のため）

### 緊急時のロールバック

1. Gitの履歴から、戻したい状態のコミットをチェックアウト、またはコードを修正
2. `terraform plan` で元に戻ることを確認
3. `terraform apply` で適用

### リソースの削除

1. Workspace → **Settings** → **Destruction and Deletion**
2. **Queue destroy plan** をクリック
3. 確認して **Confirm & Apply**

## 🔍 トラブルシューティング

### エラー: "Error: Invalid provider configuration"

- Terraform Cloud Variablesの設定を確認
- `private_key` の形式が正しいか確認（改行含む）
- 全ての変数が設定されているか確認

### エラー: "Service error:NotAuthorizedOrNotFound"

- Compartment OCIDが正しいか確認
- ユーザーに適切な権限が付与されているか確認
- OCIコンソールでポリシーを確認

### Planが実行されない

- `terraform login` が正しく完了しているか確認（`~/.terraform.d/credentials.tfrc.json` の有無など）
- `versions.tf` の Organization 名と Workspace 名が正しいか確認

## 📚 参考リンク

- [Terraform Cloud Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
- [CLI-Driven Workflow](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
- [OCI Provider Documentation](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [Variable Sets](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables/managing-variables#variable-sets)
