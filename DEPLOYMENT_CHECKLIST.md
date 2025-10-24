# Deployment Checklist - Quick Reference

## 5-Minute Setup Overview

1. **Render PostgreSQL** - 2 minutes
2. **Render Backend API** - 3 minutes (deploys in background)
3. **Vercel Frontend** - 3 minutes (deploys in background)
4. **Connect them** - 1 minute

---

## Phase 1: Render Database (Do First)

```
1. Go to https://render.com/dashboard
2. Click "New +" → "PostgreSQL"
3. Name: truthboard-db
4. Click "Create Database"
5. COPY the Internal Database URL (looks like postgresql://...)
```

**Expected time: 2 minutes**
**Status:** Green checkmark when ready (usually instant)

---

## Phase 2: Render Backend API

```
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect GitHub (select your repo)
4. Root Directory: backend
5. Name: truthboard-api
6. Environment: Docker
7. Click "Advanced" → Add Environment Variables:
   - DATABASE_URL=<paste from Phase 1>
   - ENABLE_SCHEDULER=false
   - ALLOWED_ORIGINS=http://localhost:3000
8. Click "Deploy"
9. Wait ~10 minutes, then COPY the URL (https://truthboard-api.onrender.com)
```

**Expected time: 5 minutes to deploy, 10 minutes to build**
**Status:** Blue/green when ready

---

## Phase 3: Update Frontend Config

```bash
# In your local repo, create this file:
frontend/.env.production

# Add these lines:
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com

# Then:
git add frontend/.env.production
git commit -m "Add production config"
git push
```

**Expected time: 2 minutes**

---

## Phase 4: Vercel Frontend

```
1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repo
4. Root Directory: frontend
5. Add Environment Variables:
   - NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
   - INTERNAL_API_URL=https://truthboard-api.onrender.com
6. Click "Deploy"
7. Wait ~5 minutes, COPY the URL (https://truthboard.vercel.app)
```

**Expected time: 5 minutes to deploy**
**Status:** Blue when ready

---

## Phase 5: Connect Frontend to Backend

```
1. Go back to Render Dashboard → truthboard-api
2. Go to "Environment" tab
3. Update ALLOWED_ORIGINS to:
   https://truthboard.vercel.app
4. Click "Save changes"
5. Wait 1 minute for redeploy
```

**Expected time: 2 minutes**

---

## Phase 6: Verify Everything

```
Test 1: Backend Health
curl https://truthboard-api.onrender.com/health
→ Should return JSON with "status": "healthy"

Test 2: Frontend Loads
Visit https://truthboard.vercel.app
→ Should show "Top Confirmed Events" with political news

Test 3: Search Works
Search for "trump" or "politics"
→ Should return results

Test 4: API Connection
Open browser console (F12)
Check for [API] logs
→ Should have no red errors
```

---

## Environment Variables Summary

### Backend (Render)
```
DATABASE_URL=postgresql://user:password@host:5432/truthboard
ALLOWED_ORIGINS=https://truthboard.vercel.app
ENABLE_SCHEDULER=false
PYTHONUNBUFFERED=1
```

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

---

## If Something Goes Wrong

| Problem | Solution |
|---------|----------|
| Backend shows 500 errors | Check Render logs → Dashboard → truthboard-api → Logs |
| Frontend shows "Failed to fetch" | Verify ALLOWED_ORIGINS in Render includes Vercel domain |
| Takes too long to deploy | Free tier is slow; normal behavior |
| "Connection refused" | Backend might still be deploying; wait 10 min |

---

## Minimal Cost

- **Free tier covers everything**
- Render: Free Web Service + Free PostgreSQL (1 GB)
- Vercel: Free tier (unlimited deployments)
- **Total: $0/month**

---

## Keep Alive Strategy (Prevent Free Tier Sleep)

Free services sleep after 15 minutes of inactivity. Add this keep-alive:

**Option A: UptimeRobot (Easy)**
1. Go to https://uptimerobot.com
2. Sign up free
3. Add monitor: `https://truthboard-api.onrender.com/health`
4. Interval: 30 minutes
5. Done!

**Option B: Cron job** (see DEPLOYMENT_GUIDE.md)

---

## After Deployment

1. **Add to your GitHub README:**
   ```
   ## Live Demo
   Frontend: https://truthboard.vercel.app
   API: https://truthboard-api.onrender.com
   ```

2. **Monitor weekly:**
   - Check Vercel for build errors
   - Check Render logs for API errors
   - Verify UptimeRobot shows "Up"

3. **Never worry about cost** - it's $0!

---

## Total Time Estimate

- **Phase 1 (Database):** 2 min
- **Phase 2 (Backend):** 10 min
- **Phase 3 (Config):** 2 min
- **Phase 4 (Frontend):** 5 min
- **Phase 5 (Connect):** 2 min
- **Phase 6 (Test):** 3 min

**Total: ~25 minutes from start to live website**

---

## Success Indicators

✅ Vercel shows "Ready"
✅ Render shows green checkmark
✅ `https://truthboard-api.onrender.com/health` returns JSON
✅ `https://truthboard.vercel.app` loads without errors
✅ Browser console has no red errors
✅ All pages load (home, developing, conflicts, stats)

**You're deployed!**
