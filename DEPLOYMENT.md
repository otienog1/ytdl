# Deployment Guide

Complete guide for deploying the YouTube Shorts Downloader to production.

## Overview

This application uses:
- **Vercel** for frontend hosting
- **Google Cloud Run** for backend hosting
- **MongoDB Atlas** for database
- **Redis Cloud** for caching and queues
- **Google Cloud Storage** for file storage

## Prerequisites

- GitHub account
- Vercel account
- Google Cloud Platform account
- MongoDB Atlas account
- Redis Cloud account (optional, can use GCP Memorystore)

## Part 1: Database Setup

### MongoDB Atlas

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a new cluster (M0 Free tier)
4. Create a database user
5. Add IP address 0.0.0.0/0 to whitelist (for Cloud Run)
6. Get connection string:
   - Click "Connect" → "Connect your application"
   - Copy connection string
   - Replace `<password>` with your password
   - Save as `MONGODB_URI`

### Redis Cloud

1. Go to https://redis.com/try-free
2. Create a free account
3. Create a new subscription (30MB Free tier)
4. Create a database
5. Get connection string from database details
6. Save as `REDIS_URL`

## Part 2: Google Cloud Setup

### 1. Create Project

```bash
gcloud projects create shorts-downloader-prod
gcloud config set project shorts-downloader-prod
```

### 2. Enable APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

### 3. Create Storage Bucket

```bash
gsutil mb -p shorts-downloader-prod gs://shorts-downloader-temp
```

### 4. Create Service Account

```bash
gcloud iam service-accounts create shorts-downloader-sa \
    --display-name="Shorts Downloader Service Account"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding shorts-downloader-prod \
    --member="serviceAccount:shorts-downloader-sa@shorts-downloader-prod.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create credentials.json \
    --iam-account=shorts-downloader-sa@shorts-downloader-prod.iam.gserviceaccount.com
```

## Part 3: Backend Deployment (Google Cloud Run)

### 1. Prepare Backend

Update `backend/.env` for production:

```env
NODE_ENV=production
MONGODB_URI=<your-atlas-connection-string>
REDIS_URL=<your-redis-cloud-url>
GCP_PROJECT_ID=shorts-downloader-prod
GCP_BUCKET_NAME=shorts-downloader-temp
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
PORT=8080
CORS_ORIGIN=https://your-domain.vercel.app
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30
FILE_EXPIRY_HOURS=24
```

### 2. Build and Push Docker Image

```bash
cd backend

# Build image
gcloud builds submit --tag gcr.io/shorts-downloader-prod/backend

# Or use Docker
docker build -t gcr.io/shorts-downloader-prod/backend .
docker push gcr.io/shorts-downloader-prod/backend
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy shorts-downloader-backend \
  --image gcr.io/shorts-downloader-prod/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "NODE_ENV=production" \
  --set-env-vars "MONGODB_URI=<your-mongodb-uri>" \
  --set-env-vars "REDIS_URL=<your-redis-url>" \
  --set-env-vars "GCP_PROJECT_ID=shorts-downloader-prod" \
  --set-env-vars "GCP_BUCKET_NAME=shorts-downloader-temp" \
  --set-env-vars "CORS_ORIGIN=https://your-domain.vercel.app" \
  --set-env-vars "RATE_LIMIT_WINDOW_MS=900000" \
  --set-env-vars "RATE_LIMIT_MAX_REQUESTS=30" \
  --set-env-vars "FILE_EXPIRY_HOURS=24"
```

### 4. Set Up Service Account

```bash
# Upload credentials.json as a secret
gcloud secrets create gcs-credentials --data-file=credentials.json

# Grant Cloud Run access to secret
gcloud run services update shorts-downloader-backend \
  --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=gcs-credentials:latest
```

### 5. Get Backend URL

```bash
gcloud run services describe shorts-downloader-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

Save this URL for frontend configuration.

## Part 4: Frontend Deployment (Vercel)

### 1. Push to GitHub

```bash
cd ..
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy to Vercel

1. Go to https://vercel.com
2. Import your GitHub repository
3. Select the `frontend` directory as root
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Cloud Run backend URL
5. Click "Deploy"

### 3. Configure Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `CORS_ORIGIN` in Cloud Run to include your custom domain

```bash
gcloud run services update shorts-downloader-backend \
  --region us-central1 \
  --update-env-vars "CORS_ORIGIN=https://your-custom-domain.com,https://your-vercel-domain.vercel.app"
```

## Part 5: Post-Deployment Configuration

### 1. Set Up Monitoring

**Cloud Run Monitoring:**
```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# View logs
gcloud run services logs read shorts-downloader-backend \
  --region us-central1
```

**Vercel Analytics:**
- Enable in Vercel dashboard under Analytics tab

### 2. Set Up Alerts

Create alert for Cloud Run errors:
```bash
gcloud alpha monitoring policies create \
  --notification-channels=<channel-id> \
  --display-name="Backend Error Rate" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=60s \
  --condition-display-name="Error rate" \
  --condition-threshold-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"'
```

### 3. Configure CDN (Optional)

For better performance, set up Cloud CDN:
```bash
gcloud compute backend-services create shorts-backend \
  --global \
  --enable-cdn
```

### 4. Set Up Auto-Scaling

Cloud Run auto-scales by default, but you can configure:

```bash
gcloud run services update shorts-downloader-backend \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80
```

### 5. Configure File Cleanup

The cleanup runs automatically every hour. To adjust:

Update `FILE_EXPIRY_HOURS` environment variable in Cloud Run.

## Part 6: Security Hardening

### 1. Enable Cloud Armor (DDoS Protection)

```bash
gcloud compute security-policies create shorts-security-policy \
  --description "Security policy for Shorts Downloader"

gcloud compute security-policies rules create 1000 \
  --security-policy shorts-security-policy \
  --expression "origin.region_code == 'CN'" \
  --action "deny-403"
```

### 2. Set Up Secret Manager

Move sensitive env vars to Secret Manager:

```bash
# Create secrets
echo -n "your-mongodb-uri" | gcloud secrets create mongodb-uri --data-file=-
echo -n "your-redis-url" | gcloud secrets create redis-url --data-file=-

# Update Cloud Run to use secrets
gcloud run services update shorts-downloader-backend \
  --region us-central1 \
  --update-secrets=MONGODB_URI=mongodb-uri:latest,REDIS_URL=redis-url:latest
```

### 3. Enable HTTPS Only

Both Vercel and Cloud Run enforce HTTPS by default.

## Part 7: Cost Optimization

### Estimated Monthly Costs (Light Usage)

- **Vercel**: Free tier (1TB bandwidth)
- **Cloud Run**: ~$5-20/month (depends on usage)
- **MongoDB Atlas**: Free tier (512MB)
- **Redis Cloud**: Free tier (30MB)
- **Cloud Storage**: ~$0.02/GB/month
- **Total**: ~$5-25/month for light usage

### Cost Saving Tips

1. **Use free tiers** where possible
2. **Set max instances** on Cloud Run to prevent runaway costs
3. **Enable file cleanup** to minimize storage costs
4. **Use CDN caching** to reduce Cloud Run requests
5. **Monitor usage** regularly in GCP Console

## Part 8: Maintenance

### Update Backend

```bash
cd backend
gcloud builds submit --tag gcr.io/shorts-downloader-prod/backend
gcloud run deploy shorts-downloader-backend \
  --image gcr.io/shorts-downloader-prod/backend \
  --region us-central1
```

### Update Frontend

```bash
git add .
git commit -m "Update frontend"
git push
# Vercel auto-deploys
```

### View Logs

**Backend:**
```bash
gcloud run services logs read shorts-downloader-backend --region us-central1 --limit 50
```

**Frontend:**
- View in Vercel Dashboard → Logs

### Monitor Performance

- Cloud Run: GCP Console → Cloud Run → Metrics
- Vercel: Vercel Dashboard → Analytics
- MongoDB: Atlas Dashboard → Metrics
- Redis: Redis Cloud Dashboard → Metrics

## Troubleshooting

### Backend not starting
- Check Cloud Run logs
- Verify environment variables
- Test MongoDB/Redis connections

### CORS errors
- Verify `CORS_ORIGIN` includes frontend URL
- Check frontend uses correct API URL

### File upload failures
- Check GCS bucket permissions
- Verify service account has access
- Check credentials secret is mounted

### Rate limiting issues
- Adjust `RATE_LIMIT_MAX_REQUESTS`
- Consider using Cloud Armor for better rate limiting

## Rollback Procedure

### Backend Rollback

```bash
# List revisions
gcloud run revisions list --service shorts-downloader-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic shorts-downloader-backend \
  --region us-central1 \
  --to-revisions <previous-revision>=100
```

### Frontend Rollback

1. Go to Vercel Dashboard
2. Select Deployments
3. Find previous deployment
4. Click "Promote to Production"

## Support

For deployment issues:
1. Check logs first
2. Review this guide
3. Consult GCP/Vercel documentation
4. Open GitHub issue with details
