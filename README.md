# Microservices DevOps Project

A learning project using Python Flask microservices, Docker, Docker Compose, Nginx, Jenkins, Prometheus, Grafana, and Terraform on AWS.

## Architecture

- **User Service**: create and retrieve users.
- **Product Service**: create and retrieve products.
- **Order Service**: calls User and Product services to validate an order.
- **Nginx**: reverse proxy and single API entry point.
- **Prometheus**: scrapes metrics from all three Flask services.
- **Grafana**: dashboard interface for Prometheus metrics.
- **Jenkins**: validates, builds, starts, and smoke-tests the application.
- **Terraform**: provisions an EC2 deployment host and security group.

The three application services use in-memory demo data. Their data resets when containers are recreated. No database is included in this version.

## Requirements

- Docker Engine and Docker Compose v2
- Git and curl
- For AWS: AWS CLI credentials, Terraform >= 1.5, and an existing EC2 key pair in the selected region

## Run locally

Run from the project root:

```bash
docker compose up -d --build
docker compose ps
```

Open:
- API gateway: http://localhost
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Grafana demo login is `admin` / `ChangeThisPassword123!`. Change it before sharing or exposing Grafana. You can override it by setting `GRAFANA_ADMIN_PASSWORD` before starting Compose.

## API testing

```bash
curl http://localhost/health
curl http://localhost/api/users
curl http://localhost/api/products
curl http://localhost/api/orders
```

Create a user:

```bash
curl -X POST http://localhost/api/users -H "Content-Type: application/json" -d '{"name":"Anil","email":"anil@example.com"}'
```

Create a product:

```bash
curl -X POST http://localhost/api/products -H "Content-Type: application/json" -d '{"name":"Keyboard","price":1500}'
```

Create an order (seeded user ID 1 and product ID 101):

```bash
curl -X POST http://localhost/api/orders -H "Content-Type: application/json" -d '{"user_id":1,"product_id":101,"quantity":2}'
```

Prometheus targets: http://localhost:9090/targets

## Configure Grafana

1. Sign in to Grafana.
2. Open **Connections → Data sources → Add data source**.
3. Choose **Prometheus**.
4. Set the URL to `http://prometheus:9090`.
5. Click **Save & test**.
6. Open Explore and query `flask_http_request_total`.

## Jenkins pipeline

Create a Jenkins Pipeline job and configure **Pipeline script from SCM** for this Git repository. The Jenkins agent needs Docker Engine access, Docker Compose v2, Python 3, and curl. The pipeline has five stages: Checkout, Validate Project, Build Docker Images, Start Services, and Smoke Tests. It leaves containers running after the pipeline.

## Provision AWS EC2 with Terraform

Ensure a default VPC and at least one subnet exist in the configured region. Create an EC2 key pair in that region.

From the `terraform` directory:

```bash
terraform init
terraform fmt
terraform validate
terraform plan -var="key_name=YOUR_KEY_PAIR_NAME"
terraform apply -var="key_name=YOUR_KEY_PAIR_NAME"
```

For safer access, replace the default open CIDRs with your public IP:

```bash
terraform apply   -var="key_name=YOUR_KEY_PAIR_NAME"   -var='ssh_allowed_cidrs=["YOUR_PUBLIC_IP/32"]'   -var='monitoring_allowed_cidrs=["YOUR_PUBLIC_IP/32"]'
```

Get the EC2 IP:

```bash
terraform output -raw public_ip
```

Terraform provisions only the EC2 host and security group. It does not install Docker or deploy the application. Connect to the instance, install Docker and the Compose plugin using the current Amazon Linux instructions, clone this repository, and run:

```bash
docker compose up -d --build
```

Destroy demo infrastructure when finished:

```bash
terraform destroy -var="key_name=YOUR_KEY_PAIR_NAME"
```

Review the destroy plan before confirming.

## Useful Docker commands

```bash
docker compose ps
docker compose logs -f
docker compose logs -f order-service
docker compose restart order-service
docker compose down
```

Remove containers and monitoring volumes:

```bash
docker compose down -v
```

## Production considerations

This is a demo, not a production-ready deployment. Before production use:
- Replace in-memory dictionaries with a persistent database.
- Add authentication and authorization.
- Restrict SSH, Prometheus, and Grafana access to trusted IPs or a private network.
- Set a strong Grafana password through a secret manager.
- Add HTTPS/TLS, rate limiting, structured logs, resource limits, and alerting.
- Add automated unit and integration tests.
- Regularly update and scan container images and dependencies.
Testing automatic Jenkins trigger
