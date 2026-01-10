# News Check - OCI Infrastructure
#
# このプロジェクトは、News CheckアプリケーションをOracle Cloud Infrastructure (OCI) に
# デプロイするためのTerraform構成です。
#
# リソース定義は以下のファイルに分割されています:
# - data.tf:     データソース (Availability Domains, OS Images)
# - network.tf:  ネットワーク関連リソース (VCN, Subnet, Internet Gateway, Security List)
# - compute.tf:  コンピュートリソース (Compute Instance)
# - variables.tf: 変数定義
# - outputs.tf:  出力値定義
# - versions.tf: Terraformバージョンとプロバイダー設定
