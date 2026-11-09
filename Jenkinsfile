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


        DEPLOYMENT_ATTEMPTED = 'false'
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


        stage('Capture Previous Deployment') {
            steps {
                script {
                    def capturedTag = sh(
                        returnStdout: true,
                        script: '''
                            set -eu

                            cd "$DEPLOY_DIR"

                            user_image=$(docker inspect --format='{{.Config.Image}}' user-service)
                            product_image=$(docker inspect --format='{{.Config.Image}}' product-service)
                            order_image=$(docker inspect --format='{{.Config.Image}}' order-service)

                            user_tag="${user_image##*:}"
                            product_tag="${product_image##*:}"
                            order_tag="${order_image##*:}"

                            if [ "$user_tag" != "$product_tag" ] || [ "$user_tag" != "$order_tag" ]; then
                                echo "ERROR: Services are not using the same image tag" >&2
                                exit 1
                            fi

                            case "$user_tag" in
                                build-*) ;;
                                *)
                                    echo "ERROR: Invalid previous image tag: $user_tag" >&2
                                    exit 1
                                    ;;
                            esac

                            printf '%s\n' "$user_tag"
                        '''
                    ).trim()

                    if (!capturedTag || !capturedTag.startsWith('build-')) {
                        error("Could not capture a valid previous deployment tag: ${capturedTag}")
                    }

                    env.PREVIOUS_IMAGE_TAG = capturedTag

                    echo "Captured previous deployment: ${capturedTag}"
                    echo "Rollback environment variable: ${env.PREVIOUS_IMAGE_TAG}"
                }
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

                    echo "All new images pulled successfully"
                '''

                script {
                    env.DEPLOYMENT_ATTEMPTED = 'true'
                }

                sh '''
                    set -eu

                    cd "$DEPLOY_DIR"

                    echo "Starting deployment..."

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

                    echo "Testing rollback trigger..."
                    curl -fsS http://localhost:9999/rollback-test

                    echo "All smoke tests passed"
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished.'
        }

        success {
            echo "CI/CD SUCCESSFUL: ${IMAGE_TAG} deployed and verified."
        }

        failure {
            echo 'CI/CD FAILED. Starting automatic rollback.'

            script {
                if (env.DEPLOYMENT_ATTEMPTED == 'true' &&
                    env.PREVIOUS_IMAGE_TAG?.trim()) {

                    echo "Rolling back to ${env.PREVIOUS_IMAGE_TAG}"

                    try {
                        withEnv(["IMAGE_TAG=${env.PREVIOUS_IMAGE_TAG}"]) {
                            sh '''
                                set -eu

                                cd "$DEPLOY_DIR"

                                echo "Pulling previous application images..."

                                docker-compose pull \
                                    user-service \
                                    product-service \
                                    order-service

                                echo "Restoring previous application version..."

                                docker-compose up -d --no-deps \
                                    user-service \
                                    product-service \
                                    order-service

                                echo "Checking restored services..."

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
                                        echo "ERROR: $service rollback health check failed"
                                        docker logs "$container_id"
                                        exit 1
                                    fi
                                done

                                echo "Testing restored application..."

                                curl -fsS http://localhost/health
                                curl -fsS http://localhost/api/users
                                curl -fsS http://localhost/api/products
                                curl -fsS http://localhost/api/orders

                                echo "Rollback verification successful"
                            '''
                        }

                        echo "ROLLBACK SUCCESSFUL: ${env.PREVIOUS_IMAGE_TAG} restored."

                    } catch (rollbackError) {
                        echo "ROLLBACK FAILED: ${rollbackError}"
                        currentBuild.result = 'FAILURE'
                    }

                } else {
                    echo 'Rollback skipped: deployment was not attempted or previous tag was not captured.'
                }
            }
        }
    }
}
