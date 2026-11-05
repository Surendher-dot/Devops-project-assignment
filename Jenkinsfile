
pipeline {
    agent {
        label 'aws-ec2'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION = 'us-east-1'
        AWS_ACCOUNT_ID = '762052017474'
        ECR_REGISTRY = '762052017474.dkr.ecr.us-east-1.amazonaws.com'

        COMPOSE_PROJECT_NAME = 'devops-project-assignment'
        DEPLOY_DIR = '/home/ec2-user/Devops-project-assignment'
        IMAGE_TAG = "build-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Project') {
            steps {
                sh '''
                    set -eu

                    echo "Running as:"
                    whoami

                    aws sts get-caller-identity

                    docker info >/dev/null
                    docker-compose --version

                    test -f user-service/app.py
                    test -f product-service/app.py
                    test -f order-service/app.py
                    test -f docker-compose.yml
                    test -f monitoring/prometheus.yml

                    python3 -m py_compile \
                        user-service/app.py \
                        product-service/app.py \
                        order-service/app.py

                    docker-compose config -q

                    echo "Project validation successful"
                '''
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                sh '''
                    set -eu

                    aws ecr get-login-password \
                        --region "$AWS_REGION" \
                    | docker login \
                        --username AWS \
                        --password-stdin "$ECR_REGISTRY"
                '''
            }
        }

        stage('Build and Push Docker Images') {
            steps {
                sh '''
                    set -eu

                    for service in user-service product-service order-service
                    do
                        echo "Building $service with tag $IMAGE_TAG"

                        docker build \
                            -t "$ECR_REGISTRY/$service:$IMAGE_TAG" \
                            "./$service"

                        docker push "$ECR_REGISTRY/$service:$IMAGE_TAG"
                    done

                    echo "All images pushed successfully"
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                    set -eu

                    cd "$DEPLOY_DIR"

                    echo "Deploying image tag: $IMAGE_TAG"

                    docker-compose pull \
                        user-service \
                        product-service \
                        order-service

                    docker-compose up -d --no-deps \
                        user-service \
                        product-service \
                        order-service

                    echo "Waiting for application health checks..."

                    for service in user-service product-service order-service
                    do
                        container_id="$(docker-compose ps -q "$service")"

                        if [ -z "$container_id" ]; then
                            echo "ERROR: $service container not found"
                            exit 1
                        fi

                        status=""

                        for attempt in $(seq 1 30)
                        do
                            status="$(docker inspect \
                                --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
                                "$container_id")"

                            echo "$service: $status"

                            if [ "$status" = "healthy" ]; then
                                break
                            fi

                            if [ "$status" = "unhealthy" ] || [ "$status" = "exited" ]; then
                                docker logs "$container_id"
                                exit 1
                            fi

                            sleep 5
                        done

                        if [ "$status" != "healthy" ]; then
                            echo "ERROR: $service did not become healthy"
                            docker logs "$container_id"
                            exit 1
                        fi
                    done

                    echo "All microservices are healthy"
                '''
            }
        }

        stage('Smoke Tests') {
            steps {
                sh '''
                    set -eu

                    echo "Testing API Gateway..."

                    curl -fsS http://localhost/health
                    curl -fsS http://localhost/api/users
                    curl -fsS http://localhost/api/products
                    curl -fsS http://localhost/api/orders

                    echo "Testing Prometheus..."

                    curl -fsS http://localhost:9090/-/healthy

                    echo "All smoke tests passed"
                '''
            }
        }
    }

    post {
        always {
            sh 'cd /home/ec2-user/Devops-project-assignment && docker-compose ps || true'
        }

        success {
            echo "CI/CD SUCCESSFUL: ${IMAGE_TAG} deployed and verified."
        }

        failure {
            echo 'CI/CD FAILED. Check the stage logs and service health.'
        }
    }
}
