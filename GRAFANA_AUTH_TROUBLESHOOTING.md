# Grafana Cloud Authentication Troubleshooting

## 🔴 Error: "authentication error: invalid authentication credentials"

This error occurs when the Grafana Cloud authorization header is not formatted correctly.

---

## ✅ Solution: Fix Authorization Header Format

### Problem

The current format in your `.env` might have encoding issues:
```bash
# ❌ WRONG - URL encoded
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20<token>
```

### Solution

The authorization header should be formatted differently for the `.env` file:

```bash
# ✅ CORRECT - Space instead of %20
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_token_here>
```

---

## 🔧 Step-by-Step Fix

### Step 1: Get Your Grafana Cloud Credentials

1. Go to https://grafana.com
2. Log in to your account
3. Navigate to **Connections** → **Add new connection** → **OpenTelemetry**
4. Or go to your existing OTLP configuration

You should see:
- **Endpoint**: `https://otlp-gateway-prod-ap-south-1.grafana.net/otlp`
- **Instance ID**: (a number, e.g., `1598636`)
- **Token**: (starts with `glc_...`)

### Step 2: Create the Correct Authorization Header

Your token needs to be Base64 encoded in the format: `<instance_id>:<token>`

#### Option A: Use Online Base64 Encoder

1. Go to https://www.base64encode.org/
2. Enter: `<your_instance_id>:<your_token>`
   - Example format: `YOUR_INSTANCE_ID:YOUR_TOKEN`
3. Click **Encode**
4. Copy the result

#### Option B: Use Python

```python
import base64

instance_id = "YOUR_INSTANCE_ID"  # e.g., "1598636"
token = "YOUR_TOKEN"  # e.g., "glc_abc123..."

# Combine and encode
credentials = f"{instance_id}:{token}"
encoded = base64.b64encode(credentials.encode()).decode()

print(f"Your Base64 encoded credentials: {encoded}")
```

#### Option C: Use Command Line

**Linux/Mac/WSL:**
```bash
echo -n "YOUR_INSTANCE_ID:YOUR_TOKEN" | base64
```

**Windows PowerShell:**
```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("YOUR_INSTANCE_ID:YOUR_TOKEN"))
```

### Step 3: Update Your `.env` File

Open your `.env` file and update these two lines:

```bash
# Grafana Cloud - Metrics Monitoring
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic YOUR_BASE64_ENCODED_CREDENTIALS
```

**IMPORTANT**: 
- Use a **space** between `Basic` and your credentials (not `%20`)
- Do NOT include `%20` in the `.env` file
- The Base64 string should be the output from Step 2

### Step 4: Verify Format

Your `.env` should look like this:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic Z2xjX2V5SnZJam9pTVRVNU9EWXpOaUlzSW00aU9pSndhWEJsWTJGMElpd2lheUk2SWxjNVF6UXdkakpzTlVkc1lXWnRUVlE1TldGM01qQkZNU0lzSW0waU9uc2ljaUk2SW5CeWIyUXRZWEF0YzI5MWRHZ3RNU0o5ZlE9PToxNDQ4MzM5
```

(Your Base64 string will be different based on your credentials)

---

## 🧪 Test Your Configuration

### Step 1: Check Environment Variables

Create a test script `test_grafana_auth.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")

print("=" * 80)
print("Grafana Configuration Check")
print("=" * 80)
print(f"Endpoint: {endpoint}")
print(f"Headers: {headers}")
print("=" * 80)

if not endpoint:
    print("❌ ERROR: OTEL_EXPORTER_OTLP_ENDPOINT not set")
elif not headers:
    print("❌ ERROR: OTEL_EXPORTER_OTLP_HEADERS not set")
elif "Basic " not in headers:
    print("❌ ERROR: Authorization header missing 'Basic '")
elif "%20" in headers:
    print("❌ ERROR: Remove %20 encoding from .env file")
else:
    print("✅ Configuration looks good!")
    
    # Extract and decode the token
    import base64
    try:
        auth_part = headers.replace("Authorization=", "").replace("Basic ", "")
        decoded = base64.b64decode(auth_part).decode()
        print(f"✅ Decoded credentials format: {decoded[:20]}... (truncated)")
        
        if ":" in decoded:
            print("✅ Credentials contain ':' separator")
        else:
            print("❌ ERROR: Credentials should be in format 'instance_id:token'")
    except Exception as e:
        print(f"❌ ERROR decoding credentials: {e}")
```

Run it:
```bash
python test_grafana_auth.py
```

### Step 2: Test with Curl

Test the endpoint directly:

```bash
# Replace YOUR_BASE64_CREDENTIALS with your actual Base64 string
curl -X POST \
  https://otlp-gateway-prod-ap-south-1.grafana.net/otlp/v1/metrics \
  -H "Authorization: Basic YOUR_BASE64_CREDENTIALS" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected responses:**
- ✅ `400 Bad Request` or `415 Unsupported Media Type` = Auth is working! (Empty payload is invalid, but auth passed)
- ❌ `401 Unauthorized` = Auth credentials are wrong
- ❌ `403 Forbidden` = Token doesn't have permissions

### Step 3: Run Your Bot

```bash
uv run bot.py
```

Look for these logs:
```
✅ OpenTelemetry configured for Grafana Cloud
✅ Metric instruments created
```

And check that you DON'T see:
```
❌ ERROR:opentelemetry.exporter.otlp.proto.http.metric_exporter:Failed to export metrics
❌ authentication error: invalid authentication credentials
```

---

## 🔍 Common Issues

### Issue 1: URL Encoding in .env

**Problem**: `.env` has `%20` instead of space
```bash
# ❌ WRONG
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20ABC123
```

**Solution**: Use space
```bash
# ✅ CORRECT
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ABC123
```

### Issue 2: Missing "Basic" Keyword

**Problem**: Authorization header missing "Basic"
```bash
# ❌ WRONG
OTEL_EXPORTER_OTLP_HEADERS=Authorization=ABC123
```

**Solution**: Include "Basic"
```bash
# ✅ CORRECT
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ABC123
```

### Issue 3: Wrong Credentials Format

**Problem**: Token not Base64 encoded, or wrong format

**Solution**: Ensure you encode `instance_id:token` (with colon separator)
```
Format: <instance_id>:<token>
Example: YOUR_INSTANCE_ID:YOUR_TOKEN
```

### Issue 4: Expired Token

**Problem**: Token has expired

**Solution**: Generate a new token in Grafana Cloud:
1. Go to Grafana Cloud dashboard
2. Navigate to **Connections** → **OpenTelemetry**
3. Generate a new token
4. Update your `.env` file

### Issue 5: Wrong Region

**Problem**: Using wrong Grafana Cloud region

**Solution**: Verify your region in Grafana Cloud dashboard:
- `ap-south-1` (Mumbai, India)
- `us-east-1` (US East)
- `eu-west-1` (Europe West)

Update endpoint:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-<YOUR_REGION>.grafana.net/otlp
```

---

## 📋 Quick Checklist

Before running the bot, verify:

- [ ] `.env` file exists in the project root
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` is set correctly
- [ ] `OTEL_EXPORTER_OTLP_HEADERS` starts with `Authorization=Basic `
- [ ] No `%20` in the authorization header (use space instead)
- [ ] Credentials are Base64 encoded in format `instance_id:token`
- [ ] Token hasn't expired
- [ ] Correct region in endpoint URL
- [ ] No extra spaces or newlines in `.env` values

---

## 🎯 Expected Working Configuration

Your `.env` should have:

```bash
# Grafana Cloud - Metrics Monitoring
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_base64_encoded_instance_id:token>
```

Where `<your_base64_encoded_instance_id:token>` is the Base64 encoding of `YOUR_INSTANCE_ID:YOUR_TOKEN`

---

## 📞 Still Having Issues?

### Check Grafana Cloud Dashboard

1. Log in to https://grafana.com
2. Go to your workspace
3. Check **Connections** → **Data sources**
4. Verify OTLP is configured correctly
5. Check for any service outages or alerts

### Enable Debug Logging

Add to your `bot.py` temporarily:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed OpenTelemetry export attempts.

### Contact Grafana Support

If authentication still fails:
1. Verify your Grafana Cloud account is active
2. Check your subscription includes OTLP metrics
3. Contact Grafana support with your instance ID

---

**Last Updated**: 2025-11-25  
**Common Fix**: Replace `%20` with space in `.env` file
