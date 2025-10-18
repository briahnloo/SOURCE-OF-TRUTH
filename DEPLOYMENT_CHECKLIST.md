# Truth Layer Deployment Checklist

Use this checklist when deploying to production.

## Pre-Deployment

### Code Preparation
- [ ] All tests passing locally (`make test`)
- [ ] No linter errors
- [ ] Latest changes committed to GitHub
- [ ] Local system works with `make dev`

### Configuration
- [ ] Chose cloud platform (Render/Railway/DigitalOcean)
- [ ] Registered domain OR using free subdomain
- [ ] Created production environment variables
- [ ] Configured DATABASE_URL for PostgreSQL
- [ ] Set ALLOWED_ORIGINS with production domain
- [ ] Added optional API keys (NewsAPI, Mediastack)

### Platform Setup
- [ ] Account created on chosen platform
- [ ] Payment method added (if required)
- [ ] GitHub repository connected
- [ ] PostgreSQL database provisioned

---

## Deployment Steps

### Database
- [ ] PostgreSQL database created
- [ ] Connection string copied
- [ ] Database accessible from services
- [ ] Tables auto-create on first backend start

### Backend Service
- [ ] Service created with correct Dockerfile path
- [ ] Environment variables configured
- [ ] Health check path set to `/health/ready`
- [ ] Service deployed successfully
- [ ] Logs show "Database initialized"
- [ ] Health endpoint returns 200: `curl https://backend-url/health`

### Worker Service
- [ ] Background worker service created
- [ ] Start command: `python -m app.workers.scheduler`
- [ ] Environment variables match backend
- [ ] Service running
- [ ] Logs show "Worker started"
- [ ] First ingestion cycle completed (check logs)

### Frontend Service
- [ ] Service created with correct Dockerfile path
- [ ] NEXT_PUBLIC_API_URL points to backend
- [ ] Service deployed successfully
- [ ] Can access UI in browser
- [ ] No console errors (check browser DevTools)

---

## Verification

### Functional Testing
- [ ] Frontend loads without errors
- [ ] Homepage shows hero section: "Welcome, Seekers of Knowledge"
- [ ] Navigation works (Confirmed, Developing, Underreported, Stats)
- [ ] Events display correctly (may be empty initially)
- [ ] Stats page shows system metrics
- [ ] API documentation accessible: `/docs`
- [ ] RSS feed works: `/feeds/verified.xml`

### Backend Health
- [ ] `/health` returns status: "healthy"
- [ ] `/health/live` returns status: "alive"
- [ ] `/health/ready` returns status: "ready"
- [ ] `/events` returns valid JSON
- [ ] `/events/stats/summary` shows statistics

### Worker Health
- [ ] Worker logs show ingestion cycles every 15 minutes
- [ ] Articles being fetched (check logs for "✅ GDELT", "✅ RSS", etc.)
- [ ] Events being created
- [ ] Scoring running
- [ ] No repeated errors in logs

### Data Pipeline
- [ ] Wait 15 minutes for first cycle
- [ ] Check `/health` - total_articles should increase
- [ ] Check `/events?status=all` - should have events
- [ ] Verify events have sources
- [ ] Check underreported detection working

---

## Post-Deployment

### Monitoring Setup
- [ ] UptimeRobot monitor added (prevents free tier sleep)
- [ ] Discord webhook working (if configured)
- [ ] Error tracking setup (Sentry, optional)
- [ ] Set calendar reminder for free tier expiration

### Performance
- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms
- [ ] No memory leaks (monitor for 24 hours)
- [ ] Database size reasonable (<100MB initially)

### Security
- [ ] HTTPS working (green padlock)
- [ ] HTTP redirects to HTTPS
- [ ] CORS only allows your domain
- [ ] No sensitive data in logs
- [ ] Environment variables not exposed

### Documentation
- [ ] Update README with live URL
- [ ] Add deployment date to docs
- [ ] Document any platform-specific quirks
- [ ] Create runbook for operations

---

## 24-Hour Monitoring

### Hour 1
- [ ] All services responding
- [ ] No error spikes in logs
- [ ] First ingestion cycle completed

### Hour 6
- [ ] Worker ran 24 ingestion cycles (every 15 min × 24 = 6 hours)
- [ ] Events accumulating
- [ ] No database connection errors
- [ ] Memory usage stable

### Hour 24
- [ ] System stable
- [ ] Data retention working (30-day cleanup)
- [ ] API response times consistent
- [ ] No unexpected costs

---

## Rollback Plan

If deployment fails:

1. **Check Logs**: Platform dashboard → Service → Logs
2. **Common Issues**:
   - Database URL wrong → Fix in env vars, redeploy
   - CORS error → Update ALLOWED_ORIGINS
   - Build failure → Check Dockerfile paths

3. **Emergency Rollback**:
   ```bash
   git revert HEAD
   git push origin main
   # Platform auto-deploys previous version
   ```

4. **Keep Local Running**: Your localhost version still works!

---

## Success Criteria

Deployment is successful when:

✅ Public URL accessible from any device/network  
✅ HTTPS enabled with valid certificate  
✅ All pages load without errors  
✅ Worker ingesting every 15 minutes  
✅ Events appearing and being scored  
✅ No errors in logs after 24 hours  
✅ Monitoring alerts configured  
✅ Automatic deployments working on git push  

**Congratulations! Truth Layer is now live for the world! 🎉**

---

## Maintenance

### Daily
- [ ] Check health endpoint
- [ ] Review error logs

### Weekly
- [ ] Verify data ingestion continuing
- [ ] Check database size
- [ ] Review performance metrics

### Monthly
- [ ] Verify backups working
- [ ] Check for security updates
- [ ] Review costs vs budget
- [ ] Update dependencies if needed

---

## Support Resources

- **Platform Support**: Check your platform's documentation
- **Truth Layer Docs**: See `/docs/` directory
- **GitHub Issues**: https://github.com/briahnloo/SOURCE-OF-TRUTH/issues
- **Community**: (Add Discord/forum when available)

