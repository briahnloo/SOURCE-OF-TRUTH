# Maintenance Guide: What You Need to Know

## TL;DR: Yes, You Can Just Leave It Running

Your system is **100% self-sustaining**. You can leave it running indefinitely with zero manual intervention required (besides paying your Render bill).

---

## What Happens Automatically (You Don't Need to Do Anything)

✅ **Every 15 minutes**:
- Scheduler fetches articles from 5+ free sources
- Processes articles into events
- Scores events for quality/importance
- Updates database
- Updates "Last Update" timestamp

✅ **Every 24 hours**:
- Articles older than 30 days are deleted (configurable)
- System stays optimized

✅ **On errors**:
- Failed source skipped, others continue
- Error logged for your review
- System continues running

---

## Monthly Checklist (Optional, But Recommended)

### Every Month - Quick Verification (5 minutes)

```bash
# Check if system is still healthy
curl https://truthboard-api.onrender.com/health | jq '.'

# Expected:
# - status: healthy ✅
# - database: connected ✅
# - worker_last_run: Recent time (not days old) ✅
# - total_articles: Should be > 4500 and growing ✅
```

**What to look for**:
- `worker_last_run` should be within the last 30 minutes (latest ingestion time)
- `total_articles` should increase over time (more articles = working)
- `status: healthy` and `database: connected` ✅

If all looks good, you're done! ✅

---

## When to Worry (Very Rare)

### Scenario 1: `worker_last_run` is 24+ hours old

**What it means**: No ingestion has run recently

**Fix**:
1. Check Render logs: https://dashboard.render.com/
2. Look for errors in "Logs" tab
3. Manually trigger: `curl -X POST https://truthboard-api.onrender.com/health/ingest`
4. Wait 5 min and check health again

### Scenario 2: `total_articles` not increasing

**What it means**: Data might not be fetching

**Fix**:
1. Check Render logs for fetch errors
2. Verify database is connected: Look for "database: connected" ✅
3. Manually trigger ingestion (see above)

### Scenario 3: Service shows as "crashed" in Render dashboard

**What it means**: The service went down (rare)

**Fix**:
1. Go to https://dashboard.render.com
2. Click "truthboard-api" service
3. Click "Reboot Instance" button
4. Wait 2 minutes for restart
5. Check health endpoint again

All of these scenarios are **extremely rare** if the system is running properly.

---

## What's Configured and Why

### Backend Configuration (Automatic)
- **Scheduler**: Every 15 minutes ✅ (hardcoded)
- **Data sources**: 5+ free sources ✅ (hardcoded)
- **Timeout**: 25 seconds ✅ (for Render resource limits)
- **Data retention**: 30 days ✅ (automatic cleanup)
- **Database**: PostgreSQL on Render ✅ (configured)

### Frontend Configuration (Automatic)
- **API endpoint**: Hardcoded to Render ✅
- **Auto-refresh**: 30 seconds ✅
- **Politics filter**: Enabled ✅
- **Data updates**: Real-time ✅

**No configuration needed on your end.**

---

## Optional Enhancements (If You Want Them)

### 1. Email Alerts (Optional)
Set `DISCORD_WEBHOOK_URL` environment variable to get alerts on errors.

Not recommended unless you want extra monitoring - system handles errors gracefully.

### 2. Tune Data Retention (Optional)
Currently keeps 30 days of articles.

To change (in backend/app/config.py):
```python
article_retention_days: int = 30  # Change to 60, 7, etc.
```

### 3. API Key for Extra Data Sources (Optional)
If you want NewsAPI data (higher article volume):
1. Get free API key from https://newsapi.org
2. Add to Render environment: `NEWSAPI_KEY=your_key`
3. Restart service

**Not necessary** - system works perfectly without it.

---

## Monitoring Options

### Option A: Do Nothing (Recommended)
Just let it run. Check health once a month if curious.

### Option B: Light Monitoring
- Bookmark: https://truthboard-api.onrender.com/health
- Check once a week (literally just visit the URL)
- Should always show healthy status ✅

### Option C: Detailed Monitoring
Monitor Render logs in dashboard (optional):
- https://dashboard.render.com/services/truthboard-api
- Click "Logs" tab
- You'll see ingestion happening every 15 minutes

---

## Cost Management

### What You're Paying For

**Render (Backend)**:
- Standard tier: ~$12/month (includes 2GB RAM, auto-runs your scheduler)
- Excellent for this workload

**Render Database (PostgreSQL)**:
- Starter plan: ~$15-20/month
- Currently holds ~4,500 articles, ~300 events
- Growing slowly (30-day retention keeps it manageable)

**Vercel (Frontend)**:
- Free tier for Next.js is usually sufficient
- Rarely exceeds free quota

**Total**: ~$27-35/month for a fully operational news event platform

### How to Reduce Costs

**Option 1**: Stay on Standard tier (current - recommended)
- Keeps system running smoothly
- Scheduler works reliably
- Cost is reasonable

**Option 2**: Downgrade to Basic Render tier (not recommended)
- Scheduler would be unreliable
- May have memory issues
- Would need to manually manage ingestion

**Recommendation**: Stick with Standard tier. Cost is worth the reliability.

---

## What If You Stop Using It?

### To Pause (Keep Data)
1. Go to Render dashboard
2. Click "truthboard-api" service
3. Click "Suspend" (not "Delete")
4. No cost while suspended
5. Can restart anytime

### To Fully Delete
1. Delete service on Render
2. Delete database on Render
3. All data is lost (no recovery)

---

## Emergency Contact (If Something's Wrong)

If your system ever has issues and you want to debug:

**Check these in order**:
1. Is Render service running? (Dashboard > truthboard-api > Status)
2. Is database connected? (Check health endpoint for `database: connected`)
3. Are there logs showing errors? (Dashboard > Logs tab)
4. Did scheduler run recently? (Check `worker_last_run` timestamp)

If all look OK, system is fine!

---

## Summary: What You Actually Need to Do

### Daily
Nothing. ✅

### Weekly
Nothing. ✅

### Monthly
Optionally check health endpoint once. ✅

### When paying Render bill
✅ Standard tier = Keep
❌ Don't downgrade
❌ Don't cancel

**That's it.**

---

## The Real Question: Do I Need to Do Anything?

**No.**

Your system is:
- ✅ Self-scheduling (every 15 minutes)
- ✅ Self-healing (errors handled gracefully)
- ✅ Self-cleaning (old data auto-deleted)
- ✅ Self-monitoring (logs available if needed)
- ✅ Fully automated (zero manual intervention)

**Just pay the Render bill and let it run.**

The only reason to check on it is if you're curious about the data or performance. The system will continue working perfectly whether you monitor it or not.

---

## Documentation for Reference

If you ever need to understand how it works:

1. **System status**: Check `/health` endpoint
2. **Data flow**: See `SYSTEM_NOW_OPERATIONAL.md`
3. **Bug fixes applied**: See `CRITICAL_BUGFIXES_APPLIED.md`
4. **Data sources**: See `SCHEDULER_FREE_SOURCES_FIX.md`
5. **Verification steps**: See `VERIFICATION_GUIDE.md`

---

**TL;DR: You can literally just leave it running forever. No maintenance required. Just pay the bill.**

🎉 Congratulations! You have a fully autonomous news event platform!
