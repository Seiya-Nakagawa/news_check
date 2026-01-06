terraform {
  required_version = ">= 1.0.0"

  # Terraform Cloud使用時はコメント解除
  # ローカル実行時はコメントアウトのまま
  # cloud {
  #   organization = "your-organization-name" # ← 自分のOrganization名に変更してください
  #   workspaces {
  #     name = "news-check-production"
  #   }
  # }

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  # 認証情報の設定方法:
  #
  # [APIキー認証使用時]
  # Workspace の Variables セクションで以下を設定:
  # - tenancy_ocid
  # - user_ocid
  # - fingerprint
  # - private_key (Sensitive)
  # - region
  tenancy_ocid = var.tenancy_ocid
  user_ocid    = var.user_ocid
  fingerprint  = var.fingerprint
  private_key  = var.private_key
  region       = var.region
}
