# Compute Instance
resource "oci_core_instance" "news_check_instance" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = var.instance_display_name
  shape               = var.instance_shape

  # Always Free: VM.Standard.A1.Flex (ARM) - 4 OCPU, 24GB RAM
  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  # Oracle Cloud Agentの設定 (Bastion用プラグインを有効化)
  agent_config {
    is_management_disabled = false
    is_monitoring_disabled = false

    plugins_config {
      desired_state = "ENABLED"
      name          = "Bastion"
    }

    plugins_config {
      desired_state = "ENABLED"
      name          = "Compute Instance Console Connection"
    }
  }

  # OS Image (Ubuntu 24.04 ARM64)
  source_details {
    source_type             = "image"
    source_id               = var.os_image_id != "" ? var.os_image_id : data.oci_core_images.ubuntu_arm64.images[0].id
    boot_volume_size_in_gbs = 200 # Always Free: max 200GB
  }

  # Network設定
  create_vnic_details {
    subnet_id        = oci_core_subnet.news_check_public_subnet.id
    assign_public_ip = true
    display_name     = "${var.instance_display_name}-vnic"
  }

  # Cloud-init
  metadata = {
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      project_name = var.project_name
    }))
  }

  # 永続化設定
  preserve_boot_volume = false

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }

  # インスタンスの削除時にboot volumeを削除
  lifecycle {
    ignore_changes = [
      source_details[0].source_id, # OSイメージの更新を無視
    ]
  }
}
