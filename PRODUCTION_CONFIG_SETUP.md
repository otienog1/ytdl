# Production Configuration Setup

## ⚠️ Important: Sensitive Files Not in Repo

The actual production configuration files (`.env.production.server*`) contain sensitive information (passwords, API keys, credentials) and are **NOT stored in this repository**.

They are `.gitignore`d to prevent accidental commits.

## 📁 Configuration Files Structure

```
backend-python/
├── .env.production.server1        # ❌ NOT in repo (sensitive)
├── .env.production.server2        # ❌ NOT in repo (sensitive)
├── .env.production.server3        # ❌ NOT in repo (sensitive)
└── .env.production.server1.example # ✅ Template in repo

cookie-extractor/
├── .env.production.server1        # ❌ NOT in repo (sensitive)
├── .env.production.server2        # ❌ NOT in repo (sensitive)
├── .env.production.server3        # ❌ NOT in repo (sensitive)
└── .env.production.server1.example # ✅ Template in repo
```

## 🔧 How to Create Production Configs

### Step 1: Create Backend Configs

```bash
cd backend-python

# Copy template for each server
cp .env.production.server1.example .env.production.server1
cp .env.production.server1.example .env.production.server2
cp .env.production.server1.example .env.production.server3
```

### Step 2: Fill in Real Values

Edit each file and replace placeholder values:

**`.env.production.server1`** (Server 1 - Account A):
```bash
# MongoDB
MONGODB_URI=mongodb+srv://mongoatlas_user:REAL_PASSWORD@cluster.mongodb.net/ytdl_db

# Shared Redis
BULL_REDIS_URL=redis://mdlworker:REAL_PASSWORD@57.159.27.119:6379/2

# GCP
GCP_PROJECT_ID=divine-actor-473706-k4
GCP_BUCKET_NAME=ytdl_bkt
GOOGLE_APPLICATION_CREDENTIALS=/opt/ytdl/backend-python/divine-actor-473706-k4-fdec9ee56ba0.json

# Account A specific
YT_ACCOUNT_ID=account_a
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_a.txt

# ... (fill in all other values)
```

**`.env.production.server2`** (Server 2 - Account B):
```bash
# Same as server1 but change:
YT_ACCOUNT_ID=account_b
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_b.txt
```

**`.env.production.server3`** (Server 3 - Account C):
```bash
# Same as server1 but change:
YT_ACCOUNT_ID=account_c
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_c.txt
```

### Step 3: Create Cookie Extractor Configs

```bash
cd cookie-extractor

# Copy template for each server
cp .env.production.server1.example .env.production.server1
cp .env.production.server1.example .env.production.server2
cp .env.production.server1.example .env.production.server3
```

**`.env.production.server1`** (Account A):
```bash
REDIS_HOST=57.159.27.119
REDIS_PASSWORD=REAL_PASSWORD
ACCOUNT_ID=account_a
YT_EMAIL=otienog1@yahoo.com
YT_PASSWORD=REAL_PASSWORD
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-a
CHROME_DEBUG_PORT=9222
```

**`.env.production.server2`** (Account B):
```bash
ACCOUNT_ID=account_b
YT_EMAIL=otienog1@icluod.com
YT_PASSWORD=REAL_PASSWORD
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-b
CHROME_DEBUG_PORT=9223
```

**`.env.production.server3`** (Account C):
```bash
ACCOUNT_ID=account_c
YT_EMAIL=7plus8studios@gmail.com
YT_PASSWORD=REAL_PASSWORD
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-c
CHROME_DEBUG_PORT=9224
```

## 🔐 Security Best Practices

1. **NEVER commit `.env.production.server*` files**
   - They're already in `.gitignore`
   - Double-check before committing: `git status`

2. **Store backups securely**
   - Use encrypted storage (1Password, LastPass, etc.)
   - Or secure cloud storage (not in repo!)

3. **Use environment-specific credentials**
   - Production: Strong passwords
   - Development: `.env` file (also gitignored)

4. **Rotate credentials regularly**
   - Update all `.env.production.server*` files
   - Redeploy with new credentials

## 📤 Deployment

Once you've created the `.env.production.server*` files:

```bash
# Deploy from your local machine
deploy-from-local.bat

# Or manually on each server
ssh root@ytd.timobosafaris.com
cd /opt/ytdl
sudo bash deploy-hybrid-redis.sh 1
```

The deployment script will:
1. Copy `.env.production.server1` → `.env.production` on Server 1
2. Copy `.env.production.server2` → `.env.production` on Server 2
3. Copy `.env.production.server3` → `.env.production` on Server 3

## ✅ Verify Configuration

After creating configs:

```bash
# Check that sensitive files exist locally but not in git
ls -la backend-python/.env.production.server*
git status  # Should NOT show .env.production.server* files

# Verify gitignore is working
git check-ignore backend-python/.env.production.server1
# Should output: backend-python/.env.production.server1
```

## 🆘 If You Accidentally Committed Sensitive Files

```bash
# Remove from git (keeps local file)
git rm --cached backend-python/.env.production.server*
git rm --cached cookie-extractor/.env.production.server*

# Commit the removal
git commit -m "Remove sensitive .env files from git"

# If already pushed, force push (WARNING: coordinate with team)
git push origin master --force

# Then rotate ALL credentials in those files!
```

## 📋 Checklist

- [ ] Created all 3 backend `.env.production.server*` files
- [ ] Created all 3 cookie-extractor `.env.production.server*` files
- [ ] Filled in real credentials (no placeholders)
- [ ] Verified files are NOT in git (`git status`)
- [ ] Stored backup of configs in secure location
- [ ] Ready to deploy with `deploy-from-local.bat`

## 📚 Related Documentation

- [DEPLOY_README.md](DEPLOY_README.md) - Deployment guide
- [QUICK_DEPLOY.md](QUICK_DEPLOY.md) - Quick deployment reference
- [DEPLOY_HYBRID_REDIS.md](DEPLOY_HYBRID_REDIS.md) - Complete hybrid Redis guide
