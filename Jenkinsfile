pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup Python Environment') {
            steps {
                sh '''
                    # Create a virtual environment named venv
                    python3 -m venv venv
                    # Activate the virtual environment and upgrade pip
                    . venv/bin/activate
                    pip install --upgrade pip
                    # Install dependencies from requirements.txt
                    pip install -r automation-scripts/requirements.txt
                '''
            }
        }
        stage('Run Data Ingestion') {
            steps {
                sh '''
                    # Activate the virtual environment and run the script
                    . venv/bin/activate
                    python src/data_ingestion/fetch_ohlvc.py
                '''
            }
        }
    }
    triggers {
        cron('H 2 * * *') // Executes daily at approximately 2 AM UTC
    }
}