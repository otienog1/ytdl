# Quick Start: Switch to Local MongoDB

Your backend is now configured to use **local MongoDB** instead of MongoDB Atlas. This eliminates the "max number of clients reached" error!

## ✅ What's Already Done

1. ✅ `.env` file updated to use `mongodb://localhost:27017/youtube_shorts_downloader`
2. ✅ `.env.atlas.backup` created (your original Atlas configuration)
3. ✅ Export script created: `export-remote-db.bat`
4. ✅ Import script created: `import-to-local-db.bat`
5. ✅ MongoDB connection pool configured (50 max connections)

## 🚀 Next Steps

### Option A: Start Fresh with Empty Database (Fastest)

Just restart your backend server:

```bash
# Stop current server (Ctrl+C)
# Then restart:
.\start-dev.bat
```

✅ **Done!** Your app will work with an empty local database.

### Option B: Migrate Existing Data from Atlas

If you want to copy your existing data from MongoDB Atlas:

1. **Export data from Atlas** (takes 1-2 minutes):
   ```bash
   .\export-remote-db.bat
   ```

2. **Import to local MongoDB**:
   ```bash
   .\import-to-local-db.bat
   ```

3. **Restart backend server**:
   ```bash
   .\start-dev.bat
   ```

## 📊 Verify It's Working

After restarting, you should see in the logs:
```
MongoDB connected successfully to database: youtube_shorts_downloader
```

Try downloading a video - the "max number of clients reached" error should be gone!

## 🔄 Switching Back to Atlas

To switch back to MongoDB Atlas:

1. Edit `.env` file
2. Comment out local MongoDB:
   ```env
   # MONGODB_URI=mongodb://localhost:27017/youtube_shorts_downloader
   ```
3. Uncomment Atlas URI:
   ```env
   MONGODB_URI=mongodb+srv://mongoatlas_user:...
   ```
4. Restart backend server

## 🎯 Benefits of Local MongoDB

- ✅ **No connection limits** - unlimited connections
- ✅ **Faster** - no network latency
- ✅ **Works offline** - develop anywhere
- ✅ **Free** - no cost concerns
- ✅ **Safe testing** - won't affect production data

## 🐛 Troubleshooting

### MongoDB Not Running
```bash
# Check if MongoDB service is running
sc query MongoDB

# Start MongoDB service
net start MongoDB
```

### Can't Connect to MongoDB
- Check if port 27017 is available: `netstat -ano | findstr :27017`
- Check MongoDB logs (usually in: `C:\Program Files\MongoDB\Server\<version>\log\mongod.log`)

### mongodump/mongorestore Not Found
- Add MongoDB bin folder to PATH:
  `C:\Program Files\MongoDB\Server\<version>\bin`
- Or use full path in scripts

## 📝 Database Details

- **Local Database Name**: `youtube_shorts_downloader`
- **Connection String**: `mongodb://localhost:27017/youtube_shorts_downloader`
- **Default Port**: `27017`
- **Collections**: `downloads`, `storage_stats`

## 💾 Data Location

MongoDB data is stored at: `C:\Program Files\MongoDB\Server\<version>\data\db`

---

**Ready?** Just run `.\start-dev.bat` and start developing! 🚀
