# Deployment Guide: The Truthboard

Complete instructions for deploying to **Render** (backend) and **Vercel** (frontend) with minimal cost.

---

## Overview

- **Frontend**: Next.js 14 → **Vercel** (free tier)
- **Backend**: FastAPI → **Render** (free tier with PostgreSQL)
- **Database**: PostgreSQL → **Render** (free tier, 1 GB storage)
- **Total Cost**: **$0/month** (free tier)

---

## Part 1: Backend Deployment (Render)

### Prerequisites

1. Create **Render** account at https://render.com
2. Create **GitHub** account and push your repo there
3. Have your backend code ready in `/backend` directory

### Step 1: Create PostgreSQL Database

**In Render Dashboard:**

1. Click **New +** → **PostgreSQL**
2. **Configuration:**
   - Name: `truthboard-db`
   - Database: `truthboard`
   - User: `truthboard_user`
   - Region: Choose closest to users
   - PostgreSQL Version: 15
   - Plan: **Free**

3. Click **Create Database**
4. **Save the connection string** (looks like: `postgresql://user:password@host:5432/truthboard`)

### Step 2: Deploy Backend API

**In Render Dashboard:**

1. Click **New +** → **Web Service**
2. **Connect GitHub Repository:**
   - Click **Connect account**
   - Select your repository
   - Branch: `main`
   - Root Directory: `backend`

3. **Configuration:**
   - Name: `truthboard-api`
   - Environment: `Docker`
   - Plan: **Free**
   - Region: Same as database

4. **Environment Variables** (click **Advanced**):
   ```
   DATABASE_URL=<paste-postgresql-connection-string-from-step-1>
   ENABLE_SCHEDULER=false
   PYTHONUNBUFFERED=1
   ```

5. Click **Deploy**

**Wait 5-10 minutes for deployment to complete.**

### Step 3: Verify Backend

- Render will give you a URL like: `https://truthboard-api.onrender.com`
- Test: `https://truthboard-api.onrender.com/health`
- **Save this URL** for frontend configuration

### Important Notes:

- **Free tier sleeps after 15 min inactivity** → add to cron job to keep alive
- **No background scheduler** on free tier (set `ENABLE_SCHEDULER=false`)
- **1 GB database storage** - sufficient for ~5,000 events
- Add to `.env` or set in Render environment:
  ```
  ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
  ```

---

## Part 2: Frontend Deployment (Vercel)

### Prerequisites

1. Create **Vercel** account at https://vercel.com
2. Connect GitHub account to Vercel

### Step 1: Configure Frontend

**In `/frontend/.env.production`** (create this file):

```env
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

**Commit and push to GitHub:**

```bash
git add frontend/.env.production
git commit -m "Add production API configuration"
git push
```

### Step 2: Deploy to Vercel

**In Vercel Dashboard:**

1. Click **Add New** → **Project**
2. **Import Git Repository:**
   - Select your GitHub repository
   - Click **Import**

3. **Configure Project:**
   - Framework Preset: **Next.js**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **Environment Variables:**
   - `NEXT_PUBLIC_API_URL`: `https://truthboard-api.onrender.com`
   - `INTERNAL_API_URL`: `https://truthboard-api.onrender.com`

5. Click **Deploy**

**Wait 3-5 minutes for deployment.**

### Step 3: Verify Frontend

- Vercel will give you a URL like: `https://truthboard.vercel.app`
- Visit the URL and test:
  - Homepage loads political events
  - Developing page shows developing events
  - Search works
  - Stats page displays

### Step 4: Update Backend CORS

Go back to **Render Dashboard** → **truthboard-api** → **Environment**

Update:
```
ALLOWED_ORIGINS=https://truthboard.vercel.app
```

Click **Save changes** and Render will auto-redeploy.

---

## Part 3: Keep-Alive Strategy (Prevent Free Tier Sleeping)

### Option A: Render Cron Job (Recommended)

1. Create `render-cron.yml` in repository:

```yaml
services:
  - type: cron
    name: api-keep-alive
    schedule: "0 */14 * * *"  # Every 14 hours
    command: curl https://truthboard-api.onrender.com/health
```

### Option B: External Cron Service

Use **UptimeRobot** (free):

1. Go to https://uptimerobot.com
2. **Add Monitor:**
   - Name: Truthboard API
   - URL: `https://truthboard-api.onrender.com/health`
   - Interval: 30 minutes
   - Alert Contacts: Your email

---

## Part 4: Database Management

### Backup Data

From your local machine:

```bash
# Download database backup
pg_dump "postgresql://user:password@host:5432/truthboard" > backup.sql

# Restore if needed
psql "postgresql://user:password@host:5432/truthboard" < backup.sql
```

### Monitor Storage

- **Render Dashboard** → **PostgreSQL** instance → **Metrics**
- If approaching 1 GB:
  - Archive old events (older than 30 days)
  - Delete unimportant events with low confidence score

---

## Part 5: Configuration Reference

### Backend Environment Variables

```env
DATABASE_URL=postgresql://user:password@host:5432/truthboard
ALLOWED_ORIGINS=https://truthboard.vercel.app,http://localhost:3000
ENABLE_SCHEDULER=false
PYTHONUNBUFFERED=1
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
```

### Frontend Environment Variables

```env
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

---

## Part 6: Troubleshooting

### Backend returns 500 errors

1. Check Render logs: **Dashboard** → **truthboard-api** → **Logs**
2. Common issues:
   - Database connection string wrong
   - Database not ready yet (wait 5 min)
   - Missing environment variables

### Frontend shows "Failed to fetch from API"

1. Verify backend is running: `curl https://truthboard-api.onrender.com/health`
2. Check CORS: Backend's `ALLOWED_ORIGINS` must include your Vercel domain
3. Check frontend `.env.production`: Must match backend URL

### Slow API responses

1. Free tier is slow - normal behavior
2. Add keep-alive cron to prevent sleep
3. Consider upgrading to **$7/month** Render plan for better performance

### Database full (1 GB limit)

1. Archive old events:
   ```bash
   # Keep only recent 50 most important political events
   DELETE FROM events
   WHERE importance_score < 50
   AND last_seen < now() - interval '30 days'
   ```
2. Upgrade to paid PostgreSQL plan

---

## Part 7: Custom Domain Setup (Optional)

### Bind Vercel to Custom Domain

1. **In Vercel Dashboard:**
   - Project Settings → Domains
   - Add `yourdomain.com`

2. **Update DNS at registrar:**
   - Add CNAME: `yourdomain.com → truthboard.vercel.app`
   - Wait 24 hours for propagation

3. **SSL automatically enabled** (free via Let's Encrypt)

### Custom Domain for API (Optional)

Similar process for Render API at your registrar.

---

## Part 8: Monitoring & Maintenance

### Daily Tasks

- **Monitor uptime:** UptimeRobot dashboard
- **Check Vercel** for deployment errors: https://vercel.com/dashboard
- **Check Render logs** for backend errors: https://dashboard.render.com

### Weekly Tasks

- Check database size in Render
- Verify API response times are acceptable
- Review error logs for patterns

### Monthly Tasks

- Clean up old events if DB approaching limits
- Review cost (should be $0 on free tier)
- Consider upgrading if needed

---

## Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| **Vercel** (Frontend) | Free | $0 |
| **Render** (API) | Free | $0 |
| **Render** (PostgreSQL) | Free | $0 |
| **UptimeRobot** (Monitoring) | Free | $0 |
| **Total** | | **$0/month** |

**Optional Upgrades:**
- Render Web Service: $7/month (better performance)
- Render PostgreSQL: $15/month (10 GB storage)

---

## Deployment Checklist

### Before Deploying

- [ ] Update `ALLOWED_ORIGINS` in backend config
- [ ] Set `ENABLE_SCHEDULER=false` in backend
- [ ] Create `.env.production` in frontend
- [ ] Commit and push to GitHub
- [ ] Database URL ready to paste

### Render Deployment

- [ ] Create PostgreSQL database
- [ ] Note connection string
- [ ] Deploy Web Service with GitHub integration
- [ ] Set environment variables
- [ ] Test `/health` endpoint
- [ ] Save API URL

### Vercel Deployment

- [ ] Connect GitHub account
- [ ] Import project from GitHub
- [ ] Set environment variables
- [ ] Set root directory to `frontend`
- [ ] Deploy
- [ ] Test homepage loads

### Post-Deployment

- [ ] Update backend `ALLOWED_ORIGINS` with Vercel URL
- [ ] Verify frontend can fetch from backend
- [ ] Set up UptimeRobot keep-alive
- [ ] Test all pages: home, developing, conflicts, stats
- [ ] Test search functionality
- [ ] Monitor first 24 hours for errors

---

## Final URLs

After deployment:

- **Frontend**: `https://truthboard.vercel.app`
- **Backend API**: `https://truthboard-api.onrender.com`
- **API Health**: `https://truthboard-api.onrender.com/health`
- **API Docs**: `https://truthboard-api.onrender.com/docs`

---

## Questions?

1. Backend won't start → Check Render logs for specific error
2. Frontend shows blank page → Check browser console for API errors
3. Slow performance → Normal on free tier; use keep-alive cron
4. Database full → Delete old events or upgrade plan

**Total setup time: ~30 minutes**
