# Dockerfile
FROM jenkins/jenkins:lts

# Switch to root to install additional packages
USER root

# Install Python3 and pip3
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3.11-venv && \
    apt-get clean

# Revert to the jenkins user
USER jenkins