terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
provider "aws" { region = var.aws_region }

data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_security_group" "microservices_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for microservices demo"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH - restrict to your IP"
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }
  ingress {
    description = "Nginx API gateway"
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Prometheus UI - restrict to your IP"
    from_port = 9090
    to_port = 9090
    protocol = "tcp"
    cidr_blocks = var.monitoring_allowed_cidrs
  }
  ingress {
    description = "Grafana UI - restrict to your IP"
    from_port = 3000
    to_port = 3000
    protocol = "tcp"
    cidr_blocks = var.monitoring_allowed_cidrs
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.project_name}-sg" }
}

resource "aws_instance" "microservices" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.microservices_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }
  tags = { Name = "${var.project_name}-ec2" }
}
