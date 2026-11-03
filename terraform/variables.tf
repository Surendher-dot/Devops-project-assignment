variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}
variable "project_name" {
  description = "Resource name prefix"
  type        = string
  default     = "microservices-devops"
}
variable "instance_type" {
  description = "EC2 type; t3.small or larger recommended for the full stack"
  type        = string
  default     = "t3.small"
}
variable "key_name" {
  description = "Existing EC2 key pair name in this region"
  type        = string
}
variable "ssh_allowed_cidrs" {
  description = "SSH source CIDRs; use your public IP/32"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
variable "monitoring_allowed_cidrs" {
  description = "Prometheus/Grafana source CIDRs; use your public IP/32"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
