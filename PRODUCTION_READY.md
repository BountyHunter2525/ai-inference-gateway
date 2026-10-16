# 🚀 Production Deployment Checklist

Making NexusAI production-ready with Redis and best practices.

---

## ✅ Pre-Deployment Checklist

### 1. Install Redis (Required)

**Windows:**
- Download Memurai: https://www.memurai.com/get-memurai
- Install and verify it's running on port 6379
- See `INSTALL_REDIS.md` for detailed instructions

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Mac
brew install redis
brew services start redis
```

### 2. Update Configuration

**Copy production config:**
```bash
cd backend
cp .env.production .env
```

**Edit `.env` and change:**
- `ADMIN_API_KEY` → Use a strong random key
- `VALID_API_KEYS` → Your actual production API keys
- `REDIS_URL` → Your Redis connection string
- `DEBUG=False` → Keep false in production

**Generate secure keys:**
```bash
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### 3. Security Hardening

**✅ Change default API keys**
```
❌ sk-nexus-dev-demo-key
✅ sk-prod-e4f3a2d1b9c8f7e6a5d4c3b2a1f0e9d8
```

**✅ Use strong admin key**
```
❌ sk-nexus-admin-master-key  
✅ sk-admin-8f7e6d5c4b3a2e1d0c9b8a7f6e5d4c3b
```

**✅ Enable HTTPS** (use Nginx + Let's Encrypt)

**✅ Configure CORS** properly in production:
```python
# In main.py, update allow_origins:
allow_origins=["https://yourdomain.com"]  # Not "*"
```

### 4. Performance Optimization

**✅ Redis Configuration**
```bash
# In redis.conf (Linux/Mac)
maxmemory 512mb
maxmemory-policy allkeys-lru
```

**✅ Increase cache size**
```bash
# In .env
CACHE_MAX_ENTRIES=5000  # For production load
```

**✅ Adjust rate limits**
```bash
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_WINDOW_SECONDS=60
```

### 5. Monitoring Setup

**✅ Prometheus metrics available at:**
```
http://your-server:8000/api/v1/metrics
```

**✅ Set up Prometheus + Grafana:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nexusai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics'
```

**✅ Health check endpoint:**
```bash
curl http://your-server:8000/api/v1/health
```

---

## 🔥 Production Deployment

### Option 1: Render.com (Easiest)

1. **Push to GitHub** (done ✓)
2. **Sign up at render.com**
3. **Create Redis service:**
   - Click "New +" → Redis
   - Plan: Starter (Free)
   - Copy the Internal Redis URL

4. **Create Web Service:**
   - Click "New +" → Web Service
   - Connect GitHub repo
   - Settings:
     - Build: `cd backend && pip install -r requirements.txt`
     - Start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     ```
     REDIS_URL=<paste from step 3>
     ADMIN_API_KEY=<your secure key>
     VALID_API_KEYS=<your keys>
     DEBUG=False
     ```

5. **Deploy!** Takes 3-5 minutes

### Option 2: VPS (DigitalOcean, AWS, etc.)

```bash
# SSH into your server
ssh user@your-server-ip

# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip redis-server nginx

# Clone repo
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway/backend

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.production .env
nano .env  # Edit with your settings

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Run with systemd (production)
sudo nano /etc/systemd/system/nexusai.service
```

**systemd service file:**
```ini
[Unit]
Description=NexusAI Gateway
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ai-inference-gateway/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start nexusai
sudo systemctl enable nexusai
sudo systemctl status nexusai
```

**Setup Nginx reverse proxy:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 🧪 Post-Deployment Testing

### 1. Verify Redis Connection

```bash
curl http://your-domain/api/v1/health
```

Should show:
```json
{
  "status": "healthy",
  "backend_storage": "REDIS",  // ✅ Not IN_MEMORY
  "embedder_ready": true
}
```

### 2. Test Cache Persistence

```bash
# Make a query
curl -X POST http://your-domain/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"prompt":"test","provider":"mock"}'

# Restart server
sudo systemctl restart nexusai

# Query again - should be CACHE HIT
curl -X POST http://your-domain/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"prompt":"test","provider":"mock"}'
```

### 3. Load Testing

```bash
# Install hey (load testing tool)
brew install hey  # Mac
# or download from: https://github.com/rakyll/hey

# Test with 100 requests
hey -n 100 -c 10 \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -m POST \
  -d '{"prompt":"test","provider":"mock"}' \
  http://your-domain/api/v1/infer
```

### 4. Monitor Metrics

```bash
curl http://your-domain/api/v1/metrics | grep nexusai
```

---

## 📊 Production Metrics to Watch

**Key Metrics:**
- `nexusai_cache_hits_total` - Should be high!
- `nexusai_cache_misses_total` - Should be lower
- `nexusai_latency_hit_seconds` - Should be ~5ms
- `nexusai_latency_miss_seconds` - Should be ~500ms
- `nexusai_rate_limit_rejected_total` - Watch for abuse

**Set up alerts for:**
- Cache hit ratio drops below 60%
- Error rate above 1%
- High memory usage (>80%)
- Redis connection failures

---

## 🔒 Security Best Practices

### ✅ Implemented
- API key authentication
- Rate limiting (100 req/min per key)
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention (no SQL used)
- Audit logging

### ⚠️ Additional Recommendations
1. **Use secrets manager** (AWS Secrets Manager, HashiCorp Vault)
2. **Enable request logging** (but sanitize sensitive data)
3. **Implement IP whitelisting** if possible
4. **Regular security updates:** `pip install --upgrade -r requirements.txt`
5. **Monitor for abuse** via audit logs
6. **Backup Redis data** regularly

---

## 💾 Backup & Recovery

### Redis Backup

**Enable RDB snapshots:**
```bash
# In redis.conf
save 900 1      # Save after 900s if 1 key changed
save 300 10     # Save after 300s if 10 keys changed
save 60 10000   # Save after 60s if 10000 keys changed
```

**Manual backup:**
```bash
redis-cli BGSAVE
# Backup file: /var/lib/redis/dump.rdb
```

### Application Backup

**Backup checklist:**
- ✅ Redis dump.rdb file
- ✅ Environment configuration (.env)
- ✅ Custom model files (if any)
- ✅ Audit logs

---

## 📈 Scaling Strategies

### Vertical Scaling (Single Server)
- Increase RAM (cache size)
- Faster CPU (ML inference)
- SSD storage (Redis persistence)

### Horizontal Scaling (Multiple Servers)
1. **Load balancer** (Nginx, HAProxy)
2. **Shared Redis** (all servers connect to same Redis)
3. **Redis Cluster** (for huge cache)
4. **Container orchestration** (Kubernetes)

---

## 🎯 Performance Benchmarks

**Expected performance with Redis:**

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Cache Hit Ratio | >70% | >80% | >90% |
| Cache Hit Latency | <10ms | <5ms | <3ms |
| Cache Miss Latency | <1000ms | <500ms | <200ms |
| Throughput | >100 req/s | >500 req/s | >1000 req/s |
| Error Rate | <1% | <0.1% | <0.01% |

---

## ✅ Production Checklist

Before going live:

- [ ] Redis installed and running
- [ ] Production .env configured
- [ ] Default API keys changed
- [ ] HTTPS enabled
- [ ] CORS configured properly
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Health checks working
- [ ] Backup strategy in place
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## 🆘 Troubleshooting Production Issues

### Issue: High memory usage
**Solution:** Reduce `CACHE_MAX_ENTRIES` or enable Redis `maxmemory-policy`

### Issue: Slow responses
**Solution:** Check Redis latency, increase cache size, optimize queries

### Issue: Cache not persisting
**Solution:** Verify Redis RDB/AOF persistence is enabled

### Issue: Too many rate limit rejections
**Solution:** Increase `RATE_LIMIT_MAX_REQUESTS` or identify abuse

---

**Your application is now production-ready! 🚀**

Monitor metrics, watch logs, and optimize based on real usage patterns.
