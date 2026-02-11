# Pre-Deployment Checklist

Use this checklist to ensure everything is configured correctly before deploying to production.

## Development Setup Checklist

### Prerequisites
- [ ] Node.js 18+ installed
- [ ] npm installed
- [ ] yt-dlp installed and in PATH
- [ ] ffmpeg installed and in PATH
- [ ] Git installed
- [ ] Code editor (VS Code recommended)

### Local Services
- [ ] MongoDB running (local or Atlas connection)
- [ ] Redis running (local or cloud connection)
- [ ] Google Cloud Storage bucket created
- [ ] GCS service account created with Storage Admin role
- [ ] GCS credentials JSON downloaded

### Backend Setup
- [ ] `cd backend && npm install` completed
- [ ] `backend/.env` created and configured
- [ ] MongoDB URI set correctly
- [ ] Redis URL set correctly
- [ ] GCS credentials path set correctly
- [ ] GCS bucket name set correctly
- [ ] CORS_ORIGIN set to frontend URL
- [ ] Backend starts without errors: `npm run dev`
- [ ] Health check works: `curl http://localhost:3001/health`

### Frontend Setup
- [ ] `cd frontend && npm install` completed
- [ ] `frontend/.env.local` created and configured
- [ ] NEXT_PUBLIC_API_URL set to backend URL
- [ ] Frontend starts without errors: `npm run dev`
- [ ] Can access http://localhost:3000
- [ ] UI loads correctly

### Integration Testing
- [ ] Frontend can reach backend API
- [ ] CORS is properly configured
- [ ] Can submit a valid YouTube Shorts URL
- [ ] Job is created and queued
- [ ] Status polling works
- [ ] Video info is fetched correctly
- [ ] Video downloads successfully
- [ ] File uploads to GCS
- [ ] Download URL is generated
- [ ] Can download the MP4 file
- [ ] Error handling works for invalid URLs

## Production Deployment Checklist

### Google Cloud Platform Setup
- [ ] GCP project created
- [ ] Billing enabled on GCP project
- [ ] Cloud Run API enabled
- [ ] Cloud Build API enabled
- [ ] Cloud Storage API enabled
- [ ] Storage bucket created
- [ ] Service account created
- [ ] Service account has Storage Admin role
- [ ] Service account key downloaded

### MongoDB Atlas Setup
- [ ] MongoDB Atlas account created
- [ ] Cluster created (M0 Free or higher)
- [ ] Database user created with read/write access
- [ ] Network access configured (0.0.0.0/0 for Cloud Run)
- [ ] Connection string obtained
- [ ] Connection tested from local machine

### Redis Cloud Setup
- [ ] Redis Cloud account created (or using GCP Memorystore)
- [ ] Redis database created
- [ ] Connection string obtained
- [ ] Connection tested from local machine

### Backend Deployment (Cloud Run)
- [ ] Backend code committed to Git
- [ ] Dockerfile tested locally: `docker build -t backend .`
- [ ] Environment variables prepared for Cloud Run
- [ ] Docker image built: `gcloud builds submit --tag gcr.io/PROJECT_ID/backend`
- [ ] Cloud Run service deployed
- [ ] Environment variables set in Cloud Run
- [ ] Service account configured for GCS access
- [ ] Health check endpoint accessible
- [ ] Backend URL obtained and saved
- [ ] Logs are working: `gcloud run services logs read SERVICE_NAME`

### Frontend Deployment (Vercel)
- [ ] Frontend code pushed to GitHub
- [ ] Vercel account created
- [ ] Project imported in Vercel
- [ ] Build settings configured (root: frontend)
- [ ] Environment variables set in Vercel
- [ ] NEXT_PUBLIC_API_URL set to Cloud Run URL
- [ ] Build succeeds
- [ ] Deployment successful
- [ ] Frontend URL accessible
- [ ] UI loads correctly

### Post-Deployment Configuration
- [ ] Backend CORS_ORIGIN updated with Vercel URL
- [ ] Backend redeployed with updated CORS
- [ ] Frontend can reach backend
- [ ] End-to-end test: submit URL, download video
- [ ] Rate limiting is working
- [ ] File cleanup schedule is running
- [ ] Error tracking is configured
- [ ] Monitoring is set up

### Security Checklist
- [ ] Environment variables are not committed to Git
- [ ] .gitignore includes .env files
- [ ] Service account keys are not in repository
- [ ] CORS is properly configured (not allowing *)
- [ ] Rate limiting is enabled
- [ ] Helmet.js is configured
- [ ] HTTPS is enforced (default on Vercel/Cloud Run)
- [ ] Input validation is working
- [ ] Error messages don't expose sensitive info

### Legal & Compliance
- [ ] Terms of Use page is accessible
- [ ] Privacy Policy page is accessible
- [ ] FAQ page is accessible
- [ ] Copyright notices are displayed
- [ ] Legal disclaimers are visible
- [ ] Usage guidelines are clear

### Performance & Monitoring
- [ ] Cloud Run auto-scaling is configured
- [ ] Max instances set to prevent runaway costs
- [ ] Min instances set appropriately
- [ ] Memory allocation is adequate (2GB recommended)
- [ ] Timeout is appropriate (300s for Cloud Run)
- [ ] Logs are accessible and readable
- [ ] Error tracking is working
- [ ] Performance monitoring is active

### Cost Management
- [ ] Free tier resources are used where possible
- [ ] Max instances limit set on Cloud Run
- [ ] Budget alerts configured in GCP
- [ ] File expiry is set to 24 hours
- [ ] Cleanup job is running
- [ ] Storage costs are monitored
- [ ] Bandwidth usage is tracked

### Documentation
- [ ] README.md is up to date
- [ ] QUICKSTART.md is accurate
- [ ] DEPLOYMENT.md is complete
- [ ] API endpoints are documented
- [ ] Environment variables are documented
- [ ] Architecture is documented

### Testing Production
- [ ] Health check returns 200 OK
- [ ] Can submit YouTube Shorts URL
- [ ] Video processing works
- [ ] Download completes successfully
- [ ] Error handling works for invalid URLs
- [ ] Rate limiting triggers correctly
- [ ] CORS works from frontend
- [ ] Mobile UI is responsive
- [ ] Desktop UI is functional
- [ ] All legal pages are accessible

### Rollback Plan
- [ ] Previous Cloud Run revision is available
- [ ] Previous Vercel deployment is available
- [ ] Know how to rollback backend
- [ ] Know how to rollback frontend
- [ ] Database backups are configured
- [ ] Have tested rollback procedure

## Launch Checklist

### Pre-Launch
- [ ] All above checklists completed
- [ ] End-to-end testing passed
- [ ] Performance testing completed
- [ ] Security review done
- [ ] Legal review done
- [ ] Documentation reviewed
- [ ] Team trained on deployment process
- [ ] Monitoring alerts configured
- [ ] Incident response plan in place

### Launch Day
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Verify health checks
- [ ] Test critical user flows
- [ ] Monitor logs for errors
- [ ] Check performance metrics
- [ ] Announce launch (if applicable)
- [ ] Monitor user feedback

### Post-Launch
- [ ] Monitor error rates
- [ ] Track usage metrics
- [ ] Review performance
- [ ] Check cost estimates vs actual
- [ ] Collect user feedback
- [ ] Plan improvements
- [ ] Schedule regular maintenance

## Maintenance Checklist

### Daily
- [ ] Check error logs
- [ ] Monitor API response times
- [ ] Review cost dashboard
- [ ] Check file storage usage

### Weekly
- [ ] Review download success rate
- [ ] Check rate limiting effectiveness
- [ ] Monitor storage costs
- [ ] Review user feedback

### Monthly
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] Cost optimization review
- [ ] Backup verification
- [ ] Documentation updates

### Quarterly
- [ ] Major dependency updates
- [ ] Security penetration testing
- [ ] Architecture review
- [ ] Scaling assessment
- [ ] Legal compliance review

## Emergency Contacts

Document your emergency contacts:

- [ ] GCP Support: _________________
- [ ] Vercel Support: _________________
- [ ] MongoDB Atlas Support: _________________
- [ ] Redis Cloud Support: _________________
- [ ] Team Lead: _________________
- [ ] DevOps Contact: _________________

## Notes

Use this space for deployment-specific notes:

```
Date deployed: __________
Backend URL: __________
Frontend URL: __________
GCP Project: __________
MongoDB Cluster: __________
Redis Instance: __________

Special configurations:
-
-
-

Known issues:
-
-
-
```

---

**Remember**: Always test in a staging environment before deploying to production!
