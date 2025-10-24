# 🚀 Truthboard - Exact Deployment Guide

**Complete deployment with exact variable names, URLs, and values specified**

---

## 📋 What This Guide Contains

This guide shows **exactly** what to put where, with:
- Exact variable names and their values
- Exact URLs for your backend and frontend
- Your PostgreSQL connection string used throughout
- Step-by-step Render and Vercel UI instructions
- Exact copy-paste commands for each step

---

## 🎯 Your Exact URLs After Deployment

These are the URLs you'll have after following this guide:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | `https://truthboard.vercel.app` | What users visit |
| **Backend API** | `https://truthboard-api.onrender.com` | Where frontend sends requests |
| **API Health Check** | `https://truthboard-api.onrender.com/health` | Verify backend is running |
| **API Docs** | `https://truthboard-api.onrender.com/docs` | Interactive API documentation |

---

## 🔑 Your Exact Database Connection String

This is the PostgreSQL connection string Render will give you:

```
postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer
```

**Breaking this down:**
- **Username**: `truthlayer`
- **Password**: `hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM`
- **Host**: `dpg-d3qr8o56ubrc73868q20-a`
- **Port**: `5432` (default, not shown in URL)
- **Database Name**: `truthlayer`

This exact string will be used as the value for:
- **In Render Backend**: `DATABASE_URL` environment variable

---

## 📊 Total Cost

| Item | Cost |
|------|------|
| Vercel (Frontend) | **$0/month** |
| Render API (Backend) | **$0/month** |
| Render PostgreSQL Database | **$0/month** |
| **TOTAL** | **$0/month** ✅ |

*(Assumes you use UptimeRobot free tier for keep-alive)*

---

## ⏱️ Time Required

- **Step 1-3 (Database + Backend)**: ~15 minutes
- **Step 4-5 (Frontend)**: ~10 minutes
- **Step 6 (Verification)**: ~3 minutes
- **TOTAL**: ~28 minutes

---

---

# 🛠️ DEPLOYMENT STEPS

## Step 1: Create Render Account & PostgreSQL Database

### 1.1 Sign Up for Render

1. Go to https://render.com
2. Click "Sign up"
3. Choose "GitHub" as sign-up method (or email)
4. Authorize Render to access your GitHub account

### 1.2 Create PostgreSQL Database

Once logged into Render dashboard:

1. Click **"New +"** button (top-right area)
2. Click **"PostgreSQL"**
3. Configure the database:

   | Field | Value |
   |-------|-------|
   | **Name** | `truthboard-db` |
   | **Database** | `truthlayer` |
   | **User** | `truthlayer` |
   | **Region** | `Ohio` (or closest to you) |
   | **PostgreSQL Version** | `15` (or latest) |
   | **Plan** | `Free` ✅ |

4. Click **"Create Database"**
5. **Wait 2-3 minutes** for database to be ready (status will turn green)

### 1.3 Copy Your Database Connection String

Once the database is created:

1. In Render dashboard, click on the database name `truthboard-db`
2. Look for **"Connections"** section
3. You'll see the connection string:

   ```
   postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer
   ```

4. **Copy this entire string** - you'll need it in Step 2

---

## Step 2: Deploy Backend to Render

### 2.1 Create Web Service on Render

In Render dashboard:

1. Click **"New +"** button (top-right)
2. Click **"Web Service"**
3. Click **"Connect repository"** and select your GitHub repo

### 2.2 Configure Backend Service

Fill in these exact values:

| Field | Value |
|-------|-------|
| **Name** | `truthboard-api` |
| **Environment** | `Docker` |
| **Region** | `Ohio` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Plan** | `Free` |

**IMPORTANT**: Make sure **Root Directory** is set to `backend` (Render might auto-detect this)

### 2.3 Add Environment Variables to Render Backend

After creating the service, go to the **"Environment"** tab and add these variables:

#### Variable 1: DATABASE_URL

| Key | Value |
|-----|-------|
| **DATABASE_URL** | `postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer` |

**What this does**: Tells the backend how to connect to your PostgreSQL database

**Steps to add:**
1. Click **"Add Environment Variable"**
2. In **Name** field, type: `DATABASE_URL`
3. In **Value** field, paste: `postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer`
4. Click **"Save"**

#### Variable 2: ALLOWED_ORIGINS

| Key | Value |
|-----|-------|
| **ALLOWED_ORIGINS** | `https://truthboard.vercel.app` |

**What this does**: Tells backend which frontend domain is allowed to make API requests (prevents CORS errors)

**Steps to add:**
1. Click **"Add Environment Variable"**
2. In **Name** field, type: `ALLOWED_ORIGINS`
3. In **Value** field, type: `https://truthboard.vercel.app`
4. Click **"Save"**

#### Variable 3: ENABLE_SCHEDULER

| Key | Value |
|-----|-------|
| **ENABLE_SCHEDULER** | `false` |

**What this does**: Disables background data processing (keeps memory usage low for free tier)

**Steps to add:**
1. Click **"Add Environment Variable"**
2. In **Name** field, type: `ENABLE_SCHEDULER`
3. In **Value** field, type: `false`
4. Click **"Save"**

#### Variable 4: PYTHONUNBUFFERED

| Key | Value |
|-----|-------|
| **PYTHONUNBUFFERED** | `1` |

**What this does**: Shows Python logs in real-time (helps debugging)

**Steps to add:**
1. Click **"Add Environment Variable"**
2. In **Name** field, type: `PYTHONUNBUFFERED`
3. In **Value** field, type: `1`
4. Click **"Save"**

### 2.4 Wait for Backend Deployment

After adding environment variables:

1. Render will automatically start building and deploying
2. Look for a **blue "Deployed"** status (takes 10-15 minutes)
3. Once deployed, you'll see your backend URL at the top:

   ```
   https://truthboard-api.onrender.com
   ```

4. **Save this URL** - you'll need it in Step 4

### 2.5 Verify Backend is Working

Once deployment shows blue "Deployed":

```bash
# Test 1: Check if backend is alive
curl https://truthboard-api.onrender.com/health

# Expected response:
# {"status":"healthy","message":"API is running"}
```

---

## Step 3: Create & Update Frontend Configuration

### 3.1 Create `.env.production` File in Frontend

On your local machine, in the `/frontend` directory:

1. Create a new file named `.env.production`
2. Add these exact environment variables:

```
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

**What each variable does:**

| Variable | Value | Purpose |
|----------|-------|---------|
| **NEXT_PUBLIC_API_URL** | `https://truthboard-api.onrender.com` | Frontend browser code uses this to fetch from backend |
| **INTERNAL_API_URL** | `https://truthboard-api.onrender.com` | Next.js server-side code uses this |

**File location after creation:**
```
frontend/.env.production
```

### 3.2 Commit & Push to GitHub

From your terminal, in the project root directory:

```bash
# Add the new file to git
git add frontend/.env.production

# Commit the change
git commit -m "Add production environment variables for frontend"

# Push to GitHub (this triggers Vercel deployment in next step)
git push origin main
```

---

## Step 4: Sign Up for Vercel & Deploy Frontend

### 4.1 Sign Up for Vercel

1. Go to https://vercel.com
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub account

### 4.2 Create Vercel Project

On Vercel dashboard:

1. Click **"Add New..."** → **"Project"**
2. Under "Import Git Repository", find your project repository
3. Click **"Import"**

### 4.3 Configure Frontend Project

Fill in these exact values:

| Field | Value |
|-------|-------|
| **Project Name** | `truthboard` |
| **Framework Preset** | `Next.js` |
| **Root Directory** | `./frontend` |

### 4.4 Add Environment Variables to Vercel

Vercel will ask for environment variables. Add these:

#### Variable 1: NEXT_PUBLIC_API_URL

| Key | Value |
|-----|-------|
| **NEXT_PUBLIC_API_URL** | `https://truthboard-api.onrender.com` |

**Steps:**
1. In the "Environment Variables" section, click **"Add"**
2. **Name**: `NEXT_PUBLIC_API_URL`
3. **Value**: `https://truthboard-api.onrender.com`
4. Make sure it's set for **"Production"** (checkbox)

#### Variable 2: INTERNAL_API_URL

| Key | Value |
|-----|-------|
| **INTERNAL_API_URL** | `https://truthboard-api.onrender.com` |

**Steps:**
1. Click **"Add"** again
2. **Name**: `INTERNAL_API_URL`
3. **Value**: `https://truthboard-api.onrender.com`
4. Make sure it's set for **"Production"**

### 4.5 Deploy

1. Click **"Deploy"**
2. **Wait 5-10 minutes** for deployment to complete
3. Once you see the **blue checkmark** next to deployment, it's live
4. You'll see a URL like: `https://truthboard.vercel.app`

### 4.6 Verify Frontend is Working

Once deployment is complete:

```bash
# Check if frontend loads
curl https://truthboard.vercel.app | grep -i "truthboard"

# Should see HTML with "truthboard" in it (no errors)
```

---

## Step 5: Update Backend ALLOWED_ORIGINS with Final Vercel URL

Now that you have your Vercel frontend URL, you need to tell the backend that this domain is allowed to make requests.

### 5.1 Get Your Vercel Frontend URL

From Vercel dashboard:
1. Click your project `truthboard`
2. At the top, you'll see the URL: `https://truthboard.vercel.app`

### 5.2 Update Backend Environment Variable

Go back to Render dashboard:

1. Click on your backend service `truthboard-api`
2. Click **"Environment"** tab
3. Find the `ALLOWED_ORIGINS` variable
4. Change the value (it might currently say `http://localhost:3000`)
5. Set it to: `https://truthboard.vercel.app`

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| **ALLOWED_ORIGINS** | `http://localhost:3000` | `https://truthboard.vercel.app` |

6. Click **"Save"**
7. Render will automatically redeploy (wait 2-3 minutes for deployment to finish)

---

## Step 6: Full System Verification

### 6.1 Test Backend Health

```bash
curl https://truthboard-api.onrender.com/health

# Expected response:
# {"status":"healthy","message":"..."}
```

**Status**: ✅ Backend is running

### 6.2 Test Backend API Endpoint

```bash
curl "https://truthboard-api.onrender.com/events?status=confirmed&politics_only=true&limit=2"

# Expected response:
# {"total":X,"results":[{"id":..., "title":...}]}
```

**Status**: ✅ Backend can access database

### 6.3 Test Frontend Loads

Open this URL in your browser:

```
https://truthboard.vercel.app
```

**What to look for:**
- [ ] Page loads without hanging
- [ ] See "Top Confirmed Events" section with news articles
- [ ] No red error messages in browser console (F12)
- [ ] Search bar appears at the top

**Status**: ✅ Frontend is live

### 6.4 Test Search Functionality

1. On `https://truthboard.vercel.app`, click the search bar
2. Type: `election`
3. Press Enter
4. You should see search results page with articles matching "election"

**Status**: ✅ Frontend ↔ Backend communication works

### 6.5 Test All Pages

Visit each URL and verify it loads without errors:

| Page | URL | Should See |
|------|-----|-----------|
| **Home** | `https://truthboard.vercel.app` | Top confirmed events |
| **Developing Events** | `https://truthboard.vercel.app/developing` | In-progress events |
| **Conflicts** | `https://truthboard.vercel.app/conflicts` | Conflicting narratives |
| **Stats** | `https://truthboard.vercel.app/stats` | Charts and statistics |

**Status**: ✅ All pages working

---

## 🔧 Environment Variables Summary

### All Variables You Created

Here's a complete list of every variable and where it goes:

#### **In Render Backend Service**

```
DATABASE_URL=postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer
ALLOWED_ORIGINS=https://truthboard.vercel.app
ENABLE_SCHEDULER=false
PYTHONUNBUFFERED=1
```

#### **In Vercel Frontend Project**

```
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

#### **Explanation of Each**

| Variable | Location | Value | Why |
|----------|----------|-------|-----|
| `DATABASE_URL` | Render Backend | `postgresql://truthlayer:...` | Backend needs to know how to connect to your database |
| `ALLOWED_ORIGINS` | Render Backend | `https://truthboard.vercel.app` | Prevents CORS errors when frontend makes API requests |
| `ENABLE_SCHEDULER` | Render Backend | `false` | Keeps memory usage low on free tier |
| `PYTHONUNBUFFERED` | Render Backend | `1` | Shows Python logs in real-time |
| `NEXT_PUBLIC_API_URL` | Vercel Frontend | `https://truthboard-api.onrender.com` | Frontend JavaScript code uses this for API calls |
| `INTERNAL_API_URL` | Vercel Frontend | `https://truthboard-api.onrender.com` | Next.js server uses this for API calls during SSR |

---

## 🔒 Keep Backend Alive (Free Tier Requirement)

Free tier Render services sleep after 15 minutes of inactivity. Use UptimeRobot to keep it awake.

### 7.1 Sign Up for UptimeRobot

1. Go to https://uptimerobot.com
2. Click **"Sign Up for Free"**
3. Create account

### 7.2 Create Monitoring Alert

1. Click **"Add Monitor"**
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Monitor Type** | `HTTP(s)` |
   | **Friendly Name** | `Truthboard Backend` |
   | **URL** | `https://truthboard-api.onrender.com/health` |
   | **Monitoring Interval** | `30 minutes` |

3. Click **"Create Monitor"**

**What this does**: Every 30 minutes, UptimeRobot pings your backend, keeping it awake 24/7

---

## 📊 Directory & File Structure Summary

After deployment, here's what you have:

```
Your GitHub Repo
├── /frontend
│   ├── src/
│   ├── .env.production          ← Added in Step 3
│   ├── package.json
│   └── next.config.js
│
├── /backend
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
└── /data
    └── events.db               ← Will be synced to PostgreSQL
```

**Deployed to:**
- **Frontend**: https://truthboard.vercel.app (Vercel's servers)
- **Backend**: https://truthboard-api.onrender.com (Render's servers)
- **Database**: PostgreSQL on Render servers

---

## ⚠️ Common Mistakes & How to Fix

### Mistake 1: CORS Error on Frontend
```
Error: "Access to XMLHttpRequest has been blocked by CORS policy"
```

**Fix**:
1. Go to Render → truthboard-api → Environment
2. Check `ALLOWED_ORIGINS` = `https://truthboard.vercel.app` (not `http://localhost`)
3. If wrong, update it
4. Click "Save" and wait for redeploy

### Mistake 2: "Failed to fetch" Error
```
Error: TypeError: Failed to fetch
```

**Fix**:
1. Go to Vercel → truthboard project → Settings
2. Check "Environment Variables"
3. Verify `NEXT_PUBLIC_API_URL` = `https://truthboard-api.onrender.com`
4. If wrong, update it and redeploy

### Mistake 3: Database Connection Error
```
Error: "could not translate host name "dpg-..." to address"
```

**Fix**:
1. Go to Render → truthboard-api → Environment
2. Copy `DATABASE_URL` from Render PostgreSQL service (don't type it manually)
3. Make sure it's the exact value, not modified
4. Click "Save" and redeploy

### Mistake 4: Backend Deployment Failing
```
Error: "Docker build failed"
```

**Check these:**
1. Root directory is set to `backend` in Render
2. Backend has `requirements.txt` (all Python dependencies)
3. Backend has `Dockerfile`
4. All files are committed to GitHub

### Mistake 5: Frontend Deployment Failing
```
Error: "Build failed"
```

**Check these:**
1. Root directory is set to `frontend` in Vercel
2. Frontend has `package.json` (all Node.js dependencies)
3. All files are committed to GitHub
4. Environment variables are set before deployment

---

## 📈 What to Monitor After Deployment

### Daily (5 minutes)
- Check Render logs for any errors: https://dashboard.render.com
- Check Vercel deployment status: https://vercel.com/dashboard

### Weekly (10 minutes)
- Test health endpoint:
  ```bash
  curl https://truthboard-api.onrender.com/health
  ```
- Visit `https://truthboard.vercel.app` and test search
- Verify UptimeRobot shows "Up": https://uptimerobot.com/dashboard

### Monthly (15 minutes)
- Check database storage usage in Render
- Review any error patterns
- Verify cost is still $0

---

## 🚀 Success Checklist

After completing all steps, verify:

- [ ] PostgreSQL database created on Render (green status)
- [ ] Backend deployed to Render (blue "Deployed" status)
- [ ] `DATABASE_URL` set in Render backend environment
- [ ] `ALLOWED_ORIGINS` set to `https://truthboard.vercel.app` in Render
- [ ] `ENABLE_SCHEDULER` set to `false` in Render
- [ ] Frontend deployed to Vercel (blue checkmark)
- [ ] `NEXT_PUBLIC_API_URL` set to `https://truthboard-api.onrender.com` in Vercel
- [ ] `INTERNAL_API_URL` set to `https://truthboard-api.onrender.com` in Vercel
- [ ] `curl https://truthboard-api.onrender.com/health` returns JSON
- [ ] `https://truthboard.vercel.app` loads without errors
- [ ] Search functionality works
- [ ] All pages load (home, developing, conflicts, stats)
- [ ] UptimeRobot monitor created and shows "Up"

**If all checked**: ✅ **You're deployed!** 🎉

---

## 💬 Quick Reference Card

**Keep this handy while deploying:**

```
VERCEL FRONTEND URLs:
- Production: https://truthboard.vercel.app
- Settings: https://vercel.com/dashboard

RENDER BACKEND URLs:
- Production: https://truthboard-api.onrender.com
- Dashboard: https://dashboard.render.com
- Health: https://truthboard-api.onrender.com/health

RENDER DATABASE:
- PostgreSQL: postgresql://truthlayer:...

UPTIMEROBOT:
- Monitor URL: https://truthboard-api.onrender.com/health
- Dashboard: https://uptimerobot.com/dashboard

ENVIRONMENT VARIABLES (Render Backend):
- DATABASE_URL=postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer
- ALLOWED_ORIGINS=https://truthboard.vercel.app
- ENABLE_SCHEDULER=false
- PYTHONUNBUFFERED=1

ENVIRONMENT VARIABLES (Vercel Frontend):
- NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
- INTERNAL_API_URL=https://truthboard-api.onrender.com
```

---

## ❓ FAQ

**Q: Why are there two environment variables with the same API URL?**
A: `NEXT_PUBLIC_API_URL` is used by browser JavaScript, `INTERNAL_API_URL` is used by Next.js server code during page generation.

**Q: What if my Vercel URL is different than `truthboard.vercel.app`?**
A: Vercel might give you a different URL. Whatever URL it gives you, use that in `ALLOWED_ORIGINS` on the Render backend.

**Q: Do I need to do anything with the database?**
A: No, Render handles it automatically. It backs up daily and handles all maintenance.

**Q: What if it still doesn't work?**
A: Check the troubleshooting section above, or review the logs:
- Render logs: https://dashboard.render.com → truthboard-api → Logs
- Vercel logs: https://vercel.com/dashboard → truthboard → Deployments

**Q: Can I use a custom domain?**
A: Yes! After this works, Vercel lets you add custom domains very easily in Settings.

**Q: When do I need to upgrade from free tier?**
A: See the FREE_TIER_ANALYSIS.md document for detailed scenarios. Summary: if you have <50 users/day, free tier works great. 50-100 users/day requires monitoring. >100 users/day needs upgrade to $7/month tier.

---

## 📚 Related Documentation

For more details, see these files:

- **FREE_TIER_ANALYSIS.md** - Complete analysis of free tier viability, memory usage, load scenarios
- **DEPLOYMENT_ARCHITECTURE.txt** - System diagrams, network flow, scaling options
- **DEPLOYMENT_CHECKLIST.md** - Quick reference checklist for each step
- **DEPLOYMENT_COMMANDS.md** - Copy-paste ready commands for all operations

---

## 🎓 What Each Component Does

- **Vercel (Frontend)**: Hosts your Next.js website, serves it globally via CDN
- **Render (Backend API)**: Runs your FastAPI server, processes requests from frontend
- **Render PostgreSQL**: Stores all your event data, articles, and analysis
- **UptimeRobot**: Keeps backend awake by pinging it every 30 minutes

Together they create: **Truthboard** - A political news analyzer that detects conflicting narratives across multiple news sources.

---

## 🎉 You're Done!

**Your Truthboard instance is now live at: `https://truthboard.vercel.app`**

Users can:
- ✅ View top confirmed political events
- ✅ See developing/breaking news
- ✅ Search for specific topics
- ✅ Analyze conflicting narratives
- ✅ Review statistical summaries

**All for $0/month!** 💰

---

*Deployment Guide Generated: October 23, 2025*
*For The Truthboard v1.0*
*With Render (Backend + Database) + Vercel (Frontend)*
