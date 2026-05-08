# Multi-System Facial Recognition Setup

## Prerequisites

You already have AWS configured. Now set up Google Cloud and Azure.

---

## 1. Google Cloud Vision API

### Create a Google Cloud Project

1. Go to **cloud.google.com**
2. Click **Sign in** (or create account)
3. Click **Console** (top right)
4. Create new project:
   - Click project dropdown (top)
   - Click **NEW PROJECT**
   - **Project name**: `facial-recognition-accessibility`
   - Click **CREATE**

### Enable Vision API

1. In Console, search for **Vision API**
2. Click **Vision API**
3. Click **ENABLE**
4. Wait for it to finish

### Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **CREATE SERVICE ACCOUNT**
3. **Service account name**: `facial-recognition-validator`
4. Click **CREATE AND CONTINUE**
5. Grant role: **Editor**
6. Click **CONTINUE** → **DONE**

### Download Service Account Key

1. Click the service account you just created
2. Go to **KEYS** tab
3. Click **ADD KEY** → **Create new key**
4. **Key type**: JSON
5. Click **CREATE**
6. A JSON file downloads automatically
7. Save it as `google-service-account-key.json` in your project folder

### Update config.json

In `config.json`:
```json
"google_service_account_path": "google-service-account-key.json"
```

---

## 2. Azure Face API

### Create Azure Account

1. Go to **azure.microsoft.com**
2. Sign up for free ($200 credits)
3. Go to **portal.azure.com**

### Create Cognitive Services Resource

1. Click **+ Create a resource**
2. Search for **Face**
3. Click **Face**
4. Click **Create**
5. Fill in:
   - **Resource group**: Create new: `facial-recognition-rg`
   - **Region**: `eastus` or closest to you
   - **Name**: `facial-recognition-face`
   - **Pricing tier**: `Free F0` (limited but free)
6. Click **Review + create** → **Create**

### Get API Key and Endpoint

1. Go to the resource you just created
2. Click **Keys and Endpoint**
3. Copy **Key 1** and **Endpoint**
4. Update `config.json`:

```json
"azure_endpoint": "https://YOUR-REGION.api.cognitive.microsoft.com/",
"azure_key": "YOUR-KEY-HERE"
```

---

## 3. Install Required Python Packages

```bash
pip install google-cloud-vision --break-system-packages
pip install azure-cognitiveservices-vision-face --break-system-packages
```

---

## 4. Finalized config.json

Your final config should look like:

```json
{
  "aws": {
    "region": "us-east-1",
    "note": "Uses existing AWS credentials from ~/.aws/credentials"
  },
  "google_service_account_path": "google-service-account-key.json",
  "azure_endpoint": "https://eastus.api.cognitive.microsoft.com/",
  "azure_key": "abc123def456..."
}
```

---

## 5. Test the Validator

```bash
python multi_system_validator.py --image data/processed/test_faces/age_ranges/4BG2yKyCaWg.jpg --systems aws
```

This tests only AWS first (should work immediately).

Then test all three:

```bash
python multi_system_validator.py --image data/processed/test_faces/age_ranges/4BG2yKyCaWg.jpg --systems aws,google,azure
```

---

## Costs

- **AWS**: Free tier covers ~1M face detections/month
- **Google Cloud**: $300 free credits (expires in 90 days), then ~$1.50 per 1000 detections
- **Azure**: Free F0 tier covers 30 detections/minute (sufficient for research)

All three are effectively free for your capstone testing.

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'google.cloud'"**
→ Install: `pip install google-cloud-vision --break-system-packages`

**"UNAUTHENTICATED" error from Google**
→ Make sure `google-service-account-key.json` is in project root folder

**"Authentication error" from Azure**
→ Double-check your key and endpoint in config.json (no extra spaces)

**AWS still works but Google/Azure don't**
→ That's fine! AWS alone gives you solid results. Set `--systems aws` and move forward.

