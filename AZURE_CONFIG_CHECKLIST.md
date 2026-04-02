# ✅ STEP-BY-STEP AZURE CONFIGURATION CHECKLIST

---

## 📋 BEFORE DEPLOYMENT - CONFIGURATION CHANGES

### Step 1: Update backend/.env (Local)

```bash
# Open: backend/.env

# CHANGE (Line 1-2):
ENVIRONMENT=development        # ← CHANGE TO: production
PORT=8001                     # ← CHANGE TO: 8000

# CHANGE (Last line):
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
# ↓ CHANGE TO:
ALLOWED_ORIGINS=https://stressdetect.azurestaticwebsites.net
```

✅ Do this now before deploying

---

### Step 2: Generate Azure PostgreSQL Connection String

You'll need this during Azure deployment. Format:
```
postgresql://dbadmin:PASSWORD@stressdetect-db.postgres.database.azure.com/stressdetect
```

**How to get it:**
1. Deploy Azure PostgreSQL (first step in MASTER_DEPLOYMENT_CHECKLIST.md)
2. Get hostname: `stressdetect-db.postgres.database.azure.com`
3. Get username: `dbadmin`
4. Use password you created during setup

**Example:**
```
postgresql://dbadmin:YourPassword123!@stressdetect-db.postgres.database.azure.com/stressdetect
```

---

### Step 3: Set Variables in Azure Portal (Option A - Easiest)

**After deploying to Azure App Service:**

1. Go to: https://portal.azure.com
2. Search: "App Services"
3. Click: `stressdetect-api`
4. Left menu: **Settings → Configuration**
5. Click: **New application setting**
6. Add each variable:

| Name | Value |
|------|-------|
| `ENVIRONMENT` | `production` |
| `PORT` | `8000` |
| `ALLOWED_ORIGINS` | `https://stressdetect.azurestaticwebsites.net` |
| `DATABASE_URL` | `postgresql://dbadmin:PASSWORD@stressdetect-db.postgres.database.azure.com/stressdetect` |
| `AZURE_FACE_API_KEY` | (from your .env) |
| `AZURE_FACE_ENDPOINT` | (from your .env) |
| `AZURE_TEXT_ANALYTICS_KEY` | (from your .env) |
| `AZURE_TEXT_ANALYTICS_ENDPOINT` | (from your .env) |
| `AZURE_SIGNALR_CONNECTION_STRING` | (from your .env) |
| `AWS_ACCESS_KEY_ID` | (from your .env) |
| `AWS_SECRET_ACCESS_KEY` | (from your .env) |
| `AWS_SESSION_TOKEN` | (from your .env) |
| `AWS_S3_BUCKET` | `stressdetect-exports` |
| `GMAIL_ADDRESS` | `lokanirakeshds@gmail.com` |
| `GMAIL_APP_PASSWORD` | (from your .env) |
| `JWT_SECRET` | (from your .env) |

7. Click: **Save**

---

### Step 4: Set Variables via Azure CLI (Option B - If preferred)

```bash
az webapp config appsettings set \
  --resource-group StressDetectRG \
  --name stressdetect-api \
  --settings \
    ENVIRONMENT="production" \
    PORT="8000" \
    ALLOWED_ORIGINS="https://stressdetect.azurestaticwebsites.net" \
    DATABASE_URL="postgresql://dbadmin:PASSWORD@stressdetect-db.postgres.database.azure.com/stressdetect" \
    AZURE_FACE_API_KEY="your_api_key" \
    AZURE_FACE_ENDPOINT="your_endpoint" \
    AZURE_TEXT_ANALYTICS_KEY="your_key" \
    AZURE_TEXT_ANALYTICS_ENDPOINT="your_endpoint" \
    AZURE_SIGNALR_CONNECTION_STRING="your_connection_string" \
    AWS_ACCESS_KEY_ID="your_key_id" \
    AWS_SECRET_ACCESS_KEY="your_secret" \
    AWS_SESSION_TOKEN="your_token" \
    AWS_S3_BUCKET="stressdetect-exports" \
    GMAIL_ADDRESS="lokanirakeshds@gmail.com" \
    GMAIL_APP_PASSWORD="your_password" \
    JWT_SECRET="your_secret"
```

---

## 📊 CONFIGURATION MATRIX

| Setting | Local Dev | Azure Production | Where to Set |
|---------|-----------|------------------|--------------|
| ENVIRONMENT | `development` | `production` | .env + Azure Portal |
| PORT | `8001` | `8000` | .env + Azure Portal |
| ALLOWED_ORIGINS | `localhost:5173` | Azure frontend URL | .env + Azure Portal |
| DATABASE_URL | (optional) | PostgreSQL connection | Azure Portal only |
| All Azure Keys | Same | Same | Azure Portal |
| All AWS Keys | Same | Same | Azure Portal |
| Gmail Settings | Same | Same | Azure Portal |

---

## ✅ COMPLETE CONFIGURATION CHECKLIST

### Before Azure Deployment:
- [ ] Update ENVIRONMENT to `production` in .env
- [ ] Update PORT to `8000` in .env
- [ ] Update ALLOWED_ORIGINS to Azure URL in .env
- [ ] Commit to Git
- [ ] Test locally: `python app.py`

### During Azure Deployment:
- [ ] Create PostgreSQL database (note credentials)
- [ ] Create App Service
- [ ] Deploy code via zip

### After Azure Deployment:
- [ ] Open Azure Portal
- [ ] Go to App Service → Configuration
- [ ] Add all 15+ application settings
- [ ] Click Save
- [ ] Wait for app to restart

### Testing After Configuration:
- [ ] Test API: `https://stressdetect-api.azurewebsites.net/api/monitoring/health`
- [ ] Status should be: `{"status": "healthy"}`
- [ ] Test Frontend: `https://stressdetect.azurestaticwebsites.net`
- [ ] Try to register user
- [ ] Try to login
- [ ] Try to use features

---

## 🚨 COMMON ISSUES & FIXES

### Issue: 500 Error on API
**Cause**: Environment variables not set  
**Fix**: Check Azure Portal → Configuration → App Settings

### Issue: CORS Error
**Cause**: ALLOWED_ORIGINS not set correctly  
**Fix**: Verify URL is: `https://stressdetect.azurestaticwebsites.net`

### Issue: Database Connection Failed
**Cause**: DATABASE_URL incorrect or missing  
**Fix**: Verify format: `postgresql://user:pass@host/db`

### Issue: AWS Services Not Working
**Cause**: Credentials not set in Azure  
**Fix**: Copy AWS credentials from .env to Azure Portal

---

## 📚 KEY DIFFERENCES

### Local Development
```env
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
DATABASE_URL=local_or_none
PORT=8001
```

### Azure Production
```env
ENVIRONMENT=production
ALLOWED_ORIGINS=https://stressdetect.azurestaticwebsites.net
DATABASE_URL=postgresql://...@stressdetect-db.postgres.database.azure.com/...
PORT=8000
```

---

## 🎯 DEPLOYMENT FLOW

```
1. Update .env locally
2. Commit to Git
3. Deploy backend to Azure
4. Set environment variables in Azure Portal
5. Verify health endpoint
6. Deploy frontend to Azure Static Web App
7. Test full application
8. Demo for viva!
```

---

## ✨ READY TO CONFIGURE?

1. ✅ Read this guide
2. ✅ Update .env for production
3. ✅ Follow MASTER_DEPLOYMENT_CHECKLIST.md
4. ✅ Set variables in Azure Portal
5. ✅ Test live application

**Time needed: ~5 minutes for configuration changes**

---

**See also:** [AZURE_CONFIGURATION_GUIDE.md](AZURE_CONFIGURATION_GUIDE.md) for detailed info
