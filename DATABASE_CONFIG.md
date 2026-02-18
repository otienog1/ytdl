# Database Configuration Guide

## Environment Variables

The database configuration is now fully controlled by environment variables in `.env`:

### `MONGODB_URI`
The full MongoDB connection string.

**Local Development:**
```env
MONGODB_URI=mongodb://localhost:27017/ytdl_db
```

**Production (MongoDB Atlas):**
```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/ytdl_db
```

### `MONGODB_DB_NAME`
The database name to use when the URI doesn't specify one.

**Default:** `ytdl_db`

```env
MONGODB_DB_NAME=ytdl_db
```

## How It Works

1. **URI includes database name**: Uses the database from the URI
2. **URI doesn't include database name**: Falls back to `MONGODB_DB_NAME` setting

## Examples

### Example 1: URI with database name
```env
MONGODB_URI=mongodb://localhost:27017/my_custom_db
MONGODB_DB_NAME=ytdl_db  # Ignored - URI has database name
```
→ Uses database: `my_custom_db`

### Example 2: URI without database name
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=ytdl_db
```
→ Uses database: `ytdl_db`

### Example 3: Different database for testing
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=ytdl_db_test
```
→ Uses database: `ytdl_db_test`

## Connection Pool Settings

Both the FastAPI server and Celery worker use the same connection pool configuration:

- `maxPoolSize=50` - Maximum 50 connections per client
- `minPoolSize=10` - Maintain minimum 10 connections
- `maxIdleTimeMS=30000` - Close idle connections after 30 seconds
- `serverSelectionTimeoutMS=5000` - 5-second server selection timeout

These settings prevent the "max number of clients reached" error.

## Switching Between Local and Atlas

### Use Local MongoDB
```env
# .env
MONGODB_URI=mongodb://localhost:27017/ytdl_db
MONGODB_DB_NAME=ytdl_db
```

### Use MongoDB Atlas
```env
# .env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/ytdl_db
MONGODB_DB_NAME=ytdl_db
```

## Files Affected

1. **[settings.py](app/config/settings.py)** - Added `MONGODB_DB_NAME` setting
2. **[database.py](app/config/database.py)** - Uses `settings.MONGODB_DB_NAME` as fallback
3. **[tasks.py](app/queue/tasks.py)** - Celery worker uses `settings.MONGODB_DB_NAME` as fallback
4. **[.env](.env)** - Added `MONGODB_DB_NAME=ytdl_db`

## Benefits

✅ **Configurable**: Change database name without modifying code
✅ **Consistent**: Same database name used by API server and Celery worker
✅ **Flexible**: Easy to switch between development/staging/production databases
✅ **Clear**: Database name is explicit in configuration

## Migration Guide

If migrating from old configuration:

1. Add `MONGODB_DB_NAME=ytdl_db` to your `.env` file
2. Ensure `MONGODB_URI` points to correct server
3. Restart both backend server and Celery worker

No code changes needed - it's all in the `.env` file!
