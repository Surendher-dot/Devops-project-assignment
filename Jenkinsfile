```groovy
pipeline {
    agent {
        label 'aws-ec2'
    }

    environment {
        COMPOSE_PROJECT_NAME = 'devops-project-assignment'
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

                    test -f user-service/app.py
                    test -f product-service/app.py
                    test -f order-service/app.py
                    test -f docker-compose.yml
                    test -f monitoring/prometheus.yml

                    python3 -m py_compile \
                        user-service/app.py \
                        product-service/app.py \
                        order-service/app.py

                    echo "Project validation successful"
                '''
            }
        }

        stage('Validate Docker Compose') {
            steps {
                sh 'docker-compose config -q'
            }
        }

        stage('Smoke Tests') {
            steps {
                sh '''
                    set -eu

                    curl -fsS http://localhost/health
                    curl -fsS http://localhost/api/users
                    curl -fsS http://localhost/api/products
                    curl -fsS http://localhost/api/orders
                    curl -fsS http://localhost:9090/-/healthy

                    echo "All smoke tests passed"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker-compose ps || true'
        }

        success {
            echo 'Microservices validation and smoke tests completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check stage logs.'
        }
    }
}
```
