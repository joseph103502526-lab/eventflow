pipeline {
    agent any

    environment {
        PROJECT_ID  = 'eventflow-tibame-2026'
        REGION      = 'asia-east1'
        REGISTRY    = "asia-east1-docker.pkg.dev/eventflow-tibame-2026/eventflow-repo"
        CHART_PATH  = './eventflow-chart'
        VALUES_PATH = './eventflow-chart-values'
        KUBECONFIG  = '/var/lib/jenkins/.kube/config'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH}, Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    cd event-service
                    python3 -m pip install flask==3.0.3 pytest --break-system-packages -q
                    python3 -m pytest tests/ -v --tb=short
                    cd ..
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${REGISTRY}/event-service:${BUILD_NUMBER} ./event-service
                    docker build -t ${REGISTRY}/booking-service:${BUILD_NUMBER} ./booking-service
                    docker build -t ${REGISTRY}/notification-service:${BUILD_NUMBER} ./notification-service
                    docker build -t ${REGISTRY}/api-gateway:${BUILD_NUMBER} ./api-gateway
                '''
            }
        }

        stage('Push to Artifact Registry') {
            steps {
                sh '''
                    gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
                    docker push ${REGISTRY}/event-service:${BUILD_NUMBER}
                    docker push ${REGISTRY}/booking-service:${BUILD_NUMBER}
                    docker push ${REGISTRY}/notification-service:${BUILD_NUMBER}
                    docker push ${REGISTRY}/api-gateway:${BUILD_NUMBER}
                '''
            }
        }

        stage('Deploy to GKE') {
            steps {
                sh '''
                    helm upgrade --install event-service ${CHART_PATH} \
                        -f ${VALUES_PATH}/event-service.yaml \
                        --set image.tag=${BUILD_NUMBER} \
                        --wait --timeout 5m

                    helm upgrade --install booking-service ${CHART_PATH} \
                        -f ${VALUES_PATH}/booking-service.yaml \
                        --set image.tag=${BUILD_NUMBER} \
                        --wait --timeout 5m

                    helm upgrade --install notification-service ${CHART_PATH} \
                        -f ${VALUES_PATH}/notification-service.yaml \
                        --set image.tag=${BUILD_NUMBER} \
                        --wait --timeout 5m

                    helm upgrade --install api-gateway ${CHART_PATH} \
                        -f ${VALUES_PATH}/api-gateway.yaml \
                        --set image.tag=${BUILD_NUMBER} \
                        --wait --timeout 5m
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS - Build ${BUILD_NUMBER} deployed to GKE"
        }
        failure {
            echo "Pipeline FAILED - Build ${BUILD_NUMBER}"
        }
    }
}
