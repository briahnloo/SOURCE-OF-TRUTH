# Deployment Guide: Ground Truth

This guide walks you through deploying Ground Truth to production using:
- **Backend + Database**: Render.com (free tier)
- **Frontend**: Vercel (as "groundtruth")

**Total Time**: ~30-45 minutes  
**Cost**: Free (with some limitations)

---

## Prerequisites

- [x] GitHub account linked (yours: @briahnloo)
- [x] Code pushed to GitHub repository
- [ ] Render.com account (sign up with GitHub)
- [ ] Vercel account (sign up with GitHub)

---

## Part 1: Deploy Backend to Render

### Step 1: Sign Up & Connect Repository

1. Go to **https://render.com**
2. Click **"Get Started"** or **"Sign In"**
3. Choose **"Sign in with GitHub"**
4. Authorize Render to access your GitHub account

### Step 2: Create New Blueprint

1. Once logged in, click the **"New +"** button (top right)
2. Select **"Blueprint"** from the dropdown
3. Click **"Connect Account"** if prompted to connect GitHub
4. Find and select your repository (the one at your current path)
5. Click **"Connect"**

### Step 3: Review Blueprint Configuration

Render will automatically detect the `render.yaml` file and show you:

**Database:**
- Name: `truthlayer-db`
- Type: PostgreSQL
- Plan: Free ($0/month)

**Services:**
- `truthlayer-backend` (Web Service - API)
- `truthlayer-worker` (Background Worker)
- `truthlayer-frontend` (Web Service - we'll delete this since we're using Vercel)

### Step 4: Configure Environment Variables

Before deploying, you'll be prompted to fill in environment variables:

**For `truthlayer-backend` service:**
- `DATABASE_URL`: *(Auto-filled from database)* - Leave as is
- `ALLOWED_ORIGINS`: Pre-set to `https://groundtruth.vercel.app` - Leave as is for now
- `NEWSAPI_KEY`: Leave empty (optional)
- `MEDIASTACK_KEY`: Leave empty (optional)
- `DISCORD_WEBHOOK_URL`: Leave empty (optional)

**For `truthlayer-worker` service:**
- `DATABASE_URL`: *(Auto-filled from database)* - Leave as is
- `NEWSAPI_KEY`: Leave empty (optional)
- `MEDIASTACK_KEY`: Leave empty (optional)
- `DISCORD_WEBHOOK_URL`: Leave empty (optional)

### Step 5: Deploy

1. Click **"Apply"** at the bottom of the page
2. Render will start creating:
   - PostgreSQL database
   - Backend API service
   - Worker service
   - Frontend service (ignore this)

**This will take 5-10 minutes.** You can watch the build logs in real-time.

### Step 6: Get Your Backend URL

1. Once deployed, go to the **Dashboard**
2. Click on the **`truthlayer-backend`** service
3. At the top, you'll see the URL: `https://truthlayer-backend.onrender.com`
4. **Copy this URL** - you'll need it for Vercel

### Step 7: Test Backend Health

1. Visit: `https://truthlayer-backend.onrender.com/health`
2. You should see:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "total_events": 0,
     "total_articles": 0
   }
   ```

If you see this, your backend is live! ✅

### Step 8: Delete Frontend Service (Optional)

Since we're using Vercel for the frontend:
1. Go to Render Dashboard
2. Click on `truthlayer-frontend` service
3. Go to **Settings** (bottom of left sidebar)
4. Scroll down and click **"Delete Web Service"**
5. Confirm deletion

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Sign Up & Connect Repository

1. Go to **https://vercel.com**
2. Click **"Sign Up"** or **"Log In"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub account

### Step 2: Import Project

1. Once logged in, click **"Add New..."** button (top right)
2. Select **"Project"**
3. You'll see a list of your GitHub repositories
4. Find your repository and click **"Import"**

### Step 3: Configure Project

**Important**: Vercel needs to know your frontend is in a subdirectory.

1. **Project Name**: Enter `groundtruth`
2. **Framework Preset**: Should auto-detect as "Next.js" ✅
3. **Root Directory**: Click **"Edit"** and select `frontend` from the dropdown
4. **Build and Output Settings**: 
   - Build Command: `npm run build` *(auto-filled)*
   - Output Directory: `.next` *(auto-filled)*
   - Install Command: `npm install` *(auto-filled)*

### Step 4: Add Environment Variables

Still on the configuration page, scroll down to **"Environment Variables"**:

1. Click **"Add"**
2. **Name**: `NEXT_PUBLIC_API_URL`
3. **Value**: Paste your Render backend URL from Part 1, Step 6
   - Example: `https://truthlayer-backend.onrender.com`
4. **Environment**: Leave all checked (Production, Preview, Development)

### Step 5: Deploy

1. Click **"Deploy"** button
2. Vercel will:
   - Clone your repository
   - Install dependencies
   - Build your Next.js app
   - Deploy to their CDN

**This takes 2-5 minutes.** You can watch the build logs.

### Step 6: Get Your Frontend URL

Once deployed, you'll see a success screen with:
- **Production URL**: `https://groundtruth.vercel.app`
- You can click **"Visit"** to see your live site!

### Step 7: Test Frontend

1. Visit `https://groundtruth.vercel.app`
2. You should see the Ground Truth homepage
3. The "Developing" tab should show events (if the worker has run)

**Note**: On first load, the backend may take 30-60 seconds to wake up (Render free tier spins down after inactivity). This is normal!

---

## Part 3: Verify Integration

### Final Checks

- [ ] Backend health check works: `https://truthlayer-backend.onrender.com/health`
- [ ] Frontend loads: `https://groundtruth.vercel.app`
- [ ] Homepage shows stats (may be 0 initially)
- [ ] Navigation works (Developing, Underreported, Conflicts tabs)
- [ ] Stats page loads: `https://groundtruth.vercel.app/stats`

### Common Issues

**Issue**: Frontend shows "Failed to fetch" errors
- **Solution**: Check that `NEXT_PUBLIC_API_URL` in Vercel matches your Render backend URL exactly
- Go to Vercel → Project → Settings → Environment Variables
- Update the value and redeploy

**Issue**: CORS errors in browser console
- **Solution**: Update `ALLOWED_ORIGINS` in Render
- Go to Render → `truthlayer-backend` → Environment
- Update `ALLOWED_ORIGINS` to match your Vercel URL
- Save (service will auto-redeploy)

**Issue**: Backend is slow (30+ seconds to respond)
- **Explanation**: Render free tier spins down after 15 minutes of inactivity
- First request wakes it up (slow), subsequent requests are fast
- **Solution**: Upgrade to a paid plan for 24/7 uptime, or use a service like UptimeRobot to ping your backend every 10 minutes

**Issue**: No events showing
- **Explanation**: The background worker runs every 15 minutes
- Initial deployment may take time to populate data
- Check worker logs: Render → `truthlayer-worker` → Logs
- Manually trigger once: `python -m app.workers.run_once` (see Render Shell)

---

## Part 4: Optional Enhancements

### Add Custom Domain

If you want `groundtruth.com` instead of `groundtruth.vercel.app`:

1. **Purchase a domain** from a registrar (Namecheap, Google Domains, Cloudflare, etc.)
2. In **Vercel**:
   - Go to your project → Settings → Domains
   - Click "Add"
   - Enter your domain (e.g., `groundtruth.com`)
   - Follow DNS configuration instructions
3. In **Render**:
   - Update `ALLOWED_ORIGINS` to include your custom domain
   - Example: `https://groundtruth.com,https://groundtruth.vercel.app`

### Add API Keys (Optional)

The system works with free sources, but you can add premium sources:

**NewsAPI** (60 requests/day free):
1. Sign up at https://newsapi.org
2. Get API key
3. In Render → `truthlayer-backend` → Environment
4. Update `NEWSAPI_KEY` with your key

**MediaStack** (100 requests/month free):
1. Sign up at https://mediastack.com
2. Get API key
3. In Render → `truthlayer-backend` → Environment
4. Update `MEDIASTACK_KEY` with your key

### Set Up Monitoring

**Uptime Monitoring** (keep backend awake):
1. Sign up for UptimeRobot (free)
2. Add monitor: `https://truthlayer-backend.onrender.com/health`
3. Set interval to 10 minutes
4. This prevents the free tier from spinning down

**Discord Alerts**:
1. Create a Discord webhook
2. In Render → `truthlayer-backend` → Environment
3. Update `DISCORD_WEBHOOK_URL` with webhook URL
4. You'll get alerts for errors and ingestion failures

---

## Maintenance

### View Logs

**Backend logs**:
- Render → `truthlayer-backend` → Logs

**Worker logs**:
- Render → `truthlayer-worker` → Logs

**Frontend logs**:
- Vercel → Project → Deployments → Click latest → View Function Logs

### Redeploy

**Backend/Worker**:
- Any push to `main` branch auto-deploys
- Or: Render → Service → Manual Deploy → "Deploy latest commit"

**Frontend**:
- Any push to `main` branch auto-deploys
- Or: Vercel → Project → Deployments → "Redeploy"

### Database Management

**View database**:
- Render → `truthlayer-db` → Info
- Use connection string with a PostgreSQL client (pgAdmin, TablePlus, etc.)

**Backup**:
- Render free tier: Manual backups only
- Use `pg_dump` with connection string

---

## Support

- **Documentation**: See `/docs` folder in repository
- **Issues**: Open issue on GitHub
- **Render Support**: https://render.com/docs
- **Vercel Support**: https://vercel.com/docs

---

## Summary

You've successfully deployed **Ground Truth**! 🎉

- **Frontend**: https://groundtruth.vercel.app
- **Backend API**: https://truthlayer-backend.onrender.com
- **Health Check**: https://truthlayer-backend.onrender.com/health

Your site is now live and automatically updating every 15 minutes with the latest verified news.

