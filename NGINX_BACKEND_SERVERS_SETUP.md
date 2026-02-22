# Nginx Setup for Backend Servers (GCP & AWS)

## ⚠️ Important: This is OPTIONAL

The backend servers (GCP and AWS) **don't need nginx** for the load balancer setup to work. The load balancer on `ytd.timobosafaris.com` handles all incoming traffic and proxies directly to backend port 3001.

**Only install nginx on backend servers if you want:**
- Direct access to each server (bypassing load balancer)
- SSL on individual servers
- Local monitoring/debugging
- Nginx caching or other features

---

## Architecture Comparison

### Without Nginx on Backend Servers (Recommended for Load Balanced Setup)

```
Internet → ytd.timobosafaris.com (Nginx LB)
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
127.0.0.1  34.57.68.120  13.60.71.187
:3001      :3001         :3001
(Direct)   (Direct)      (Direct)
```

**Pros:**
- ✅ Simpler setup
- ✅ Fewer moving parts
- ✅ Lower memory usage
- ✅ Backend only needs Python/Uvicorn

**Cons:**
- ❌ Can't access individual servers with SSL
- ❌ No nginx features (caching, rate limiting) per server

---

### With Nginx on Backend Servers (Optional)

```
Internet → ytd.timobosafaris.com (Nginx LB)
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
127.0.0.1  34.57.68.120  13.60.71.187
:80        :80           :80
(Nginx)    (Nginx)       (Nginx)
  ↓          ↓             ↓
127.0.0.1  127.0.0.1     127.0.0.1
:3001      :3001         :3001
(Uvicorn)  (Uvicorn)     (Uvicorn)
```

**Pros:**
- ✅ Can access servers directly with SSL
- ✅ Individual server monitoring
- ✅ Nginx features per server

**Cons:**
- ❌ Extra complexity
- ❌ More memory usage
- ❌ Another service to maintain

---

## Recommended Setup

**For your multi-server load balanced setup, you DON'T need nginx on GCP/AWS servers.**

Just ensure:
1. Backend running on port 3001
2. Firewall allows port 3001
3. Load balancer can reach backends

However, if you still want nginx for direct access or monitoring, continue below.

---

## Installing Nginx on Backend Servers (Optional)

### On GCP Server (34.57.68.120)

```bash
# SSH to GCP server
ssh admin@34.57.68.120

# Install nginx
sudo apt update
sudo apt install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/ytd-backend
```

Paste contents from [nginx-gcp-server.conf](nginx-gcp-server.conf).

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ytd-backend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Test
curl http://localhost/health
curl http://34.57.68.120/health
```

### On AWS Server (13.60.71.187)

```bash
# SSH to AWS server
ssh admin@13.60.71.187

# Install nginx
sudo apt update
sudo apt install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/ytd-backend
```

Paste contents from [nginx-aws-server.conf](nginx-aws-server.conf).

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ytd-backend /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Test
curl http://localhost/health
curl http://13.60.71.187/health
```

---

## Update Load Balancer to Proxy to Nginx (If You Installed It)

If you install nginx on backend servers, update the load balancer upstream:

### On ytd.timobosafaris.com

Edit `/etc/nginx/sites-available/ytd`:

**Change from (direct to backend):**
```nginx
upstream ytd_backend {
    least_conn;
    server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;
    server 34.57.68.120:3001 max_fails=3 fail_timeout=30s;  # Port 3001
    server 13.60.71.187:3001 max_fails=3 fail_timeout=30s;  # Port 3001
    keepalive 32;
}
```

**To (via nginx):**
```nginx
upstream ytd_backend {
    least_conn;
    server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;  # Local still direct
    server 34.57.68.120:80 max_fails=3 fail_timeout=30s;   # Via nginx
    server 13.60.71.187:80 max_fails=3 fail_timeout=30s;   # Via nginx
    keepalive 32;
}
```

Reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**Note:** This is NOT recommended unless you have a specific reason. Direct connection to port 3001 is simpler and more efficient.

---

## Firewall Configuration

### If NOT Using Nginx on Backend Servers (Recommended)

Keep port 3001 open:
```bash
# On GCP and AWS servers
sudo ufw allow 3001/tcp
sudo ufw reload
```

### If Using Nginx on Backend Servers

Close port 3001, open port 80:
```bash
# On GCP and AWS servers
sudo ufw delete allow 3001/tcp  # Close direct access
sudo ufw allow 80/tcp           # Allow nginx
sudo ufw reload
```

---

## Testing

### Test Direct Backend Access (Without Nginx)

```bash
curl http://34.57.68.120:3001/api/health/
curl http://13.60.71.187:3001/api/health/
```

### Test Via Nginx (If Installed)

```bash
curl http://34.57.68.120/health
curl http://13.60.71.187/health
```

### Test Through Load Balancer

```bash
curl https://ytd.timobosafaris.com/health
```

All should return same JSON response ✅

---

## Monitoring Backends (If Nginx Installed)

### Check Nginx Status on Backend Servers

```bash
# On GCP server
curl http://localhost:8080/nginx_status

# On AWS server
curl http://localhost:8080/nginx_status
```

**Output:**
```
Active connections: 3
server accepts handled requests
 123 123 456
Reading: 0 Writing: 1 Waiting: 2
```

---

## When to Use Nginx on Backend Servers

### Use Cases for Nginx on Backends:

1. **Direct SSL Access to Each Server**
   - Want to access individual servers with HTTPS
   - Each server has its own subdomain (e.g., `gcp.ytd.timobosafaris.com`)

2. **Individual Rate Limiting**
   - Need different rate limits per server
   - Want to protect each server independently

3. **Caching on Each Server**
   - Want to cache responses locally on each server
   - Reduce backend load

4. **Advanced Logging**
   - Need detailed request logs per server
   - Want to analyze traffic patterns per server

5. **Static File Serving**
   - Each server serves static files directly
   - Nginx handles static content more efficiently

### Don't Use Nginx on Backends If:

1. ❌ **Simple Load Balanced Setup** (your current setup)
   - Load balancer handles all traffic
   - Backends just process requests
   - **This is your use case!**

2. ❌ **Want to Keep It Simple**
   - Fewer services to maintain
   - Lower memory usage
   - Easier debugging

3. ❌ **Backends Are Private**
   - Only accessible via load balancer
   - No direct public access needed

---

## Recommendation for Your Setup

**Don't install nginx on GCP/AWS servers.**

Your setup is optimal as-is:
- ✅ Load balancer (ytd.timobosafaris.com) handles SSL, routing, failover
- ✅ Backend servers (GCP, AWS) just run the Python API on port 3001
- ✅ Simple, efficient, easy to maintain

**Only add nginx to backend servers if you have a specific need that requires it.**

---

## Summary

| Feature | Without Nginx on Backends | With Nginx on Backends |
|---------|---------------------------|------------------------|
| Load balancing | ✅ Works perfectly | ✅ Works perfectly |
| SSL termination | ✅ At load balancer | ✅ At LB + each server |
| Direct server access | ⚠️ HTTP only (port 3001) | ✅ HTTP/HTTPS (port 80/443) |
| Complexity | ✅ Simple | ❌ More complex |
| Memory usage | ✅ Lower | ❌ Higher |
| Maintenance | ✅ Easier | ❌ More services |
| **Recommended for your setup** | ✅ **YES** | ❌ No |

**Conclusion:** Keep your backend servers simple - just Python/Uvicorn on port 3001. The load balancer handles everything else! 🚀
