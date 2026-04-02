# Stress Detection System — Azure Cloud Project

A real-time **stress detection web application** that uses your webcam and **Azure AI Services (Face API)** to analyze facial emotions and compute a stress score.

---

## 🏗️ Architecture

```
Browser (Webcam) → FastAPI Backend → Azure Face API (Emotion Analysis)
                                   → Stress Score Calculation
                                   → Azure App Service (Hosting)
```

## ✨ Features
- 📷 Real-time webcam capture
- 🧠 Azure Face API emotion detection (8 emotions)
- 📊 Animated stress gauge (0–100 score)
- 📈 Session history chart
- ⚡ Auto-detection every 5 seconds

---

## ⚙️ Local Setup

### 1. Clone / navigate to the project
```bash
cd backend
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Azure credentials
```bash
copy .env.example .env
```
Edit `.env` and fill in:
```
AZURE_FACE_API_KEY=<your Azure AI Services Key 1>
AZURE_FACE_ENDPOINT=https://<your-resource-name>.cognitiveservices.azure.com
```

> 💡 Find these in **Azure Portal → Your AI Services Resource → Keys and Endpoint**

### 5. Run locally
```bash
python app.py
```
Open: **http://localhost:8000**

---

## ☁️ Azure Deployment (App Service)

### Prerequisites
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- Logged in: `az login`

### Step 1 – Create a Resource Group
```bash
az group create --name StressDetectRG --location eastus
```

### Step 2 – Create an App Service Plan (Free tier)
```bash
az appservice plan create \
  --name StressDetectPlan \
  --resource-group StressDetectRG \
  --sku F1 \
  --is-linux
```

### Step 3 – Create the Web App
```bash
az webapp create \
  --resource-group StressDetectRG \
  --plan StressDetectPlan \
  --name stress-detect-app \
  --runtime "PYTHON:3.11" \
  --startup-file "uvicorn app:app --host 0.0.0.0 --port 8000"
```

### Step 4 – Set Environment Variables on Azure
```bash
az webapp config appsettings set \
  --resource-group StressDetectRG \
  --name stress-detect-app \
  --settings \
    AZURE_FACE_API_KEY="<your_key>" \
    AZURE_FACE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com"
```

### Step 5 – Deploy code
```bash
az webapp up \
  --resource-group StressDetectRG \
  --name stress-detect-app \
  --sku F1
```

Your app will be live at:
**https://stress-detect-app.azurewebsites.net**

---

## 🧪 API Reference

### `POST /api/analyze`
Analyze a base64-encoded webcam frame.

**Request body:**
```json
{ "image": "data:image/jpeg;base64,..." }
```

**Response:**
```json
{
  "faces_detected": 1,
  "stress": {
    "score": 62.5,
    "level": "Moderate",
    "color": "#f59e0b",
    "advice": "Try relaxing your shoulders and taking a few deep breaths."
  },
  "emotions": {
    "anger": 5.2,
    "fear": 12.1,
    "sadness": 8.3,
    "happiness": 45.0,
    "neutral": 28.1,
    "surprise": 0.8,
    "disgust": 0.3,
    "contempt": 0.2
  }
}
```

---

## 📁 Project Structure

```
backend/
├── app.py              ← FastAPI backend
├── requirements.txt    ← Python dependencies
├── Dockerfile          ← For containerized deployment
├── .env.example        ← Azure credentials template
├── .env                ← Your actual credentials (gitignored!)
├── README.md
└── static/
    └── index.html      ← Frontend (webcam UI)
```

---

## 🔐 Security Notes
- Never commit `.env` to Git — add it to `.gitignore`
- Use Azure Key Vault for production secrets
- The webcam feed stays in the browser; only captured JPEG frames are sent to the backend

---

## 📚 Azure Services Used

| Service | Usage | Tier |
|---|---|---|
| Azure AI Services (Face API) | Emotion detection | Free F0 (20 calls/min) |
| Azure App Service | Backend hosting | Free F1 |
