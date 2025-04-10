pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r automation-scripts/requirements.txt'
            }
        }
        stage('Run Data Ingestion') {
            steps {
                sh 'python src/data_ingestion/fetch_ohlvc.py'
            }
        }
    }
    triggers {
        cron('H 2 * * *') // Executes daily at approximately 2 AM UTC
    }
}