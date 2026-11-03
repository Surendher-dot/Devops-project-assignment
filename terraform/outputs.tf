output "instance_id" {
  value = aws_instance.microservices.id
}
output "public_ip" {
  value = aws_instance.microservices.public_ip
}
output "api_gateway_url" {
  value = "http://${aws_instance.microservices.public_ip}"
}
output "prometheus_url" {
  value = "http://${aws_instance.microservices.public_ip}:9090"
}
output "grafana_url" {
  value = "http://${aws_instance.microservices.public_ip}:3000"
}
