# Production Deployment Guide

Complete guide for deploying the HappyRobot Sales Agent to Render with Supabase PostgreSQL.

---

## Prerequisites

Before deploying to production, ensure you have:

1. **Supabase Account** with configured project ([supabase.com](https://supabase.com))
2. **Render Account** ([render.com](https://render.com))
3. **GitHub Repository** with code pushed
4. **FMCSA API Key** from [FMCSA Developer Portal](https://mobile.fmcsa.dot.gov/developer)

> **📖 First-time setup?** Complete [SETUP.md](../SETUP.md) locally first to verify everything works before deploying.

---

## Part 1: Supabase Production Database

### Why Supabase for Production?

- **Data Persistence**: Survives Render deployments and restarts
- **Shared Database**: Both API and Dashboard connect to same data source
- **Free Tier**: 500MB storage, perfect for POC
- **Connection Pooling**: Optimized for serverless deployments

### Step 1: Verify Supabase Setup

If you already completed [SETUP.md](../SETUP.md), you should have:
- ✅ Supabase project created
- ✅ `call_logs` table created
- ✅ Connection string (with encoded password)

If not, go to [SETUP.md - Part 1](../SETUP.md#part-1-supabase-database-setup) first.

### Step 2: Prepare Production Connection String

1. In Supabase, go to **Project Settings** → **Database**
2. Under **Connection string** → **Connection Pooling** tab
3. Select **Transaction** mode
4. Click **URI** tab
5. Copy the connection string:
   ```
   postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

6. **⚠️ CRITICAL**: URL-encode your password (same as local setup):

**Quick Encoding with Python:**
```bash
python3 << 'EOF'
import urllib.parse
password = "YourActualPasswordHere"
encoded = urllib.parse.quote(password, safe='')
print(f"Encoded password: {encoded}")
EOF
```

**Common Character Encodings:**
- `=` → `%3D`
- `%` → `%25` (encode the percent itself!)
- `^` → `%5E`
- `[` → `%5B`
- `]` → `%5D`
- `@` → `%40`

7. Replace `[YOUR-PASSWORD]` in the connection string with your **encoded** password:
   ```
   postgresql://postgres.xxx:YOUR_ENCODED_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

8. **Save this connection string securely** - you'll add it to Render in the next section.

---

## Part 2: Deploy API to Render

### Option A: Using Render Dashboard (Recommended)

#### Step 1: Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the `sales_agent` repository

#### Step 2: Configure Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `sales-agent-api` |
| **Region** | Oregon (US West) or closest to you |
| **Branch** | `main` |
| **Root Directory** | Leave blank |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free |

#### Step 3: Add Environment Variables

Click **"Add Environment Variable"** for each:

| Key | Value |
|-----|-------|
| `FMCSA_API_KEY` | Your actual FMCSA API key |
| `DATABASE_URL` | Your Supabase connection string (with encoded password!) |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |

**⚠️ CRITICAL**: Double-check `DATABASE_URL` has the **encoded password**, not the raw password.

#### Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will build and deploy (takes 2-5 minutes first time)
3. Watch the logs for any errors
4. Once deployed, you'll see: `https://sales-agent-api.onrender.com`

#### Step 5: Verify API

Test your deployed API:

```bash
# Test health endpoint
curl https://sales-agent-api.onrender.com/api/v1/call_logs

# Expected response:
# {"total_calls": 0, "status": "success", "calls": []}
```

If you get this response, your API is deployed and connected to Supabase! ✅

### Option B: Using render.yaml (Blueprint)

**Faster for deploying both API and Dashboard together.**

#### Step 1: Update render.yaml

The `deployment/render.yaml` file is already configured for Supabase. Review it to ensure service names are correct.

#### Step 2: Deploy via Blueprint

1. Push latest code to GitHub:
   ```bash
   git add .
   git commit -m "Deploy to Render with Supabase"
   git push origin main
   ```

2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **"New +"** → **"Blueprint"**
4. Select your repository
5. Render detects `deployment/render.yaml` automatically
6. Click **"Apply"**

#### Step 3: Add Environment Variables

Render creates both services but you need to add environment variables manually:

**For `sales-agent-api` service:**
1. Go to service → **Environment** tab
2. Add the same variables as Option A above

**For `sales-agent-dashboard` service:**
1. Go to service → **Environment** tab
2. Add:
   - `DATABASE_URL`: Same Supabase connection string as API
   - `APP_ENV`: `production`

#### Step 4: Trigger Deploy

After adding environment variables:
1. Go to each service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait for both to finish

---

## Part 3: Deploy Dashboard to Render

### Step 1: Create Dashboard Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Select same GitHub repository

### Step 2: Configure Dashboard

| Setting | Value |
|---------|-------|
| **Name** | `sales-agent-dashboard` |
| **Region** | Same as API (Oregon recommended) |
| **Branch** | `main` |
| **Root Directory** | Leave blank |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run streamlit/dashboard.py --server.port $PORT --server.address 0.0.0.0` |
| **Plan** | Free |

### Step 3: Add Environment Variables

| Key | Value |
|-----|-------|
| `DATABASE_URL` | **Same Supabase connection string as API** |
| `APP_ENV` | `production` |

### Step 4: Deploy and Verify

1. Click **"Create Web Service"**
2. Wait for deployment
3. Open dashboard URL: `https://sales-agent-dashboard.onrender.com`
4. You should see the dashboard (empty initially)
5. Use **Demo Controls** in sidebar to load sample data
6. Verify charts and metrics display correctly

---

## Part 4: Testing Production Deployment

### Quick Production Test

Run these tests to verify everything works:

**1. Test API Connection**
```bash
curl https://sales-agent-api.onrender.com/api/v1/call_logs | python3 -m json.tool
```

**2. Test Database Write**
```bash
curl -X POST https://sales-agent-api.onrender.com/api/v1/verify_carrier \
  -H "Content-Type: application/json" \
  -d '{"mc_number": "MC123456"}'
```

**3. Test Dashboard**
- Open dashboard URL in browser
- Click "Load" in Demo Controls
- Refresh page - should show 8 sample calls
- Verify metrics, charts, and recent calls table

**4. Test Data Persistence**
- In Render Dashboard, manually restart API service
- Check dashboard - data should still be there (from Supabase)

---

## Important Production Notes

### Cold Starts

**Render Free Tier Behavior:**
- Services spin down after 15 minutes of inactivity
- First request after inactivity takes ~30-60 seconds to spin up
- Subsequent requests are fast

**What this means:**
- First call of the day may time out
- Retry immediately - second call will work
- Consider upgrading to paid tier for always-on services

### Database Persistence

**✅ With Supabase:**
- Data persists across deployments
- Data persists across service restarts
- Both API and Dashboard share same data
- Data survives Render's ephemeral filesystem

**This is production-ready!**

### Service URLs

After deployment, your services will be at:
- **API**: `https://sales-agent-api.onrender.com`
- **API Docs**: `https://sales-agent-api.onrender.com/docs`
- **Dashboard**: `https://sales-agent-dashboard.onrender.com`

### Monitoring

**View Logs:**
1. Go to service in Render Dashboard
2. Click **"Logs"** tab
3. Real-time log streaming
4. Filter by severity (INFO, ERROR, etc.)

**Check Metrics:**
1. Click **"Metrics"** tab
2. View CPU, memory, response times
3. Identify performance issues

---

## Troubleshooting

### Issue 1: Build Fails

**Error:**
```
ERROR: Could not find a version that satisfies the requirement psycopg2-binary==2.9.9
```

**Solution:**
1. Verify `requirements.txt` includes `psycopg2-binary==2.9.9`
2. Check Python version is 3.11 in Render settings
3. Review build logs for specific error
4. Try manual deploy: **"Manual Deploy"** → **"Clear build cache & deploy"**

### Issue 2: Service Won't Start

**Error:**
```
Error: DATABASE_URL environment variable not set
```

**Solution:**
1. Go to service → **Environment** tab
2. Verify `DATABASE_URL` is set
3. Check for typos in environment variable name (case-sensitive!)
4. Click **"Manual Deploy"** to restart with new variables

### Issue 3: Database Connection Failed

**Error (in logs):**
```
FATAL: password authentication failed for user "postgres"
```

**Solution:**
1. **Password not URL-encoded correctly**
   - Go to service → Environment → Edit `DATABASE_URL`
   - Re-encode password using Python script from Part 1, Step 2
   - Remove any brackets `[` `]` around password
   - Save and redeploy

2. **Wrong connection string format**
   - Verify using **Connection Pooling** (port 6543), not Direct Connection
   - Format: `postgresql://postgres.xxx:ENCODED_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

### Issue 4: Cold Start Timeout

**Error:**
```
Request timeout (504 Gateway Timeout)
```

**Solution:**
1. This is normal for first request after inactivity (Render free tier)
2. **Wait 60 seconds**, then retry request
3. Service is waking up from sleep
4. Subsequent requests will be fast
5. To avoid: Upgrade to Render paid plan for always-on services

### Issue 5: Dashboard Shows No Data

**Symptom:** Dashboard loads but shows zero calls, no charts

**Solution:**
1. **Check DATABASE_URL is set** in dashboard service environment
2. **Verify same DATABASE_URL** as API (copy-paste from API service)
3. **Test API endpoint** to confirm data exists:
   ```bash
   curl https://sales-agent-api.onrender.com/api/v1/call_logs
   ```
4. **Use Demo Controls** in dashboard sidebar to load sample data
5. **Refresh browser** after loading data

### Issue 6: Table Does Not Exist

**Error (in logs):**
```
relation "call_logs" does not exist
```

**Solution:**
1. Table not created in Supabase
2. Go to Supabase → SQL Editor
3. Run table creation SQL from [SETUP.md - Part 1, Step 4](../SETUP.md#step-4-create-database-table)
4. Verify table exists in Table Editor
5. Restart Render service

### Issue 7: FMCSA API Errors

**Error:**
```
FMCSA API request failed: 401 Unauthorized
```

**Solution:**
1. Verify `FMCSA_API_KEY` environment variable is set correctly
2. Check API key is valid (not expired)
3. Test key locally first before deploying
4. Check FMCSA API status (may be down temporarily)

### Issue 8: Logs Show UTF-8 Errors

**Error:**
```
'utf-8' codec can't decode byte 0xf4
```

**Solution:**
1. **Password encoding issue** (same as local troubleshooting)
2. Special character in password not properly encoded
3. Re-encode password with Python script
4. **Critical**: The `%` character itself must be encoded as `%25`
5. Example: `Pass%word` → `Pass%25word`
6. Update `DATABASE_URL` and redeploy

---

## Updating Production

### Deploy Code Changes

**Option 1: Automatic Deploy (Recommended)**
1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "Update feature X"
   git push origin main
   ```
2. Render automatically detects and deploys changes
3. Watch logs to verify successful deployment

**Option 2: Manual Deploy**
1. Go to service in Render Dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Select commit to deploy
4. Click **"Deploy"**

### Update Environment Variables

1. Go to service → **Environment** tab
2. Edit or add variables
3. Click **"Save Changes"**
4. Service automatically restarts with new variables

### Database Migrations

If you need to modify the database schema:

1. **Write SQL migration**:
   ```sql
   ALTER TABLE call_logs ADD COLUMN new_field TEXT;
   ```

2. **Run in Supabase SQL Editor**:
   - Go to Supabase → SQL Editor
   - Paste migration SQL
   - Click "Run"

3. **Update code** to use new schema
4. **Deploy code changes** to Render
5. **No downtime** - Supabase changes are immediate

---

## Security Best Practices

### Environment Variables
- ✅ **Never commit** `.env` file to git (in `.gitignore`)
- ✅ **Never expose** `DATABASE_URL` publicly
- ✅ **Never share** `FMCSA_API_KEY` in screenshots or videos
- ✅ **Use Render's environment variables** - they're encrypted at rest
- ✅ **Rotate credentials** if accidentally exposed

### Supabase Security
- ✅ **Use connection pooling** (port 6543) for serverless
- ✅ **Enable RLS** (Row Level Security) in Supabase for multi-tenant apps
- ✅ **Restrict API access** to specific IPs if possible
- ✅ **Monitor access logs** in Supabase dashboard

### Render Security
- ✅ **Use HTTPS** (Render provides this automatically)
- ✅ **Enable health checks** for automatic restart on failure
- ✅ **Review logs regularly** for suspicious activity
- ✅ **Keep dependencies updated** (`pip install --upgrade`)

---

## Cost Optimization

### Render Free Tier Limits
- **750 hours/month** per service (enough for POC)
- **Services spin down** after 15 minutes inactivity
- **No custom domains** on free tier
- **Shared resources** (slower than paid)

### Supabase Free Tier Limits
- **500MB database** storage
- **1GB file storage**
- **50,000 monthly active users**
- **More than enough** for technical challenge POC

### When to Upgrade
- **High traffic** (more than 750 hours/month per service)
- **Need always-on** services (no cold starts)
- **Custom domain** required
- **More database storage** needed

---

## Next Steps

After successful production deployment:

1. ✅ **Test all API endpoints** using Swagger docs at `/docs`
2. ✅ **Load demo data** in dashboard to verify functionality
3. ✅ **Configure HappyRobot agent** to use production API URL
4. ✅ **Run test calls** through HappyRobot platform
5. ✅ **Monitor logs** during test calls
6. ✅ **Record demo video** showing full workflow
7. ✅ **Prepare deliverables** (email, build description, repository link)

---

## Support Resources

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Streamlit Documentation**: [docs.streamlit.io](https://docs.streamlit.io)

---

## Rollback Strategy

If production deployment has issues:

**Option 1: Rollback to Previous Commit**
1. In Render Dashboard → Service
2. Click **"Manual Deploy"**
3. Select previous working commit
4. Click **"Deploy"**

**Option 2: Rollback Environment Variables**
1. Go to service → **Environment** tab
2. Click on variable → **View History**
3. Restore previous value
4. Save and restart

**Option 3: Database Rollback**
1. Supabase has **Point-in-Time Recovery** (paid feature)
2. Free tier: Manually fix data with SQL
3. Or clear and reload from backup

---

## Checklist Before Going Live

- [ ] Supabase project created and table schema deployed
- [ ] Connection string tested locally first
- [ ] Password properly URL-encoded in DATABASE_URL
- [ ] FMCSA API key verified and working
- [ ] API service deployed and health check passes
- [ ] Dashboard service deployed and displays data
- [ ] Both services connect to same Supabase database
- [ ] Demo data loads successfully
- [ ] Cold start behavior tested and documented
- [ ] Logs reviewed for errors
- [ ] All environment variables secured (not in git)
- [ ] Backup plan if deployment fails
