#!/bin/bash

CONTAINER_NAME="formflow-minio"
IMAGE="minio/minio:RELEASE.2023-03-20T20-16-18Z"
DATA_DIR="$HOME/minio-data"

echo "Starting MinIO container..."

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container ${CONTAINER_NAME} already exists, starting it..."
    docker start ${CONTAINER_NAME}
else
    echo "Creating and starting MinIO container..."
    mkdir -p ${DATA_DIR}
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p 9000:9000 \
        -p 9001:9001 \
        -e MINIO_ROOT_USER=minioadmin \
        -e MINIO_ROOT_PASSWORD=minioadmin123 \
        -v ${DATA_DIR}:/data \
        ${IMAGE} server /data --console-address ":9001"
fi

echo ""
echo "MinIO Status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "MinIO Console: http://localhost:9001"
echo "MinIO API: http://localhost:9000"
echo "Username: minioadmin"
echo "Password: minioadmin123"
