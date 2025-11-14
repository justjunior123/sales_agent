# First-Time Setup Guide

Complete setup instructions for running the HappyRobot Inbound Carrier Sales Agent locally or with Docker.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed ([python.org](https://www.python.org/downloads/))
- **Docker Desktop** (for Docker deployment) ([docker.com](https://www.docker.com/products/docker-desktop))
- **Git** installed
- **Supabase account** (free tier) ([supabase.com](https://supabase.com))
- **FMCSA API key** (obtain from [https://mobile.fmcsa.dot.gov/developer](https://mobile.fmcsa.dot.gov/developer))

---

## Part 1: Supabase Database Setup

### Why Supabase?
- Production-ready PostgreSQL database
- Free tier with 500MB storage
- Data persists between deployments
- Shared across API and Dashboard services

### Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click **"New Project"**
3. Fill in project details:
   - **Name**: `sales-agent-db` (or your preferred name)
   - **Database Password**: Generate a strong password (SAVE THIS!)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free
4. Click **"Create new project"**
5. Wait ~2 minutes for provisioning

### Step 2: Get Connection String

1. In your Supabase project, go to **Project Settings** → **Database**
2. Scroll down to **"Connection string"** section
3. Click on **"Connection Pooling"** tab (NOT "Direct Connection")
4. Select **"Transaction"** mode
5. Click on the **"URI"** tab
6. Copy the connection string - it looks like:
   ```
   postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

### Step 3: URL-Encode Your Password ⚠️ CRITICAL

**Why?** Special characters in passwords break PostgreSQL connection strings.

#### Common Characters That Need Encoding:

| Character | Encoded As | Example               | Becomes               |
|-----------|------------|----------------------|-----------------------|
| `=`       | `%3D`      | `Pass=123`           | `Pass%3D123`          |
| `%`       | `%25`      | `Pass%word`          | `Pass%25word`         |
| `^`       | `%5E`      | `Pass^123`           | `Pass%5E123`          |
| `[`       | `%5B`      | `[PassWord]`         | `%5BPassWord%5D`      |
| `]`       | `%5D`      |                      |                       |
| `@`       | `%40`      | `user@pass`          | `user%40pass`         |
| `!`       | `%21`      | `Pass!word`          | `Pass%21word`         |
| `#`       | `%23`      | `Pass#123`           | `Pass%23123`          |
| `$`       | `%24`      | `Pass$123`           | `Pass%24123`          |
| `&`       | `%26`      | `Pass&word`          | `Pass%26word`         |

#### Full Example:

**Original password:** `MyP@ss=word%123!`
**URL-encoded password:** `MyP%40ss%3Dword%25123%21`

**Original connection string:**
```
postgresql://postgres.xxx:MyP@ss=word%123!@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Correctly encoded connection string:**
```
postgresql://postgres.xxx:MyP%40ss%3Dword%25123%21@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

#### Quick Encoding Method:

**Option 1: Python (Recommended)**
```python
import urllib.parse
password = "YourPasswordHere"
encoded = urllib.parse.quote(password, safe='')
print(f"Encoded: {encoded}")
```

**Option 2: Online Tool**
- Use [urlencoder.org](https://www.urlencoder.org/) (paste password only, not full URL)

### Step 4: Create Database Table

1. In Supabase, go to **SQL Editor** (left sidebar)
2. Click **"New query"**
3. Paste this SQL:

```sql
CREATE TABLE call_logs (
    call_id TEXT PRIMARY KEY,
    carrier_mc TEXT NOT NULL,
    carrier_name TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    load_id TEXT,
    loadboard_rate FLOAT,
    agreed_rate FLOAT,
    negotiation_rounds INTEGER,
    outcome TEXT,
    sentiment TEXT,
    notes TEXT,
    call_duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_call_logs_timestamp ON call_logs(timestamp DESC);
CREATE INDEX idx_call_logs_outcome ON call_logs(outcome);
```

4. Click **"Run"** or press `Ctrl+Enter`
5. Verify: You should see "Success. No rows returned"
6. Go to **Table Editor** → You should see `call_logs` table

✅ **Supabase setup complete!**

---

## Part 2: Local Python Setup

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd sales_agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all Python packages including `psycopg2-binary` for PostgreSQL.

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your actual values:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. Update these values:

```env
# FMCSA API Configuration
FMCSA_API_KEY=your_actual_fmcsa_api_key_here
FMCSA_API_URL=https://mobile.fmcsa.dot.gov/qc/services/carriers

# Database Configuration - USE YOUR ENCODED PASSWORD
DATABASE_URL=postgresql://postgres.xxx:YOUR_ENCODED_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
PORT=8000
```

**⚠️ IMPORTANT:** Make sure you use the **URL-encoded password** from Step 3 of Part 1!

4. Save and close the file

### Step 5: Start Services

**Terminal 1 - Start API:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Terminal 2 - Start Dashboard:**
```bash
streamlit run streamlit/dashboard.py
```

You should see:
```
You can now view your Streamlit app in your browser.
URL: http://localhost:8501
```

### Step 6: Verify Setup

1. **Test API:**
   - Open browser: http://localhost:8000/docs
   - You should see Swagger API documentation

2. **Test Database Connection:**
   ```bash
   curl http://localhost:8000/api/v1/call_logs
   ```
   Expected response: `{"total_calls": 0, "status": "success", "calls": []}`

3. **Test Dashboard:**
   - Open browser: http://localhost:8501
   - You should see the dashboard (with no data yet)
   - In sidebar, find **"🎬 Demo Controls"**
   - Click **"📊 Load"** to populate 8 sample calls
   - Refresh the page - you should now see charts and metrics

✅ **Local setup complete!** Both services are running and connected to Supabase.

---

## Part 3: Docker Setup

### Step 1: Ensure Docker is Running

1. Open **Docker Desktop** application
2. Wait for Docker icon in menu bar/system tray
3. Verify Docker is ready:
   ```bash
   docker info
   ```
   Should show Docker version info (not an error).

### Step 2: Configure Environment

**Same as local setup** - ensure your `.env` file has the correct DATABASE_URL with encoded password.

Docker Compose will automatically read the `.env` file.

### Step 3: Stop Local Services (if running)

```bash
# Stop Python API (Ctrl+C in Terminal 1)
# Stop Streamlit (Ctrl+C in Terminal 2)
```

### Step 4: Build and Start Docker

```bash
# Build images and start containers
docker-compose up --build
```

**First time build takes 2-3 minutes** (downloads Python image, installs dependencies).

You should see:
```
sales_agent_api         | INFO:     Uvicorn running on http://0.0.0.0:8000
sales_agent_dashboard   | You can now view your Streamlit app in your browser.
```

### Step 5: Verify Docker Setup

1. **Check containers are running:**
   ```bash
   docker-compose ps
   ```
   Both `sales_agent_api` and `sales_agent_dashboard` should show "Up".

2. **Test API:**
   ```bash
   curl http://localhost:8000/api/v1/call_logs
   ```

3. **Test Dashboard:**
   - Open browser: http://localhost:8501
   - Use Demo Controls to load sample data

### Step 6: Manage Docker Services

```bash
# Stop containers (keeps data in Supabase)
docker-compose down

# Start containers (data persists!)
docker-compose up

# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs api
docker-compose logs dashboard
```

✅ **Docker setup complete!**

---

## Troubleshooting

### Issue 1: Password Authentication Failed

**Error:**
```
FATAL: password authentication failed for user "postgres"
```

**Cause:** Password not URL-encoded correctly.

**Solution:**
1. Double-check your password encoding (see Part 1, Step 3)
2. Common mistake: Using brackets `[` `]` that Supabase UI shows - **remove them**!
   - Wrong: `[MyPassword]`
   - Right: `MyPassword`
3. Re-encode the password without brackets
4. Update `.env` with corrected DATABASE_URL
5. Restart services

### Issue 2: UTF-8 Decode Error

**Error:**
```
'utf-8' codec can't decode byte 0xf4 in position X
```

**Cause:** Special character in password (like `%f4`) not properly encoded.

**Solution:**
1. The `%` character itself needs encoding: `%` → `%25`
2. Example: `Pass%word` → `Pass%25word`
3. Use Python script from Part 1, Step 3 to encode
4. Update `.env` and restart

### Issue 3: Connection Timeout

**Error:**
```
connection timeout
```

**Solution:**
1. Check your internet connection
2. Verify Supabase project is running (check supabase.com dashboard)
3. Try using Direct Connection string instead of Pooling:
   - In Supabase: Settings → Database → "Direct Connection" → "URI"
   - Use port `5432` instead of `6543`
4. Check if corporate firewall is blocking port 6543

### Issue 4: Table Does Not Exist

**Error:**
```
Table 'call_logs' does not exist
```

**Solution:**
1. Go to Supabase → SQL Editor
2. Run the CREATE TABLE SQL from Part 1, Step 4
3. Verify in Table Editor that table exists
4. Restart services

### Issue 5: Pydantic Validation Error

**Error:**
```
Input should be a valid string [type=string_type, input_value=datetime.datetime...]
```

**Cause:** Old code version without PostgreSQL datetime handling.

**Solution:**
1. Ensure you're on latest code
2. Check `app/api/models.py` has `Union[str, datetime]` for timestamp field
3. If using Docker: `docker-compose up --build` to rebuild with latest code

### Issue 6: Docker Daemon Not Running

**Error:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
1. Open Docker Desktop application
2. Wait for it to fully start
3. Verify with: `docker info`
4. Try command again

### Issue 7: Port Already in Use

**Error:**
```
Error starting userland proxy: Bind for 0.0.0.0:8000: address already in use
```

**Solution:**
1. Stop local Python services (Ctrl+C)
2. Find and kill process:
   ```bash
   # On macOS/Linux:
   lsof -ti:8000 | xargs kill -9
   lsof -ti:8501 | xargs kill -9

   # On Windows:
   netstat -ano | findstr :8000
   taskkill /PID <PID_NUMBER> /F
   ```
3. Try starting Docker again

### Issue 8: Demo Controls Not Working

**Symptom:** Click "Load" button, nothing happens or infinite loading.

**Solution:**
1. Open browser console (F12) to check for errors
2. Verify API is accessible: `curl http://localhost:8000/api/v1/call_logs`
3. Check `API_BASE_URL` environment variable:
   - Local: Not needed (dashboard uses direct DB connection)
   - Docker: Should be `http://api:8000/api/v1`
4. Refresh browser page after clicking Load/Clear

---

## Testing Your Setup

### Quick Test Script

Run this to verify everything works:

```bash
# Test 1: Database connection
python3 << 'EOF'
from dotenv import load_dotenv
load_dotenv()
from app.data.db import get_connection
conn = get_connection()
print("✅ Database connected!")
conn.close()
EOF

# Test 2: Load sample data
python3 << 'EOF'
from dotenv import load_dotenv
load_dotenv()
from tests.test_core import populate_database
success, message = populate_database()
print(f"{'✅' if success else '❌'} {message}")
EOF

# Test 3: Query data
curl http://localhost:8000/api/v1/call_logs | python3 -m json.tool
```

Expected output:
```
✅ Database connected!
✅ Successfully loaded 8 sample calls
{
    "total_calls": 8,
    "status": "success",
    "calls": [...]
}
```

---

## Next Steps

### For Local Development
1. Make code changes
2. Services auto-reload (API has `--reload`, Streamlit detects changes)
3. Test in browser
4. Commit changes

### For Docker Development
1. Make code changes
2. Rebuild: `docker-compose up --build`
3. Test in browser
4. Commit changes

### For Production Deployment
See `deployment/DEPLOYMENT.md` for Render deployment instructions.

---

## Need Help?

1. **Check this troubleshooting section first** - most issues covered above
2. **Review logs:**
   - Local: Check terminal output
   - Docker: `docker-compose logs`
3. **Verify Supabase:**
   - Check project is running
   - Check table exists
   - Test connection string manually
4. **Check `.env` file:**
   - Password properly encoded
   - No extra spaces
   - File saved correctly

---

## Security Notes

- **Never commit `.env` file** to git (it's in `.gitignore`)
- **Never share your DATABASE_URL** publicly
- **Never share your FMCSA_API_KEY** publicly
- **Use `.env.example`** as template for others
- **Rotate credentials** if accidentally exposed
