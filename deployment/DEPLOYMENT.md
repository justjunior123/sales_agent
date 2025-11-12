# Deployment Guide

## Deploying to Render

### Prerequisites
- GitHub repository with code pushed
- Render account
- FMCSA API key

### Steps

#### 1. Prepare Repository
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### 2. Deploy to Render

**Option A: Using Render Dashboard (Recommended)**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `sales-agent-api`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

5. Add Environment Variables:
   - `FMCSA_API_KEY`: Your FMCSA API key
   - `DATABASE_PATH`: `./app/data/sales_agent.db`
   - `APP_ENV`: `production`

6. Click "Create Web Service"

7. Wait for deployment (usually 2-5 minutes)

8. Your API will be available at: `https://sales-agent-api.onrender.com`

**Option B: Using render.yaml (Blueprint)**

1. Push `deployment/render.yaml` to your repository
2. Go to Render Dashboard
3. Click "New +" → "Blueprint"
4. Select your repository
5. Render will automatically detect and deploy services defined in `render.yaml`

#### 3. Deploy Dashboard (Optional)

Repeat the same process for the Streamlit dashboard:
- **Name**: `sales-agent-dashboard`
- **Start Command**: `streamlit run streamlit/dashboard.py --server.port $PORT --server.address 0.0.0.0`

### Important Notes

**Cold Starts**: Render free tier spins down services after 15 minutes of inactivity. First request after inactivity will take ~30 seconds to spin up.

**Database Persistence**: SQLite database on Render free tier is ephemeral. For production:
- Use Render's PostgreSQL
- Or use external database service
- Or accept that data resets on deploys

**API Testing**: Once deployed, test with:
```bash
curl https://your-app.onrender.com/health
```

### Troubleshooting

**Build Fails**:
- Check Python version matches (3.11)
- Verify requirements.txt is correct
- Check build logs in Render dashboard

**Service Won't Start**:
- Verify start command is correct
- Check PORT environment variable is available
- Review service logs in Render dashboard

**Database Errors**:
- Ensure DATABASE_PATH is set correctly
- Check write permissions
- Verify SQLite is initialized properly
