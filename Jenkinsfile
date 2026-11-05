pipeline {
    agent {
        label 'aws-ec2'
    }
    environment {
        COMPOSE_PROJECT_NAME = 'microservices-devops'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Validate Project') {
            steps {
                sh '''
                    test -f user-service/app.py
                    test -f product-service/app.py
                    test -f order-service/app.py
                    test -f docker-compose.yml
                    test -f monitoring/prometheus.yml
                    python3 -m py_compile user-service/app.py product-service/app.py order-service/app.py
                '''
            }
        }
        stage('Build Docker Images') {
            steps { sh 'docker compose build' }
        }
        stage('Start Services') {
            steps { sh 'docker compose up -d' }
        }
        stage('Smoke Tests') {
            steps {
                sh '''
                    set -eu
                    for attempt in $(seq 1 20); do
                      if curl -fsS http://localhost/health >/dev/null; then break; fi
                      sleep 3
                    done
                    curl -fsS http://localhost/api/users
                    curl -fsS http://localhost/api/products
                    curl -fsS http://localhost/api/orders
                    curl -fsS http://localhost:9090/-/healthy
                '''
            }
        }
    }
    post {
        always { sh 'docker compose ps || true' }
        success { echo 'Microservices build and smoke tests completed successfully.' }
        failure { echo 'Pipeline failed. Check stage logs and container logs.' }
    }
}
