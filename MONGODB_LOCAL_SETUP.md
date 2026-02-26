# Local MongoDB Setup for Development

This guide will help you set up a local MongoDB instance for development to avoid connection limit issues with MongoDB Atlas.

## Step 1: Install MongoDB Community Edition

### Option A: Using Chocolatey (Recommended for Windows)
```powershell
# Run PowerShell as Administrator
choco install mongodb

# Or install MongoDB Community Server
choco install mongodb-database-tools
```

### Option B: Manual Installation
1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community
2. Choose Windows x64 version
3. Run the installer (choose "Complete" installation)
4. Select "Install MongoDB as a Service" during installation
5. Keep the default data directory: `C:\Program Files\MongoDB\Server\<version>\data`

## Step 2: Verify Installation

Open a new Command Prompt or PowerShell and run:
```bash
mongod --version
mongo --version  # or mongosh --version for newer versions
```

## Step 3: Start MongoDB Service

### If installed as Windows Service:
```powershell
# Start the service
net start MongoDB

# Check service status
sc query MongoDB
```

### If not installed as service:
```bash
# Create data directory
mkdir C:\data\db

# Start MongoDB manually
mongod --dbpath C:\data\db
```

## Step 4: Export Data from Remote MongoDB Atlas

We'll use the connection string from your .env file to export the data:

```bash
# Navigate to backend directory
cd backend-python

# Export the entire database (replace <connection-string> with your actual MongoDB URI)
# The script below will do this automatically
```

Run the provided script: `export-remote-db.bat`

## Step 5: Import Data to Local MongoDB

After exporting, import to your local instance:

```bash
# Run the import script
import-to-local-db.bat
```

## Step 6: Update Environment Variables

Update `backend-python\.env` to use local MongoDB:

```env
# Development - Local MongoDB
MONGODB_URI=mongodb://localhost:27017/youtube_shorts_downloader

# Production - MongoDB Atlas (keep as backup)
# MONGODB_URI=mongodb+srv://...
```

## Step 7: Restart Backend Server

```bash
cd backend-python
# Stop the current server (Ctrl+C)
# Start again
.\start-dev.bat
```

## Troubleshooting

### MongoDB service won't start
- Check if port 27017 is already in use: `netstat -ano | findstr :27017`
- Check MongoDB logs: `C:\Program Files\MongoDB\Server\<version>\log\mongod.log`

### Connection refused
- Ensure MongoDB service is running: `sc query MongoDB`
- Check firewall settings

### Import fails
- Ensure you have enough disk space
- Check that mongorestore is in your PATH

## Switching Back to Atlas

To switch back to Atlas for production:
1. Comment out the local MongoDB URI in `.env`
2. Uncomment the Atlas URI
3. Restart the backend server

## Benefits of Local MongoDB for Development

✅ No connection limits
✅ Faster development (no network latency)
✅ Works offline
✅ Full control over data
✅ No cost concerns
✅ Can test without affecting production data
