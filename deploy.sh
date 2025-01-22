#!/bin/bash
set -e  # Exit on error

# Configuration
PROJECT_ID="mltest-202903"
IMAGE_NAME="code-analysis-report"
REGION="us-central1"  # Default region
SERVICE_NAME="code-analysis-report"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting deployment process...${NC}"

# Step 1: Build the Docker image
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t "gcr.io/${PROJECT_ID}/${IMAGE_NAME}" .

# Step 2: Configure Docker to use Google Cloud credentials
echo -e "${BLUE}Configuring Docker authentication...${NC}"
gcloud auth configure-docker

# Step 3: Push the image to Google Container Registry
echo -e "${BLUE}Pushing image to Google Container Registry...${NC}"
docker push "gcr.io/${PROJECT_ID}/${IMAGE_NAME}"

# Step 4: Deploy to Cloud Run
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "gcr.io/${PROJECT_ID}/${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --project "${PROJECT_ID}"

# Step 5: Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format 'value(status.url)')

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
