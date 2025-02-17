#!/bin/bash

# Exit on any error
set -e

echo "Updating packages..."
apt-get update -y
apt-get upgrade -y

apt install make

echo "Installing dependencies..."
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

echo "Adding Docker’s GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

echo "Adding Docker APT repository..."
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

echo "Installing Docker..."
apt-get update -y
apt-get install -y docker-ce

echo "Enabling and starting Docker..."
systemctl enable docker
systemctl start docker

echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="v2.16.0"
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "Installation complete!"
docker --version
docker-compose --version
