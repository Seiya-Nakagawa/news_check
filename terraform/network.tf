# VCN (Virtual Cloud Network)
resource "oci_core_vcn" "news_check_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]
  display_name   = "${var.project_name}-vcn"
  dns_label      = "newscheck"

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}

# Internet Gateway
resource "oci_core_internet_gateway" "news_check_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.news_check_vcn.id
  display_name   = "${var.project_name}-igw"
  enabled        = true

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}

# Route Table
resource "oci_core_route_table" "news_check_route_table" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.news_check_vcn.id
  display_name   = "${var.project_name}-route-table"

  route_rules {
    network_entity_id = oci_core_internet_gateway.news_check_igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}

# Security List
resource "oci_core_security_list" "news_check_security_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.news_check_vcn.id
  display_name   = "${var.project_name}-security-list"

  # Egress Rules (送信ルール: すべての通信を許可)
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # Ingress Rule: SSH (22) from Bastion
  # セキュリティ向上のため、VCN内部（Bastion）からのアクセスのみを許可
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = var.vcn_cidr_block
    stateless   = false
    description = "Allow SSH access from Bastion"

    tcp_options {
      min = 22
      max = 22
    }
  }

  # Ingress Rule: HTTP (80)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow HTTP access"

    tcp_options {
      min = var.app_http_port
      max = var.app_http_port
    }
  }

  # Ingress Rule: HTTPS (443)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow HTTPS access"

    tcp_options {
      min = var.app_https_port
      max = var.app_https_port
    }
  }

  # Ingress Rule: ICMP (ping)
  ingress_security_rules {
    protocol    = "1" # ICMP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow ICMP (ping)"
  }

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}

# Public Subnet
resource "oci_core_subnet" "news_check_public_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.news_check_vcn.id
  cidr_block                 = var.subnet_cidr_block
  display_name               = "${var.project_name}-public-subnet"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.news_check_route_table.id
  security_list_ids          = [oci_core_security_list.news_check_security_list.id]
  prohibit_public_ip_on_vnic = false

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}

# OCI Bastion
resource "oci_bastion_bastion" "news_check_bastion" {
  bastion_type     = "STANDARD"
  compartment_id   = var.compartment_ocid
  target_subnet_id = oci_core_subnet.news_check_public_subnet.id
  client_cidr_block_allow_list = ["0.0.0.0/0"]
  name             = "${var.project_name}-bastion"
  max_session_ttl_in_seconds = 3600

  freeform_tags = {
    "Project"     = var.project_name
    "Environment" = var.environment
  }
}
