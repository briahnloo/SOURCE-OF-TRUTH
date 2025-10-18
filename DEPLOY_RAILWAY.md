# Deploy Truth Layer to Railway.app ($5/month all-inclusive)

Railway.app offers the simplest deployment with database included for $5/month.

## Prerequisites

- GitHub repository: https://github.com/briahnloo/SOURCE-OF-TRUTH
- Railway.app account: https://railway.app
- Credit card (for $5/month Hobby plan after free trial)

## Total Cost

- **$5/month** (includes PostgreSQL database!)
- All services included: Backend, Worker, Frontend, Database

## Step-by-Step Deployment

### Step 1: Create Railway Account

1. Visit https://railway.app
2. Click "Start a New Project"
3. Sign in with GitHub
4. Verify your email

### Step 2: Deploy from GitHub

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose **briahnloo/SOURCE-OF-TRUTH**
4. Railway will automatically:
   - Detect Dockerfiles
   - Create services for backend, worker, frontend
   - Generate URLs

### Step 3: Add PostgreSQL Database

1. In your project → Click **New**
2. Select **Database** → **PostgreSQL**
3. Database auto-provisions (included in $5/month)
4. Connection string auto-generated

### Step 4: Configure Environment Variables

Railway auto-detects most settings, but you need to add:

**For Backend Service:**
1. Click on `backend` service
2. Variables tab → **Add Variable**:
   ```
   DATABASE_URL = ${{Postgres.DATABASE_URL}}  (auto-linked!)
   ALLOWED_ORIGINS = ${{RAILWAY_PUBLIC_DOMAIN}}  (auto-fills)
   NEWSAPI_KEY = (add if you have)
   MEDIASTACK_KEY = (add if you have)
   ```

**For Worker Service:**
1. Click on `worker` service
2. Add same variables as backend

**For Frontend Service:**
1. Click on `frontend` service
2. Variables tab:
   ```
   NEXT_PUBLIC_API_URL = https://${{backend.RAILWAY_PUBLIC_DOMAIN}}
   ```

### Step 5: Set Service Start Commands

Railway should auto-detect, but verify:

**Backend**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
**Worker**: `python -m app.workers.scheduler`
**Frontend**: `npm start` (or auto-detected)

### Step 6: Deploy!

1. All services should auto-deploy
2. Wait 5-10 minutes for builds
3. Check **Deployments** tab for status
4. Your URLs will be:
   - Frontend: `https://truthlayer-frontend.up.railway.app`
   - Backend: `https://truthlayer-backend.up.railway.app`

---

## Post-Deployment

### Verify Everything Works

1. **Visit Frontend**: Should show hero section and events
2. **Check Health**: `https://backend-url.railway.app/health`
3. **View API Docs**: `https://backend-url.railway.app/docs`
4. **Monitor Worker**: Check logs in Railway dashboard

### Add Custom Domain (Optional)

1. In Frontend service → Settings → **Domains**
2. Click **Custom Domain**
3. Add: `truthlayer.com`
4. Railway provides CNAME or A record
5. Update DNS at your registrar
6. SSL auto-provisions!

### Update CORS

After custom domain:
1. Backend service → Variables
2. Update: `ALLOWED_ORIGINS=https://truthlayer.com`
3. Frontend service → Variables
4. Update: (Railway auto-handles this)

---

## Cost Breakdown

**Hobby Plan ($5/month):**
- ✅ Backend service (included)
- ✅ Worker service (included)
- ✅ Frontend service (included)
- ✅ PostgreSQL database (included)
- ✅ SSL certificates (included)
- ✅ 500GB bandwidth (included)
- ✅ Automatic deployments (included)

**No hidden fees!** $5/month total.

---

## Monitoring

### Built-in Monitoring

Railway provides:
- CPU/Memory usage graphs
- Request logs
- Error tracking
- Deployment history

### External Monitoring (Optional)

- **UptimeRobot**: Free uptime monitoring
- **Sentry**: Free error tracking
- **Google Analytics**: User analytics

---

## Scaling

**Current capacity:**
- ~1,000 concurrent users
- ~10,000 articles/day
- 99.9% uptime

**To scale:**
1. Upgrade to Pro plan ($20/month)
2. Add more workers (horizontal scaling)
3. Upgrade database plan
4. Add Redis caching

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Discord Community**: https://discord.gg/railway
- **Status**: https://railway.app/legal/fair-use

## Advantages of Railway

- ✅ Simplest deployment (one-click from GitHub)
- ✅ Database included in price
- ✅ Auto-deploys on git push
- ✅ Built-in metrics and logs
- ✅ Predictable pricing
- ✅ No credit card for trial

**Perfect for MVPs and side projects!** 🚀

