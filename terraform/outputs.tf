# インスタンスの公開IPアドレス
output "instance_public_ip" {
  description = "Public IP address of the compute instance"
  value       = oci_core_instance.news_check_instance.public_ip
}

# インスタンスのプライベートIPアドレス
output "instance_private_ip" {
  description = "Private IP address of the compute instance"
  value       = oci_core_instance.news_check_instance.private_ip
}

# インスタンスOCID
output "instance_ocid" {
  description = "OCID of the compute instance"
  value       = oci_core_instance.news_check_instance.id
}

# VCN OCID
output "vcn_ocid" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.news_check_vcn.id
}

# Subnet OCID
output "subnet_ocid" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.news_check_public_subnet.id
}

# Cloud Shell経由の接続案内
output "cloud_shell_instruction" {
  description = "Connection instruction using Cloud Shell"
  value       = "Use OCI Cloud Shell or Console Connection to access the instance."
}

# インスタンスの状態
output "instance_state" {
  description = "Current state of the instance"
  value       = oci_core_instance.news_check_instance.state
}

# アプリケーションURL
output "application_url" {
  description = "URL to access the application"
  value       = "http://${oci_core_instance.news_check_instance.public_ip}"
}

# 使用しているOSイメージ
output "os_image_name" {
  description = "Name of the OS image used"
  value       = var.os_image_id != "" ? "Custom Image" : data.oci_core_images.ubuntu_arm64.images[0].display_name
}
