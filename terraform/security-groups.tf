resource "aws_security_group" "logistics_api_sg" {
  name        = "logistics-api-sg-${var.environment}"
  description = "Security group for Logistics Object Detection & Reasoning API EC2 instance."

  # SSH access (restricted to admin CIDRs specified in terraform.tfvars)
  dynamic "ingress" {
    for_each = length(var.admin_cidr_blocks) > 0 ? [1] : []
    content {
      description = "SSH access for administrator"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.admin_cidr_blocks
    }
  }

  # Public HTTP access for Nginx reverse proxy
  ingress {
    description = "HTTP traffic to Nginx reverse proxy"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Public HTTPS access reserved for future SSL reverse proxy configuration
  ingress {
    description = "HTTPS traffic reserved for future SSL reverse proxy"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # NOTE: Internal port 7860 is NOT exposed to the public internet.
  # Nginx receives public traffic on 80/443 and proxies to 127.0.0.1:7860 internally.

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "logistics-api-sg-${var.environment}"
  }
}
