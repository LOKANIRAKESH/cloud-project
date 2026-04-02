#!/usr/bin/env python
"""Azure CLI Deployment - Quick Reference"""

print('\n' + '='*80)
print('  🚀 AZURE CLI DEPLOYMENT - QUICK REFERENCE')
print('='*80 + '\n')

commands = [
    ("1. LOGIN", "az login", "Authenticate with Azure"),
    ("2. CREATE RESOURCE GROUP", "az group create --name StressDetectRG --location eastus", "Create RG"),
    ("3. CREATE DATABASE", "az postgres flexible-server create --resource-group StressDetectRG --name stressdetect-db --admin-user dbadmin --admin-password PASSWORD --sku-name Standard_B1ms --tier Burstable --storage-size 32", "Create PostgreSQL"),
    ("4. CREATE STORAGE", "az storage account create --name stressdetectstorage --resource-group StressDetectRG --sku Standard_LRS --kind StorageV2", "Create Storage"),
    ("5. CREATE APP PLAN", "az appservice plan create --name StressDetectPlan --resource-group StressDetectRG --sku FREE --is-linux", "FREE tier"),
    ("6. CREATE WEB APP", "az webapp create --resource-group StressDetectRG --plan StressDetectPlan --name stressdetect-api --runtime PYTHON:3.11", "Create App Service"),
    ("7. SET VARIABLES", "az webapp config appsettings set --resource-group StressDetectRG --name stressdetect-api --settings [variables]", "Configure env vars"),
    ("8. DEPLOY CODE", "az webapp deployment source config-zip --resource-group StressDetectRG --name stressdetect-api --src backend.zip", "Deploy backend"),
    ("9. CHECK LOGS", "az webapp log tail --resource-group StressDetectRG --name stressdetect-api", "View logs"),
]

for i, (name, cmd, desc) in enumerate(commands, 1):
    print(f"STEP {i}: {name}")
    print(f"Description: {desc}")
    print(f"Command:\n  {cmd}\n")

print('='*80)
print('  📊 DEPLOYMENT TIMELINE')
print('='*80)
print()
print('  Phase 1: Setup (Login) ........................ 1 min')
print('  Phase 2: Create Resources (RG→Storage) ...... 15 mins')
print('  Phase 3: App Service (Plan→Web App) ........ 10 mins')
print('  Phase 4: Set Environment Variables ......... 5 mins')
print('  Phase 5: Build Backend ..................... 5 mins')
print('  Phase 6: Deploy Backend ................... 30 mins')
print('  Phase 7: Build Frontend ................... 5 mins')
print('  Phase 8: Deploy Frontend (Portal) ........ 10 mins')
print('  Phase 9: Test Application ................ 15 mins')
print('  ────────────────────────────────────────────')
print('  TOTAL: ................................... ~2.5 hours')
print()

print('='*80)
print('  ✅ YOUR LIVE URLS (After Deployment)')
print('='*80)
print()
print('  Backend API: https://stressdetect-api.azurewebsites.net')
print('  API Docs:    https://stressdetect-api.azurewebsites.net/docs')
print('  Health:      https://stressdetect-api.azurewebsites.net/api/monitoring/health')
print('  Frontend:    Will be shown on Static Web App creation')
print()

print('='*80)
print('  📋 BEFORE YOU START')
print('='*80)
print()
print('  ✓ Azure CLI installed? (az --version)')
print('  ✓ Azure account? (with $100 credits)')
print('  ✓ Backend tested locally?')
print('  ✓ Frontend tested locally?')
print('  ✓ .env updated for production?')
print('  ✓ All credentials ready?')
print()

print('='*80)
print('  🎯 NEXT STEPS')
print('='*80)
print()
print('  1. Read: AZURE_CLI_STEP_BY_STEP.md')
print('  2. Copy the commands from that file')
print('  3. Run them one by one')
print('  4. Wait for each to complete')
print('  5. Test when done!')
print()

print('='*80)
print('  READY? Start with: az login')
print('='*80 + '\n')
