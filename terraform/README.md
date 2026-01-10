# Terraform - OCI Infrastructure

このディレクトリには、News CheckアプリケーションをOracle Cloud Infrastructure (OCI) にデプロイするためのTerraformコードが含まれています。

## 📋 構成内容

- **Compute Instance**: VM.Standard.A1.Flex (ARM64, 4 OCPU, 24GB RAM) - Always Free枠
- **OS**: Ubuntu 24.04 LTS (ARM64)
- **Storage**: 200GB Boot Volume
- **Network**:
  - VCN (Virtual Cloud Network)
  - Public Subnet
  - Internet Gateway
  - Security List (ファイアウォールルール)

## 🚀 推奨: Terraform Cloud を使用する（VCS-driven workflow）

**このプロジェクトでは、Terraform CloudとGitHubの連携を推奨しています。**

詳細なセットアップ手順は **[TERRAFORM_CLOUD_SETUP.md](./TERRAFORM_CLOUD_SETUP.md)** を参照してください。

### メリット

✅ **セキュアな認証情報管理**: 秘密鍵などの機密情報をローカルに保存する必要がない
✅ **自動デプロイ**: GitHubにプッシュするだけで自動的にPlan/Applyが実行される
✅ **チーム開発**: Stateの共有とロックが自動管理される
✅ **監査ログ**: すべての変更履歴が記録される
✅ **無料枠**: 個人利用は無料

---

## 💻 (参考) ローカルでの実行方法

以下は、Terraform Cloudを使わずにローカルで実行する場合の手順です。

### 1. 前提条件

- [Terraform](https://www.terraform.io/downloads) がインストールされていること (>= 1.0.0)
- OCIアカウントとAPI認証情報が設定済みであること
- SSH鍵ペアが生成済みであること

### 2. OCI API認証情報の準備

#### 2.1. API鍵の生成

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

#### 2.2. OCIコンソールでAPI鍵を登録

1. OCI Console にログイン
2. 右上のプロファイルアイコン → **User Settings**
3. 左メニューの **API Keys** → **Add API Key**
4. `~/.oci/oci_api_key_public.pem` の内容を貼り付け
5. Fingerprintをメモ

#### 2.3. 必要なOCIDの取得

- **Tenancy OCID**: OCI Console右上のプロファイル → Tenancy: [名前] → OCID をコピー
- **User OCID**: OCI Console右上のプロファイル → User Settings → OCID をコピー
- **Compartment OCID**: Identity → Compartments → 使用するCompartment → OCID をコピー

### 3. 変数ファイルの作成

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` を編集して、実際の値を設定してください：

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaaaa..."
user_ocid        = "ocid1.user.oc1..aaaaaaaa..."
fingerprint      = "aa:bb:cc:dd:..."
private_key      = <<-EOT
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(秘密鍵の内容)
-----END RSA PRIVATE KEY-----
EOT
region           = "ap-tokyo-1"
compartment_ocid = "ocid1.compartment.oc1..aaaaaaaa..."
ssh_public_key   = "ssh-rsa AAAAB3NzaC1yc2E..."
```

### 4. Terraform実行

```bash
# 初期化
terraform init

# 実行計画の確認
terraform plan

# リソースの作成
terraform apply

# 確認プロンプトで "yes" を入力
```

### 5. 出力の確認

```bash
# 作成されたリソースの情報を表示
terraform output

# SSH接続
terraform output -raw ssh_connection_command
# 出力例: ssh ubuntu@xxx.xxx.xxx.xxx
```

## 🔧 Terraform Cloud を使用する場合

### 1. `versions.tf` の編集

```hcl
terraform {
  cloud {
    organization = "your-organization-name"
    workspaces {
      name = "news-check-production"
    }
  }
  # ...
}
```

### 2. Terraform Cloud で変数を設定

Workspace の **Variables** セクションで以下を設定：

**Terraform Variables**:
- `tenancy_ocid` (Sensitive: ✓)
- `user_ocid` (Sensitive: ✓)
- `fingerprint` (Sensitive: ✓)
- `private_key_path` → Terraform Cloudでは使えないため、代わりに `private_key` として秘密鍵の内容を設定
- `region`
- `compartment_ocid`
- `ssh_public_key` (Sensitive: ✓)

**注意**: Terraform Cloudを使用する場合、`private_key_path` の代わりに `private_key` 変数を使用するように `variables.tf` と `versions.tf` の修正が必要です。

### 3. VCS連携

GitHubリポジトリと連携して、プッシュ時に自動で `terraform plan` と `terraform apply` を実行できます。

## 🔐 セキュリティ

- **機密情報の管理**: `terraform.tfvars` は `.gitignore` に含まれており、Gitにコミットされません
- **SSH制限**: 本番環境では `allowed_ssh_cidr` を自分のIPアドレスに制限することを推奨
- **API鍵の管理**: 秘密鍵ファイルは適切なパーミッション (600) で保護してください

## 📝 リソースの削除

```bash
terraform destroy

# 確認プロンプトで "yes" を入力
```

## 🔍 トラブルシューティング

### エラー: "Service error:NotAuthorizedOrNotFound"

- Compartment OCIDが正しいか確認
- ユーザーに適切な権限が付与されているか確認

### エラー: "Out of host capacity"

- 別のAvailability Domainを試す
- 別のリージョンを試す
- 時間を空けて再試行

### インスタンスにSSH接続できない

- Security Listのルールを確認
- SSH公開鍵が正しく設定されているか確認
- インスタンスの起動が完了しているか確認 (cloud-initの実行完了まで数分かかる場合があります)

## 📚 参考リンク

- [OCI Provider Documentation](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [OCI Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
