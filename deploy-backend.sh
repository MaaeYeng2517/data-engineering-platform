#!/bin/bash
# deploy-backend.sh - Deploy DataAir backend to Google Cloud Run
# Run this in your terminal after: brew install --cask google-cloud-sdk && gcloud auth login

set -e

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
  echo "Error: No gcloud project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo "📦 Project: $PROJECT_ID"
echo "🔧 Enabling APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com redis.googleapis.com

echo "🐘 Creating Cloud SQL PostgreSQL..."
gcloud sql instances create dataair-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=$(openssl rand -base64 32) 2>/dev/null || echo "Instance may exist, continuing..."

gcloud sql databases create dataair --instance=dataair-db 2>/dev/null || true

echo "🔴 Creating Memorystore Redis..."
gcloud redis instances create dataair-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 2>/dev/null || echo "Instance may exist, continuing..."

export DB_CONN=$(gcloud sql instances describe dataair-db --format="value(connectionName)")
export REDIS_HOST=$(gcloud redis instances describe dataair-redis --region=us-central1 --format="value(host)")
export DB_PASSWORD=$(gcloud sql instances describe dataair-db --format="value(rootPassword)" 2>/dev/null || echo "")

if [ -z "$DB_PASSWORD" ]; then
  echo "⚠️  Could not fetch DB password. Get it from Cloud Console and update DATABASE_URL manually."
  DB_PASSWORD="YOUR_DB_PASSWORD_HERE"
fi

echo "📍 DB_CONN: $DB_CONN"
echo "📍 REDIS_HOST: $REDIS_HOST"

echo "🚀 Deploying backend to Cloud Run..."
cd /Users/maaeyeng/data-engineering-platform

gcloud run deploy dataair-backend \
  --source=backend \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --add-cloudsql-instances=$DB_CONN \
  --set-env-vars="APP_ENV=production,DEBUG=false,LLM_PROVIDER=google,GOOGLE_API_KEY=AIzaSyDuqhE_jPWaznJPvjfLFstEChpJsFg3pmQ,GEMINI_MODEL=gemini-3.8-flash,LLM_OFFLINE_FALLBACK=true,LLM_REQUEST_TIMEOUT=60,FRONTEND_URL=https://maaelab-data-air.vercel.app,PUBLIC_BASE_URL=https://maaelab-data-air.vercel.app,ALLOWED_ORIGINS=https://maaelab-data-air.vercel.app,COOKIE_SECURE=true,COOKIE_SAMESITE=lax,JWT_SECRET_KEY=$(openssl rand -hex 32),CSRF_SECRET_KEY=$(openssl rand -hex 32),API_KEY_HMAC_SECRET=$(openssl rand -hex 32),PROFILE_SECRET_KEY=$(openssl rand -hex 32),ADMIN_EMAILS=your-email@example.com,DATABASE_URL=postgresql+asyncpg://postgres:$DB_PASSWORD@/dataair?host=/cloudsql/$DB_CONN,REDIS_URL=redis://$REDIS_HOST:6379/0"

echo "✅ Backend deployed!"

export BACKEND_URL=$(gcloud run services describe dataair-backend --region=us-central1 --format="value(status.url)")
echo "🌐 Backend URL: $BACKEND_URL"

echo ""
echo "📝 Now update Vercel frontend:"
echo "cd /Users/maaeyeng/data-engineering-platform/frontend"
echo "vercel env add NEXT_PUBLIC_API_URL production"
echo "# Enter: $BACKEND_URL/api/v1"
echo "vercel --prod"