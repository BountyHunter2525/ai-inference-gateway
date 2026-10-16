# Deployment Guide

Quick guide to deploy NexusAI to various platforms.

---

## 🚀 Option 1: Render.com (Easiest, Free Tier)

### Step 1: Create Redis Service
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Redis"
3. Name it `nexusai-redis`
4. Select **Free tier**
5. Click "Create Redis"
6. Copy the **Internal Redis URL** (looks like `redis://red-xxx:6379`)

### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Fill in details:
   - **Name:** `nexusai-gateway`
   - **Environment:** Python 3
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Set Environment Variables
Click "Environment" and add:
```
REDIS_URL=<paste internal redis URL from step 1>
```

Optional (if you want real LLM responses):
```
HUGGINGFACE_API_TOKEN=hf_your_token
OPENAI_API_KEY=sk_your_key
```

### Step 4: Deploy!
1. Click "Create Web Service"
2. Wait 3-5 minutes for deployment
3. Access your app at `https://nexusai-gateway.onrender.com`

**That's it!** 🎉

---

## 🚂 Option 2: Railway.app (Also Easy)

1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Python and builds automatically
5. Click "Add Plugin" → "Redis"
6. Railway automatically sets `REDIS_URL` for you
7. Done! Access via the generated URL

---

## 💧 Option 3: DigitalOcean / AWS EC2 / Any VPS

### Prerequisites
- A server with Ubuntu 20.04+
- SSH access
- Domain name (optional)

### Step 1: Install Docker

```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone and Deploy

```bash
# Clone your repository
git clone https://github.com/BountyHunter2525/ai-inference-gateway.git
cd ai-inference-gateway

# Create .env file
nano backend/.env
# Add your environment variables

# Start services
docker compose up -d

# Check logs
docker compose logs -f
```

### Step 3: Setup Nginx (Optional - for custom domain)

```bash
# Install Nginx
sudo apt update
sudo apt install nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/nexusai
```

Paste this config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/nexusai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: SSL Certificate (Optional but recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🐳 Option 4: Docker Hub (For Sharing)

If you want to share your Docker image:

### Build and Push
```bash
# Login to Docker Hub
docker login

# Build image
docker build -t your-username/nexusai-gateway:latest ./backend

# Push to Docker Hub
docker push your-username/nexusai-gateway:latest
```

### Others can then run:
```bash
docker pull your-username/nexusai-gateway:latest
docker run -p 8000:8000 -e REDIS_URL=redis://localhost:6379 your-username/nexusai-gateway:latest
```

---

## 🔧 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No* | In-memory | Redis connection URL |
| `HUGGINGFACE_API_TOKEN` | No | - | HuggingFace API token |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `CACHE_MAX_ENTRIES` | No | 500 | Max cache entries before eviction |
| `SIMILARITY_THRESHOLD` | No | 0.92 | Minimum similarity for cache hit |
| `RATE_LIMIT_MAX_REQUESTS` | No | 100 | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | No | 60 | Rate limit window size |
| `VALID_API_KEYS` | No | dev-demo-key | Comma-separated API keys |

*Redis is optional - the app will use in-memory storage as fallback

---

## 📊 Monitoring Your Deployment

### Health Check
```bash
curl https://your-app-url.com/api/v1/health
```

### View Metrics
```bash
curl https://your-app-url.com/api/v1/metrics
```

### Check Cache Stats
```bash
curl https://your-app-url.com/api/v1/cache/stats \
  -H "X-API-Key: sk-nexus-dev-demo-key"
```

---

## 🐛 Troubleshooting

### App won't start
- Check logs: `docker compose logs`
- Verify Python version: `python --version` (need 3.11+)
- Ensure Redis is running: `docker compose ps`

### Can't connect to Redis
- Check `REDIS_URL` environment variable
- Test Redis connection: `redis-cli -u $REDIS_URL ping`
- App will work without Redis (uses in-memory fallback)

### Out of memory
- Reduce `CACHE_MAX_ENTRIES` in config
- Upgrade server RAM
- Enable Redis maxmemory-policy

### Slow responses
- Check if sentence-transformers model downloaded
- Verify Redis connection isn't timing out
- Monitor with `/api/v1/metrics` endpoint

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change default API keys in environment variables
- [ ] Enable HTTPS (use Certbot for free SSL)
- [ ] Set up firewall rules (only allow ports 80, 443, 22)
- [ ] Use strong Redis password (if exposed)
- [ ] Keep Docker images updated
- [ ] Enable rate limiting (already included)
- [ ] Set up log rotation
- [ ] Regular backups of Redis data

---

## 📈 Scaling Tips

If you get popular:

1. **Vertical Scaling** - Upgrade server RAM/CPU
2. **Redis Persistence** - Enable RDB snapshots
3. **Load Balancer** - Multiple app instances behind nginx
4. **CDN** - Use CloudFlare for static files
5. **Monitoring** - Add Prometheus + Grafana stack

---

## 💡 Pro Tips

- **Free Hosting:** Render.com and Railway.app both offer free tiers
- **Custom Domain:** Get free domain from Freenom or use .tech domain
- **Logs:** Always check logs first when debugging
- **Cost:** Redis is usually free for small projects
- **Updates:** Use `git pull && docker compose up --build -d` to update

---

## 📞 Need Help?

1. Check logs first: `docker compose logs -f`
2. Read error messages carefully
3. Google the error (StackOverflow is your friend!)
4. Open issue on GitHub if you find a bug

---

**Good luck with your deployment! 🚀**
