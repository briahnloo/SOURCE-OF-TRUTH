# 🚀 Truthboard - Deployment Guide

**Complete, minimal-cost deployment to Render + Vercel**

---

## 📋 Files in This Directory

- **DEPLOYMENT_SUMMARY.txt** - Start here! Quick overview (2 min read)
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist with UI instructions
- **DEPLOYMENT_COMMANDS.md** - Copy-paste ready commands
- **DEPLOYMENT_GUIDE.md** - Complete detailed guide with all options

---

## ⚡ 25-Minute Deployment

### Prerequisites
- [ ] GitHub account with repo pushed
- [ ] Render account (free at https://render.com)
- [ ] Vercel account (free at https://vercel.com)

### Step-by-Step

**1. Create Database (2 min)**
```
Render → New → PostgreSQL → Free → Create
Copy connection string
```

**2. Deploy Backend (10 min)**
```
Render → New → Web Service
Connect GitHub → /backend directory
Add DATABASE_URL env var
Wait for green checkmark → Copy URL
```

**3. Update Frontend Config (2 min)**
```bash
cat > frontend/.env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
EOF

git add frontend/.env.production
git commit -m "Add production config"
git push
```

**4. Deploy Frontend (5 min)**
```
Vercel → Add Project → Import GitHub
Root: /frontend
Add NEXT_PUBLIC_API_URL env var
Deploy → Wait for blue status
```

**5. Connect Backend (2 min)**
```
Render → truthboard-api → Environment
Update ALLOWED_ORIGINS = https://truthboard.vercel.app
Save → Wait 1 min for redeploy
```

**6. Verify (3 min)**
```bash
curl https://truthboard-api.onrender.com/health
# Visit https://truthboard.vercel.app
# Test search & all pages
```

---

## 🔧 Configuration Reference

### Backend Environment Variables
```
DATABASE_URL=postgresql://user:pass@host:5432/truthboard
ALLOWED_ORIGINS=https://truthboard.vercel.app
ENABLE_SCHEDULER=false
PYTHONUNBUFFERED=1
```

### Frontend Environment Variables
```
NEXT_PUBLIC_API_URL=https://truthboard-api.onrender.com
INTERNAL_API_URL=https://truthboard-api.onrender.com
```

---

## 📊 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Free | **$0** |
| Render API | Free | **$0** |
| Render DB | Free (1 GB) | **$0** |
| **Total** | | **$0/month** ✅ |

---

## 🌐 URLs After Deployment

- **Frontend:** `https://truthboard.vercel.app`
- **Backend API:** `https://truthboard-api.onrender.com`
- **API Health:** `https://truthboard-api.onrender.com/health`
- **API Docs:** `https://truthboard-api.onrender.com/docs`

---

## ✅ Validation Tests

```bash
# Test 1: Backend is running
curl https://truthboard-api.onrender.com/health
# Should return: {"status":"healthy"...}

# Test 2: API returning data
curl "https://truthboard-api.onrender.com/events?status=confirmed&politics_only=true&limit=1"
# Should return: {"total":X,"results":[...]}

# Test 3: Frontend loads
curl https://truthboard.vercel.app | grep -i "truthboard"
# Should return: HTML with "Truthboard" title

# Test 4: No CORS errors
# Visit https://truthboard.vercel.app
# Open F12 → Console
# Should show NO red errors
```

---

## 🛡️ Keep Backend Alive (Prevent Free Tier Sleep)

Free tier services sleep after 15 minutes inactivity.

**Recommended: UptimeRobot (5 minutes setup)**
```
1. https://uptimerobot.com → Sign up free
2. Add Monitor:
   - URL: https://truthboard-api.onrender.com/health
   - Interval: 30 minutes
3. Done! Keeps backend awake.
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `curl: Connection refused` | Backend still deploying - wait 10 min |
| Frontend: "Failed to fetch" | Check ALLOWED_ORIGINS in Render |
| `HTTP 500` errors | Check Render logs for actual error |
| `Connection refused` to DB | Wrong DATABASE_URL - copy again from Render |
| Everything works locally but not deployed | Check environment variables match |

---

## 📦 What Gets Deployed

### Frontend (Vercel)
- Next.js 14 application
- React components
- Static assets
- Environment variables from `.env.production`

### Backend (Render)
- FastAPI application
- Python dependencies (from pyproject.toml)
- Docker container
- Scheduled jobs (disabled on free tier)

### Database (Render PostgreSQL)
- SQLite converted to PostgreSQL
- 1 GB storage (free tier)
- Automatic backups

---

## 🔄 Deployment Updates

After initial deployment, any push to `main` branch will:

**Frontend:**
- Automatically redeploy on Vercel
- Usually takes 2-5 minutes
- Shows deployment status at https://vercel.com/dashboard

**Backend:**
- Automatically redeploy on Render
- Rebuilds Docker image
- Usually takes 10-15 minutes
- Check at https://dashboard.render.com

---

## 📈 Monitoring

### Daily
- Check Vercel deployment status
- Check Render logs for errors
- Verify UptimeRobot shows "Up"

### Weekly
- Run health check: `curl https://truthboard-api.onrender.com/health`
- Visit frontend: Verify pages load

### Monthly
- Check database size (Render → PostgreSQL → Metrics)
- Review any error patterns in logs
- Verify cost is still $0

---

## 🚀 Next Steps (Optional)

### Add Custom Domain
1. Buy domain from registrar (GoDaddy, Namecheap, etc.)
2. Vercel: Settings → Domains → Add your domain
3. Update DNS CNAME to point to Vercel
4. SSL automatic via Let's Encrypt

### Upgrade for Better Performance
- Backend: $7/month tier (better CPU/memory)
- Database: $15/month tier (10 GB storage)
- Still way cheaper than AWS/GCP

### Add Monitoring Alerts
- Slack notifications for API downtime
- Email alerts from UptimeRobot
- Vercel deployment notifications

---

## 📚 For More Details

1. **DEPLOYMENT_CHECKLIST.md** - Step-by-step with UI walkthrough
2. **DEPLOYMENT_COMMANDS.md** - All copy-paste commands organized
3. **DEPLOYMENT_GUIDE.md** - Complete reference with all options

---

## ❓ FAQ

**Q: Will it really cost $0?**
A: Yes, if you use free tiers and UptimeRobot's free plan. Keep alive is important to prevent sleeping.

**Q: How long does deployment take?**
A: ~25 minutes total. Backend takes 10 min to build Docker image, frontend takes 5 min. Rest is configuration.

**Q: What if I want to scale?**
A: Render and Vercel both have paid tiers. Upgrade anytime, no contract.

**Q: Can I use a different provider?**
A: Yes! The guide is Render + Vercel specific, but architecture works on AWS, GCP, etc.

**Q: What about database backups?**
A: Render PostgreSQL has automatic daily backups. Accessible from dashboard.

**Q: How do I deploy new code?**
A: Just push to GitHub `main` branch. Both Vercel and Render auto-redeploy.

---

## 🎯 Success Indicators

✅ `https://truthboard-api.onrender.com/health` returns JSON
✅ `https://truthboard.vercel.app` loads without console errors
✅ Homepage shows "Top Confirmed Events" with political news
✅ Search bar works and returns results
✅ All pages (developing, conflicts, stats) load
✅ UptimeRobot shows "Up"

**You're deployed! 🎉**

---

## 📞 Support

- **Render issues?** → https://dashboard.render.com (click service → Logs)
- **Vercel issues?** → https://vercel.com/dashboard (click project → Deployments)
- **Need to scale?** → Check pricing pages for upgrade options
- **Custom domain?** → See DEPLOYMENT_GUIDE.md

---

## 📄 License

Same as main project

---

**Total Setup Time: ~25 minutes**
**Total Cost: $0/month**
**Maintenance Time: ~5 min/week**

Happy deploying! 🚀
