# Fetch latest Canonical Ubuntu 24.04 LTS x86_64 AMI if ami_id is not supplied
data "aws_ami" "ubuntu_2404" {
  most_recent = true
  owners      = ["099720109477"] # Canonical owner ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

locals {
  selected_ami_id = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu_2404.id
}

# EC2 Instance for 24/7 autonomous logistics perception API hosting
resource "aws_instance" "logistics_api" {
  ami                    = local.selected_ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name != "" ? var.key_name : null
  vpc_security_group_ids = [aws_security_group.logistics_api_sg.id]

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "logistics-api-root-disk-${var.environment}"
    }
  }

  user_data = templatefile("${path.module}/user-data.sh", {
    repo_url = var.repo_url
  })

  tags = {
    Name      = "logistics-object-detection-api-${var.environment}"
    Role      = "Computer-Vision-API"
    Framework = "RT-DETR-FastAPI"
  }
}

# Optional Elastic IP resource
resource "aws_eip" "logistics_eip" {
  count    = var.enable_elastic_ip ? 1 : 0
  instance = aws_instance.logistics_api.id
  domain   = "vpc"

  tags = {
    Name = "logistics-api-eip-${var.environment}"
  }
}
