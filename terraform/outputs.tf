output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.logistics_api.id
}

output "public_ip" {
  description = "Public IPv4 address of the EC2 instance"
  value       = var.enable_elastic_ip ? aws_eip.logistics_eip[0].public_ip : aws_instance.logistics_api.public_ip
}

output "public_dns" {
  description = "Public DNS hostname of the EC2 instance"
  value       = aws_instance.logistics_api.public_dns
}

output "api_http_url" {
  description = "Public Base HTTP URL for the deployed API via Nginx"
  value       = "http://${var.enable_elastic_ip ? aws_eip.logistics_eip[0].public_ip : aws_instance.logistics_api.public_ip}"
}

output "health_url" {
  description = "Public Health Endpoint URL"
  value       = "http://${var.enable_elastic_ip ? aws_eip.logistics_eip[0].public_ip : aws_instance.logistics_api.public_ip}/health"
}

output "docs_url" {
  description = "Public OpenAPI / Swagger Documentation URL"
  value       = "http://${var.enable_elastic_ip ? aws_eip.logistics_eip[0].public_ip : aws_instance.logistics_api.public_ip}/docs"
}
