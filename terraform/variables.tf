variable "aws_region" {
  type        = string
  description = "AWS region for deployment."
  default     = "ap-south-1"
}

variable "environment" {
  type        = string
  description = "Environment name (e.g., production, staging)."
  default     = "production"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type. Minimum t3.small recommended for RT-DETR model memory."
  default     = "t3.small"
}

variable "ami_id" {
  type        = string
  description = "Custom Ubuntu 24.04 LTS AMI ID. If empty, the latest Canonical Ubuntu 24.04 LTS AMI will be dynamically fetched."
  default     = ""
}

variable "root_volume_size" {
  type        = number
  description = "Root EBS volume size in GB."
  default     = 20
}

variable "repo_url" {
  type        = string
  description = "Git repository URL to clone on EC2 instance."
  default     = "https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git"
}

variable "admin_cidr_blocks" {
  type        = list(string)
  description = "List of IPv4 CIDR blocks allowed for SSH access. Must be set to your specific public IP (e.g., ['YOUR_PUBLIC_IP/32']) in terraform.tfvars. Default is empty [] to prevent exposing SSH to the internet by default."
  default     = []
}


variable "key_name" {
  type        = string
  description = "Existing AWS SSH Key Pair name for EC2 access. Leave empty if SSH key authentication is not needed."
  default     = ""
}

variable "enable_elastic_ip" {
  type        = bool
  description = "Whether to allocate an AWS Elastic IP (EIP) for a static public IP address. Note: Unattached EIPs incur AWS charges."
  default     = false
}
