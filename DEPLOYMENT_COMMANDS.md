# Deployment Commands - Copy & Paste Ready

## Prerequisites

- [ ] GitHub account with repo pushed
- [ ] Render account (https://render.com)
- [ ] Vercel account (https://vercel.com)

---

## Step 1: Prepare Frontend Environment File

```bash
# In your project root:
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
EOF
```

Then push to GitHub:

```bash
cd /path/to/project
git add frontend/.env.production
git commit -m "Add production environment configuration"
git push origin main
```

---

## Step 2: Render - Create PostgreSQL Database

**Manual Steps (UI):**
1. Go to https://render.com/dashboard
2. Click "New +" → "PostgreSQL"
3. Enter these values:
   - **Name:** `truthboard-db`
   - **Database:** `truthboard`
   - **User:** `truthboard_user`
   - **PostgreSQL Version:** 15
   - **Region:** (pick closest to your users)
   - **Plan:** Free
4. Click "Create Database"

**Wait for it to be ready (status = green)**

Then copy the connection string from the dashboard.

---

## Step 3: Render - Deploy Backend API

**Manual Steps (UI):**

1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Click "Connect account" if needed to connect GitHub
4. Select your repository
5. Fill in:
   - **Repository:** (your repo)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Name:** `truthboard-api`
   - **Environment:** `Docker`
   - **Plan:** Free
   - **Region:** (same as database above)

6. Click "Advanced" and add these **Environment Variables:**

```
DATABASE_URL=postgresql://truthboard_user:PASSWORD@HOST:5432/truthboard
ENABLE_SCHEDULER=false
PYTHONUNBUFFERED=1
ALLOWED_ORIGINS=http://localhost:3000
```

*Replace with your actual DATABASE_URL from Step 2*

7. Click "Deploy"

**Wait 10-15 minutes for deployment**

Copy the URL from the top (looks like `https://truthboard-api.onrender.com`)

---

## Step 4: Update Frontend Environment with Actual Backend URL

Edit your frontend environment file with the real Render URL:

```bash
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
EOF
```

Push to GitHub:

```bash
git add frontend/.env.production
git commit -m "Update API URL to production"
git push origin main
```

---

## Step 5: Vercel - Deploy Frontend

**Manual Steps (UI):**

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Click "Import Git Repository"
4. Select your GitHub repository
5. Fill in:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next`

6. Add **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
   INTERNAL_API_URL=https://truthboard-api.onrender.com
   ```

7. Click "Deploy"

**Wait 5-10 minutes for deployment**

Copy the URL from Vercel (looks like `https://truthboard.vercel.app`)

---

## Step 6: Update Backend CORS

Go back to Render and update the backend:

1. Go to https://render.com/dashboard
2. Click on `truthboard-api` service
3. Go to "Environment" tab
4. Update `ALLOWED_ORIGINS` to:
   ```
   https://truthboard.vercel.app
   ```
5. Click "Save changes"

**Wait 2-3 minutes for redeploy**

---

## Step 7: Verify Deployment

### Test Backend API

```bash
# Test health endpoint
curl https://truthboard-api.onrender.com/health

# Should return:
# {"status":"healthy","database":"connected",...}
```

### Test Backend with query

```bash
# Test getting confirmed events
curl "https://truthboard-api.onrender.com/events?status=confirmed&politics_only=true&limit=2"

# Should return JSON with events
```

### Test Frontend

```bash
# Just visit in browser:
# https://truthboard.vercel.app

# Should show:
# - Homepage with "Top Confirmed Events"
# - Political news articles
# - No red error messages
```

---

## Step 8: Set Up Keep-Alive (Prevent Free Tier Sleep)

**Option A: UptimeRobot (Recommended)**

```bash
# Go to https://uptimerobot.com
# Sign up with email

# Create monitor:
# - URL: https://truthboard-api.onrender.com/health
# - Type: HTTP(s)
# - Interval: 30 minutes
# - Alert Contacts: Your email
```

**Option B: Using a simple bash script**

```bash
# Create a cron job on any always-on server:
# Add to crontab:
# */30 * * * * curl https://truthboard-api.onrender.com/health > /dev/null 2>&1

# Or use this one-liner:
# */30 * * * * /usr/bin/curl --max-time 5 https://truthboard-api.onrender.com/health
```

---

## Troubleshooting Commands

### Check Backend Logs

```bash
# Render automatically shows logs at:
# https://dashboard.render.com/services/truthboard-api/logs

# Or from command line if you have render-cli installed:
# render logs truthboard-api
```

### Check Frontend Logs

```bash
# Vercel shows logs at:
# https://vercel.com/dashboard/truthboard/deployments

# Or check browser console (F12) when visiting the site
```

### Test API Connection

```bash
# From terminal:
curl -v https://truthboard-api.onrender.com/health

# From Python:
python3 << 'EOF'
import requests
resp = requests.get('https://truthboard-api.onrender.com/health')
print(resp.json())
EOF

# From browser console:
fetch('https://truthboard-api.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log(d))
```

### Test Frontend API Call

```bash
# Open browser, press F12, go to Console, paste:
fetch('https://truthboard-api.onrender.com/events?status=confirmed&politics_only=true&limit=1')
  .then(r => r.json())
  .then(d => console.log(d))

# Should show event data, not errors
```

---

## Reset / Redeploy

### Redeploy Backend

```bash
# Go to Render Dashboard → truthboard-api → Deploys
# Click "Manual Deploy" → "Deploy latest commit"
```

### Redeploy Frontend

```bash
# Go to Vercel Dashboard → Deployments
# Click "Redeploy"
```

### Full Reset (if needed)

```bash
# Delete services from Render/Vercel dashboards
# Then follow steps 1-6 again
```

---

## Monitor Deployment

### Daily Health Check

```bash
# Run this daily to verify everything works:

echo "Checking backend..."
curl -s https://truthboard-api.onrender.com/health | jq '.' || echo "Backend DOWN"

echo "Checking frontend..."
curl -s https://truthboard.vercel.app -I | head -n 1

echo "Done!"
```

### Monthly Database Check

```bash
# Check how much storage you're using:
# Render Dashboard → PostgreSQL Instance → Metrics

# If approaching 1 GB limit, run cleanup:
psql "postgresql://user:password@host:5432/truthboard" << 'EOF'
DELETE FROM events
WHERE importance_score < 50
AND last_seen < now() - interval '30 days';
EOF
```

---

## Final Validation Checklist

Run these to verify everything is working:

```bash
#!/bin/bash

echo "=== Deployment Validation ==="
echo ""

# Test 1: Backend Health
echo "1. Testing backend health..."
HEALTH=$(curl -s https://truthboard-api.onrender.com/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Backend is healthy"
else
    echo "   ❌ Backend is down"
    exit 1
fi

# Test 2: API Response
echo "2. Testing API endpoint..."
EVENTS=$(curl -s "https://truthboard-api.onrender.com/events?status=confirmed&politics_only=true&limit=1")
if echo "$EVENTS" | grep -q "summary"; then
    echo "   ✅ API returning data"
else
    echo "   ❌ API not returning data"
    exit 1
fi

# Test 3: Frontend Load
echo "3. Testing frontend..."
FRONTEND=$(curl -s https://truthboard.vercel.app | head -c 1000)
if echo "$FRONTEND" | grep -q "Truthboard"; then
    echo "   ✅ Frontend loaded"
else
    echo "   ❌ Frontend failed to load"
    exit 1
fi

echo ""
echo "=== All tests passed! Deployment successful! ==="
echo ""
echo "Frontend: https://truthboard.vercel.app"
echo "Backend:  https://truthboard-api.onrender.com"
```

---

## Common Issues & Fixes

### "Connection refused" on backend

**Cause:** Backend still deploying
**Fix:** Wait 10 minutes, then test again

### "Failed to fetch" in frontend

**Cause:** ALLOWED_ORIGINS not set correctly
**Fix:**
```bash
# Go to Render → truthboard-api → Environment
# Set ALLOWED_ORIGINS to: https://truthboard.vercel.app
# Save changes and wait 2 minutes
```

### Database connection error

**Cause:** Wrong DATABASE_URL
**Fix:**
```bash
# Copy the correct URL from Render PostgreSQL dashboard
# Update in Render → truthboard-api → Environment
# Redeploy
```

### Slow responses

**Normal:** Free tier is slower; this is expected

**To improve:**
- Use keep-alive to prevent service sleep
- Upgrade to paid tier if needed ($7+/month)

---

## Done!

Your site is live at:
- **Frontend:** https://truthboard.vercel.app
- **Backend:** https://truthboard-api.onrender.com
- **Status:** https://truthboard-api.onrender.com/health

**Total cost: $0/month** ✅

---

## Next Steps (Optional)

1. Add custom domain (see DEPLOYMENT_GUIDE.md)
2. Set up monitoring alerts (UptimeRobot)
3. Configure scheduled backups
4. Add analytics (Vercel provides free analytics)
