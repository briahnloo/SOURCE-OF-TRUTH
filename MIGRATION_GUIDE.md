# 📦 Migrate Your Local Data to Production

Your local database has **297 events** and **4,901 articles**. This guide will upload all of them to your production PostgreSQL database on Render.

---

## ✅ What Will Be Migrated

- ✅ All 297 events with all computed data
- ✅ All 4,901 articles linked to those events
- ✅ All LLM outputs (conflict explanations, bias compass scores)
- ✅ All state data (timestamps, categories, truth scores, etc.)
- ✅ All relationships between articles and events

**Nothing is deleted from your local database** - this is a one-way copy.

---

## 🚀 How to Migrate (3 Steps)

### Step 1: Get Your Database Connection String

From the DEPLOYMENT_README.md, your PostgreSQL connection string is:

```
postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer
```

**Keep this handy** - you'll need it in Step 2.

### Step 2: Set Environment Variable Locally

Open your terminal and run this command:

```bash
export DATABASE_URL="postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer"
```

**Note**: Replace the connection string with your actual one if it's different.

### Step 3: Run the Migration Script

From the project root directory, run:

```bash
cd /Users/bzliu/Desktop/EXTRANEOUS_CODE/SINGLE\ SOURCE\ OF\ TRUTH

python backend/scripts/migrate_sqlite_to_postgres.py
```

**What you'll see:**

```
============================================================
SQLite → PostgreSQL Migration
============================================================
✓ Found SQLite database at ...
✓ Connected to PostgreSQL at dpg-d3qr8o56ubrc73868q20-a

📊 Local SQLite Database:
   Events: 297
   Articles: 4901

🔄 Migrating 297 events...
   ✓ Inserted 50/297 events
   ✓ Inserted 100/297 events
   ✓ Inserted 150/297 events
   ✓ Inserted 200/297 events
   ✓ Inserted 250/297 events
✓ Successfully migrated 297 events

🔄 Migrating 4901 articles...
   ✓ Inserted 500/4901 articles
   ✓ Inserted 1000/4901 articles
   ... (continues)
✓ Successfully migrated 4901 articles

✅ Migration Verification:
   Events:   297 → 297 ✓
   Articles: 4901 → 4901 ✓

🎉 Migration successful!
Your production database is now populated! 🚀
Visit: https://truthboard.vercel.app
```

---

## ⏱️ How Long Does It Take?

- **Connecting**: 2-3 seconds
- **Migrating 297 events**: ~5 seconds
- **Migrating 4,901 articles**: ~30-45 seconds
- **Total**: ~1 minute

---

## ✅ Verify the Migration Worked

After the script completes, visit your website:

```
https://truthboard.vercel.app
```

You should now see:
- ✅ Homepage with "Top Confirmed Events"
- ✅ Articles showing in the event cards
- ✅ All pages (developing, conflicts, stats) populated with data
- ✅ Search functionality returning results

---

## 🔧 Troubleshooting

### Issue: "Connection refused" or "Could not connect to database"

**Solution**: Check your DATABASE_URL environment variable:

```bash
# Verify it's set
echo $DATABASE_URL

# Should output: postgresql://truthlayer:...
```

If not set, run this command again:

```bash
export DATABASE_URL="postgresql://truthlayer:hLx2iGTigwwUpLwH8WnwMzpNrJKpsSDM@dpg-d3qr8o56ubrc73868q20-a/truthlayer"
```

### Issue: "SQLite database not found"

**Solution**: Make sure you're running from the project root directory:

```bash
cd /Users/bzliu/Desktop/EXTRANEOUS_CODE/SINGLE\ SOURCE\ OF\ TRUTH
pwd  # Should show the project directory

# Then run:
python backend/scripts/migrate_sqlite_to_postgres.py
```

### Issue: "psycopg2 not found"

**Solution**: Install the backend dependencies:

```bash
cd backend
pip install -e .
```

Then try the migration again.

### Issue: "Duplicate key" errors

**Solution**: This is normal if you run the script twice. The script has `ON CONFLICT` logic that updates existing records instead of creating duplicates. Just let it finish.

---

## 🔄 How the Migration Works

The script:

1. **Connects to your local SQLite database** (`data/app.db`)
2. **Reads all 297 events** with all their computed fields
3. **Reads all 4,901 articles** with their relationships to events
4. **Connects to your production PostgreSQL database** on Render
5. **Inserts all events** in batches (with duplicate handling)
6. **Inserts all articles** in batches (with duplicate handling)
7. **Verifies** that all records were inserted successfully
8. **Closes connections** cleanly

The data is copied as-is - no transformation needed because SQLite and PostgreSQL use compatible data types for your schema.

---

## ❓ FAQ

**Q: Will this delete my local database?**
A: No. The migration only reads from your local database and writes to the remote one.

**Q: What if I run the migration twice?**
A: It's safe. The script uses `ON CONFLICT` logic that updates existing records instead of creating duplicates.

**Q: Can I undo the migration?**
A: Yes - log into Render, go to PostgreSQL, and click "Restore from backup". Render saves daily backups.

**Q: Why isn't my data showing up on the website?**
A: The website caches results. Try:
1. Hard refresh: Press Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Wait 30 seconds and reload
3. Check the browser console for errors (F12)

**Q: Can I add new data after migration?**
A: Yes! Both your local and production databases will continue to work independently. New data in production won't sync back to local.

**Q: How do I keep them in sync?**
A: Re-run this migration script occasionally to push local updates to production. Or set up a scheduled job on your backend.

---

## 📝 After Migration

Once your production database is populated:

1. **Update your backend** to continue ingesting new data:
   - The lightweight scheduler (2 sources, 60-min window) runs periodically
   - Or manually trigger new data ingestion

2. **Monitor your data**:
   - Homepage should show recent political events
   - Search should return results
   - Stats page should show charts

3. **Optional: Keep in sync**:
   - If you want production to stay in sync with local development, run this migration script on a schedule
   - Or set up a cron job: `0 */6 * * * python backend/scripts/migrate_sqlite_to_postgres.py`

---

## 🎉 Success!

Once migration completes, your production Truthboard is fully populated with your local data!

**Next steps:**
- [ ] Run: `python backend/scripts/migrate_sqlite_to_postgres.py`
- [ ] Verify data shows up at `https://truthboard.vercel.app`
- [ ] Test search, filters, and all pages
- [ ] Share the URL with others!

---

*Migration Script: `backend/scripts/migrate_sqlite_to_postgres.py`*
*Created: October 23, 2025*
