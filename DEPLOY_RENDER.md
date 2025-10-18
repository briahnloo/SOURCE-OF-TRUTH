# Deploy Truth Layer to Render.com (Free Tier)

This guide will help you deploy the Truth Layer MVP to Render.com's free tier, making it publicly accessible on the internet.

## Prerequisites

- GitHub repository: https://github.com/briahnloo/SOURCE-OF-TRUTH
- Render.com account (free): https://render.com

## Total Cost

- **Free for 90 days** (PostgreSQL free trial)
- **$7/month after** (PostgreSQL starter plan)
- Backend, Worker, Frontend remain **free forever**

## Step-by-Step Deployment

### Step 1: Create Render Account

1. Visit https://render.com
2. Click "Get Started"
3. Sign up with GitHub (recommended for easy deploys)
4. Verify your email

### Step 2: Create PostgreSQL Database

1. From Render Dashboard → **New** → **PostgreSQL**
2. Settings:
   - **Name**: `truthlayer-db`
   - **Database**: `truthlayer`
   - **User**: `truthlayer`
   - **Region**: Choose closest to your users
   - **Plan**: **Free** (expires after 90 days, then $7/month)
3. Click **Create Database**
4. **Copy** the **Internal Database URL** (starts with `postgresql://`)
   - Example: `postgresql://truthlayer:***@dpg-***-a.oregon-postgres.render.com/truthlayer_db`
   - Save this! You'll need it for all 3 services

### Step 3: Deploy Backend (FastAPI API)

1. From Dashboard → **New** → **Web Service**
2. **Connect Repository**:
   - Select **briahnloo/SOURCE-OF-TRUTH**
   - If not listed, click "Configure Account" to grant access
3. Settings:
   - **Name**: `truthlayer-backend`
   - **Region**: Same as database
   - **Root Directory**: `backend`
   - **Environment**: **Docker**
   - **Plan**: **Free**
4. **Advanced Settings**:
   - **Health Check Path**: `/health/ready`
   - **Auto-Deploy**: Yes
5. **Environment Variables** (click "Add Environment Variable"):
   ```
   DATABASE_URL = <paste your Internal Database URL from Step 2>
   ALLOWED_ORIGINS = https://truthlayer-frontend.onrender.com
   NEWSAPI_KEY = (leave empty or add if you have one)
   MEDIASTACK_KEY = (leave empty or add if you have one)
   DISCORD_WEBHOOK_URL = (leave empty or add Discord webhook)
   ```
6. Click **Create Web Service**
7. Wait 5-10 minutes for build to complete
8. **Copy your backend URL**: `https://truthlayer-backend.onrender.com`

### Step 4: Deploy Worker (Background Ingestion)

1. From Dashboard → **New** → **Background Worker**
2. **Connect Repository**:
   - Select **briahnloo/SOURCE-OF-TRUTH**
3. Settings:
   - **Name**: `truthlayer-worker`
   - **Region**: Same as database
   - **Root Directory**: `backend`
   - **Environment**: **Docker**
   - **Plan**: **Free**
4. **Start Command** (important!):
   ```
   python -m app.workers.scheduler
   ```
5. **Environment Variables**:
   ```
   DATABASE_URL = <same as backend>
   NEWSAPI_KEY = (same as backend)
   MEDIASTACK_KEY = (same as backend)
   DISCORD_WEBHOOK_URL = (same as backend)
   ```
6. Click **Create Background Worker**
7. Worker will start automatically

### Step 5: Deploy Frontend (Next.js UI)

1. From Dashboard → **New** → **Web Service**
2. **Connect Repository**:
   - Select **briahnloo/SOURCE-OF-TRUTH**
3. Settings:
   - **Name**: `truthlayer-frontend`
   - **Region**: Same as database
   - **Root Directory**: `frontend`
   - **Environment**: **Docker**
   - **Plan**: **Free**
4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL = https://truthlayer-backend.onrender.com
   ```
   (Use the URL from Step 3)
5. Click **Create Web Service**
6. Wait 5-10 minutes for build
7. **Your app is live!** Visit the URL shown (e.g., `https://truthlayer-frontend.onrender.com`)

---

## Verification Checklist

After all services deploy, verify:

### Backend Health

Visit: `https://truthlayer-backend.onrender.com/health`

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_events": 0,
  "total_articles": 0
}
```

### API Documentation

Visit: `https://truthlayer-backend.onrender.com/docs`

Should show interactive Swagger UI

### Frontend UI

Visit: `https://truthlayer-frontend.onrender.com`

Should show:
- ✅ Hero section: "Welcome, Seekers of Knowledge"
- ✅ Navigation working
- ✅ No API errors

### Worker Logs

In Render Dashboard:
1. Go to `truthlayer-worker` service
2. Click **Logs** tab
3. Should see:
   ```
   🚀 Truth Layer Worker Starting...
   Running initial ingestion...
   📥 Step 1: Fetching articles from all sources...
   ```

---

## Important Notes

### Free Tier Limitations

1. **Services sleep after 15 minutes of inactivity**
   - First request after sleep takes 30-60 seconds
   - Subsequent requests are fast
   - **Workaround**: Use UptimeRobot (free) to ping every 5 minutes

2. **Database free for 90 days**
   - After 90 days: $7/month or data is deleted
   - Set a calendar reminder to upgrade or backup!

3. **Build minutes** (500/month free)
   - Each deployment uses ~5-10 minutes
   - ~50-100 deploys/month on free tier

### Performance Expectations

- **First load**: 30-60 seconds (service waking up)
- **Normal load**: 1-3 seconds
- **API latency**: 200-500ms
- **Ingestion**: Every 15 minutes (as configured)

### Troubleshooting

**Service won't start:**
- Check Logs in Render dashboard
- Verify DATABASE_URL is correct
- Ensure all env vars are set

**Database connection errors:**
- Verify database is "Available" (not "Creating")
- Check Internal URL is used (not External)
- Confirm backend and database are in same region

**Frontend can't reach backend:**
- Verify NEXT_PUBLIC_API_URL matches backend URL exactly
- Check ALLOWED_ORIGINS includes frontend URL
- Rebuild frontend service after fixing

**Worker not ingesting:**
- Check worker logs
- Verify DATABASE_URL is set
- Look for API rate limit errors (normal for free APIs)

---

## Updating After Changes

### Automatic Deployment

Render auto-deploys on git push:

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push origin main

# Render automatically rebuilds and deploys!
# Check dashboard for build progress
```

### Manual Rebuild

In Render Dashboard:
1. Go to service (backend/worker/frontend)
2. Click **Manual Deploy** → **Deploy latest commit**

---

## Adding a Custom Domain (Optional)

### If You Own a Domain

1. **In Render** (Frontend service):
   - Settings → Custom Domains
   - Add `truthlayer.com` and `www.truthlayer.com`
   - Render provides CNAME targets

2. **In Your Domain Registrar**:
   ```
   CNAME: www.truthlayer.com → truthlayer-frontend.onrender.com
   CNAME: truthlayer.com → truthlayer-frontend.onrender.com
   ```
   (Or use A record if required)

3. **SSL**: Automatically provisioned by Render (free)

4. **Update Environment Variables**:
   - Backend: `ALLOWED_ORIGINS=https://truthlayer.com,https://www.truthlayer.com`
   - Frontend: Update if needed

### Cost

- Domain registration: ~$10-15/year
- SSL: Free (included with Render)

---

## Monitoring Setup

### UptimeRobot (Keep Services Awake)

1. Sign up at https://uptimerobot.com (free)
2. Add Monitor:
   - **Type**: HTTP(S)
   - **URL**: `https://truthlayer-frontend.onrender.com`
   - **Interval**: 5 minutes
3. Add second monitor for backend health:
   - **URL**: `https://truthlayer-backend.onrender.com/health`

This pings your services every 5 minutes, preventing sleep!

### Sentry Error Tracking (Optional)

1. Sign up at https://sentry.io (free tier)
2. Create project for "FastAPI"
3. Copy DSN
4. Add to backend env vars: `SENTRY_DSN=https://...`
5. Update `backend/pyproject.toml`: add `sentry-sdk[fastapi]`
6. Update `backend/app/main.py`: initialize Sentry

---

## Scaling & Costs

### As You Grow

| Users/Day | Plan | Cost | What Changes |
|-----------|------|------|--------------|
| < 1,000 | Free | $0-7/mo | Current setup |
| 1,000-10,000 | Starter | $14/mo | Upgrade frontend to Starter |
| 10,000+ | Standard | $50-100/mo | Multiple instances, larger DB |

### When to Upgrade

- Frontend sleeping is annoying users → Upgrade to Starter ($7/month)
- API slow (>1s) → Upgrade backend to Starter
- Database > 1GB → Upgrade to PostgreSQL Standard ($20/month)

---

## Backup Strategy

### Automatic Backups (Included)

- Render takes daily PostgreSQL backups (retained 7 days on free tier)
- Restore via dashboard: Database → Backups → Restore

### Manual Backup

```bash
# Download backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore backup
psql $DATABASE_URL < backup_20251018.sql
```

---

## Success Checklist

After deployment, you should have:

- ✅ Public URL accessible from anywhere
- ✅ HTTPS enabled (green padlock in browser)
- ✅ Database persisting data
- ✅ Worker ingesting every 15 minutes
- ✅ All 4 pages working (Confirmed, Developing, Underreported, Stats)
- ✅ API docs accessible
- ✅ RSS feed working
- ✅ Auto-deployment on git push

---

## Support

- **Render Docs**: https://render.com/docs
- **Community Forum**: https://community.render.com
- **Status**: https://status.render.com

## Next Steps

After successful deployment:

1. Share your live URL!
2. Monitor for 24 hours to ensure stability
3. Set up UptimeRobot to prevent sleep
4. Add custom domain (optional)
5. Promote on social media, Hacker News, Reddit!

**Your Truth Layer will be live for the world to use!** 🌍

