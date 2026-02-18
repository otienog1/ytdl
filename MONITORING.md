# Monitoring Guide

## Metrics Endpoint

Access Prometheus metrics at: `http://localhost:3001/metrics`

## Available Metrics

### Download Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `downloads_total` | Counter | Total download requests (labels: status, provider) |
| `downloads_in_progress` | Gauge | Currently active downloads |
| `download_duration_seconds` | Histogram | Time to download videos |

### Storage Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `storage_uploads_total` | Counter | Total file uploads (labels: provider, status) |
| `storage_upload_duration_seconds` | Histogram | Upload duration by provider |
| `storage_usage_bytes` | Gauge | Current storage usage by provider |
| `storage_file_count` | Gauge | Number of files by provider |

### Error Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `errors_total` | Counter | Total errors (labels: error_code, error_type) |

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | HTTP requests (labels: method, endpoint, status) |
| `http_request_duration_seconds` | Histogram | Request duration |

### YouTube Service Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `youtube_api_calls_total` | Counter | YouTube API calls (labels: operation, status) |
| `youtube_api_duration_seconds` | Histogram | API call duration |

### Celery Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `celery_tasks_total` | Counter | Celery tasks (labels: task_name, status) |
| `celery_task_duration_seconds` | Histogram | Task execution time |
| `celery_queue_length` | Gauge | Tasks in queue |

## Useful Queries

### Download success rate
```promql
rate(downloads_total{status="success"}[5m]) / rate(downloads_total[5m])
```

### Storage usage percentage
```promql
(storage_usage_bytes / (5 * 1024 * 1024 * 1024)) * 100
```

### Error rate
```promql
rate(errors_total[5m])
```

### p95 download time
```promql
histogram_quantile(0.95, rate(download_duration_seconds_bucket[5m]))
```

## Integration Status

✅ Core metrics infrastructure
✅ HTTP request tracking via middleware
✅ All metrics defined and accessible at /metrics
✅ YouTube service metrics integration
✅ Storage service metrics integration
✅ Storage tracker metrics integration

### Completed Integrations

- **YouTube Service**:
  - `get_video_info()` - Tracks duration and success/failure
  - `download_video_sync()` - Tracks download duration and success/failure

- **Storage Service**:
  - `_upload_to_gcs()` - Tracks GCS upload duration and success/failure
  - `_upload_to_azure()` - Tracks Azure upload duration and success/failure
  - `_upload_to_s3()` - Tracks S3 upload duration and success/failure

- **Storage Tracker**:
  - `add_file_usage()` - Updates storage_usage_bytes and storage_file_count gauges
  - `remove_file_usage()` - Updates storage_usage_bytes and storage_file_count gauges

## TODO: Optional Enhancements

The following integrations are optional for future implementation:
- [ ] Add Celery task metrics (if using Celery)
- [ ] Create background job for metric updates (if needed)
- [ ] Create Grafana dashboard configuration
