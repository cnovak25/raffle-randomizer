# 🚂 Railway Deployment Guide

## Quick Deploy to Railway

1. **Sign up at Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign up with your GitHub account

2. **Deploy from GitHub:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `cnovak25/raffle-randomizer`
   - Railway will auto-detect and deploy

3. **Set Environment Variables:**
   - In Railway dashboard, go to your project
   - Click "Variables" tab
   - Add these variables:
     ```
     KPA_SESSION_COOKIE=6Pphk3dbK4Y-mvncorp
     PORT=8501
     PROXY_PORT=8000
     ```

4. **Access Your App:**
   - Railway will provide a URL like: `https://yourapp.up.railway.app`
   - Your raffle app will be fully functional with KPA photo integration!

## 🎯 Features Available on Railway:

✅ Full Streamlit raffle app
✅ KPA photo proxy server
✅ Celebration effects (countdown, balloons)
✅ Winner card generation with photos
✅ Auto-scaling and HTTPS
✅ Custom domain support

## 🔧 Configuration Files:

- `railway.toml` - Railway deployment configuration
- `start_services.py` - Starts both Streamlit and FastAPI
- `kpa_photo_proxy_railway.py` - Railway-optimized proxy server

## 💰 Cost:

- **Free tier**: 500 hours/month (plenty for raffle events)
- **Pro plan**: $5/month for unlimited usage

Your MVN Great Save Raffle will be fully functional with all features!
