# Security Best Practices

## Environment Variables

This application uses environment variables to protect sensitive credentials. **NEVER** commit actual credentials to version control.

### Required Environment Variables

All sensitive data should be stored in environment variables or a `.env` file (which is gitignored).

See [`.env.example`](.env.example) for a complete list of required environment variables.

### Setting Up Environment Variables

#### Development (Local)

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual credentials:
   ```bash
   nano .env
   ```

3. **NEVER** commit the `.env` file to git (it's already in `.gitignore`)

#### Production (Server)

Set environment variables directly on the server or use a `.env.production` file:

```bash
# Option 1: Set system environment variables
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/database_name"
export REDIS_URL="redis://localhost:6379"

# Option 2: Use .env.production file (gitignored)
cp .env.example .env.production
nano .env.production
```

### Scripts That Use Environment Variables

The following scripts now use environment variables instead of hardcoded credentials:

#### `export-remote-db.bat`

**Required Environment Variable:** `MONGODB_ATLAS_URI`

```bash
# Set the variable before running the script
set MONGODB_ATLAS_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
export-remote-db.bat
```

Or add it to your `.env` file.

## Sensitive Files

The following files are **NEVER** committed to version control (see `.gitignore`):

- `.env` - Local environment variables
- `.env.*` - All environment files except `.env.example`
- `*cookies.txt` - YouTube cookies
- `youtube*.txt` - YouTube-related credentials
- `*.json` - Google Cloud credentials (except `package.json`, `tsconfig.json`)
- `divine-actor-*.json` - GCP service account keys

## Git History Cleanup

If you accidentally commit sensitive data:

1. **Remove from working directory:**
   ```bash
   git rm --cached .env
   ```

2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

3. **Force push** (⚠️ WARNING: This rewrites history):
   ```bash
   git push --force-with-lease
   ```

## Credential Rotation

If credentials are exposed:

1. **Immediately rotate:**
   - MongoDB Atlas password
   - AWS access keys
   - Azure storage keys
   - GCP service account keys
   - Mailgun API keys

2. **Update environment variables** with new credentials

3. **Restart services:**
   ```bash
   sudo systemctl restart ytd-backend ytd-celery
   ```

## GitHub Secret Scanning

This repository has GitHub secret scanning enabled. If you push credentials:

1. GitHub will **block the push**
2. You'll receive an error with detected secrets
3. Follow the instructions to:
   - Remove secrets from commits
   - Or mark as false positive (only if truly safe)

## Best Practices

✅ **DO:**
- Use environment variables for all secrets
- Keep `.env` files local only
- Use different credentials for dev/staging/production
- Rotate credentials regularly
- Use read-only credentials where possible
- Enable MFA on cloud accounts

❌ **DON'T:**
- Commit `.env` files
- Hardcode credentials in scripts
- Share credentials via email/chat
- Use production credentials in development
- Commit backup files with credentials (`.env.backup`, `.env.atlas.backup`)
- Log sensitive data

## Monitoring

Watch for suspicious activity:

```bash
# Check for .env access attempts (suspicious bots)
sudo tail -f /var/log/nginx/access.log | grep -i ".env"

# Monitor failed login attempts
sudo journalctl -u ytd-backend -f | grep -i "auth\|login\|401\|403"
```

## Emergency Response

If credentials are compromised:

1. **Immediately** disable/rotate affected credentials
2. Review access logs for unauthorized usage
3. Check for data exfiltration
4. Update all instances with new credentials
5. Document the incident
6. Consider filing a security report if needed

## Contact

For security concerns, contact: admin@yourdomain.com
