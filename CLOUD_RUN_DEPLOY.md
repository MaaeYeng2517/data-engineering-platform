# Cloud Run Deployment for DataAir Backend

## Prerequisites

1. **Install Google Cloud SDK:**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate & Set Project:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth configure-docker
   ```

3. **Enable APIs:**
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
   ```

## Quick Deploy (using Cloud Build)

```bash
cd /Users/maaeyeng/data-engineering-platform

# Build and deploy in one command
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
  --set-env-vars="APP_ENV=production,DEBUG=false,LLM_PROVIDER=google,GOOGLE_API_KEY=AIzaSyDuqhE_jPWaznJPvjfLFstEChpJsFg3pmQ,FRONTEND_URL=https://maaelab-data-air.vercel.app,ALLOWED_ORIGINS=https://maaelab-data-air.vercel.app,COOKIE_SECURE=true,JWT_SECRET_KEY=$(openssl rand -hex 32),CSRF_SECRET_KEY=$(openssl rand -hex 32),API_KEY_HMAC_SECRET=$(openssl rand -hex 32),PROFILE_SECRET_KEY=$(openssl rand -hex 32),ADMIN_EMAILS=your-email@example.com"
```

## With External Services (Cloud SQL, Memorystore, etc.)

For production, you'll need managed services. Create them first:

```bash
# Cloud SQL PostgreSQL
gcloud sql instances create dataair-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=your-secure-password

gcloud sql databases create dataair --instance=dataair-db

# Memorystore Redis
gcloud redis instances create dataair-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0

# Get connection details
gcloud sql instances describe dataair-db --format="value(connectionName)"
gcloud redis instances describe dataair-redis --region=us-central1 --format="value(host)"
```

Then deploy with Cloud SQL & Redis connections:

```bash
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
  --add-cloudsql-instances=YOUR_PROJECT:us-central1:dataair-db \
  --vpc-connector=projects/YOUR_PROJECT/locations/us-central1/connectors/YOUR_CONNECTOR \
  --set-env-vars="APP_ENV=production,DEBUG=false,LLM_PROVIDER=google,GOOGLE_API_KEY=AIzaSyDuqhE_jPWaznJPvjfLFstEChpJsFg3pmQ,FRONTEND_URL=https://maaelab-data-air.vercel.app,ALLOWED_ORIGINS=https://maaelab-data-air.vercel.app,COOKIE_SECURE=true,JWT_SECRET_KEY=...,CSRF_SECRET_KEY=...,API_KEY_HMAC_SECRET=...,PROFILE_SECRET_KEY=...,ADMIN_EMAILS=...,DATABASE_URL=postgresql+asyncpg://user:pass@/dataair?host=/cloudsql/YOUR_PROJECT:us-central1:dataair-db,REDIS_URL=redis://REDIS_HOST:6379/0"
```

## Using the Cloud Run Config File

Or use the `cloudrun.yaml` file:

```bash
gcloud run services replace cloudrun.yaml --region=us-central1
```

Then update environment variables in Cloud Console or:
```bash
gcloud run services update dataair-backend \
  --region=us-central1 \
  --update-env-vars="KEY=value,..."
```

## Get Service URL

```bash
gcloud run services describe dataair-backend --region=us-central1 --format="value(status.url)"
```

## Update Vercel Frontend

```bash
cd /Users/maaeyeng/data-engineering-platform/frontend
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://dataair-backend-xxxxx-uc.a.run.app/api/v1
vercel --prod
```