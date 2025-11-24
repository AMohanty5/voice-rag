# Grafana Cloud Setup - Quick Start

## ✅ What's Implemented

Your Voice RAG Bot now exports comprehensive metrics to Grafana Cloud including:
- ✅ Unique Call ID for each session
- ✅ Model information (LLM: gpt-4o, STT: gladia, TTS: cartesia)
- ✅ TTFB (Time to First Byte) metrics
- ✅ Processing time metrics
- ✅ LLM token usage
- ✅ TTS character usage
- ✅ Cost estimates
- ✅ Session duration

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Update `.env` File

Add your Grafana Cloud credentials:

```bash
# Grafana Cloud - OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_base64_encoded_token>
```

**Note**: Replace `<your_base64_encoded_token>` with your actual Grafana Cloud token from your `.env` file.

### Step 2: Install Dependencies

```bash
uv sync
```

This installs:
- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-http`

### Step 3: Run the Bot

```bash
uv run bot.py
```

Look for these startup messages:

```
================================================================================
🔗 Grafana Metrics Exporter Initialized
================================================================================
📞 Call ID: 550e8400-e29b-41d4-a716-446655440000
🤖 LLM Model: gpt-4o
🎤 STT Model: gladia
🔊 TTS Model: cartesia
📊 Grafana Endpoint: https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
================================================================================
✅ OpenTelemetry configured for Grafana Cloud
✅ Metric instruments created
```

---

## 📊 Metrics Exported

### 1. Call Identification
- **Unique Call ID**: Generated per session (UUID format)
- **Models**: LLM (gpt-4o), STT (gladia), TTS (cartesia)

### 2. Performance Metrics
- **TTFB**: `voice.ttfb.milliseconds` (Histogram)
- **Processing Time**: `voice.processing.milliseconds` (Histogram)

### 3. Usage Metrics
- **LLM Tokens**: `voice.llm.tokens.total` (Counter)
  - Separate counts for prompt and completion tokens
- **TTS Characters**: `voice.tts.characters.total` (Counter)

### 4. Cost Metrics
- **Estimated Cost**: `voice.cost.usd` (Counter)
  - Separate tracking for LLM and TTS costs

### 5. Session Metrics
- **Session Duration**: `voice.session.duration.seconds` (UpDownCounter)
- **Total Calls**: `voice.calls.total` (Counter)

---

## 🎯 View Metrics in Grafana

### 1. Access Grafana Cloud

1. Go to https://grafana.com
2. Log in to your account
3. Navigate to **Explore** → **Metrics**

### 2. Query Your Metrics

Try these queries:

#### Average TTFB
```promql
rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m])
```

#### Total Token Usage
```promql
sum(voice_llm_tokens_total)
```

#### Total Cost
```promql
sum(voice_cost_usd)
```

#### Calls by Model
```promql
count by (llm_model, stt_model, tts_model) (voice_calls_total)
```

### 3. Create Dashboard

1. Go to **Dashboards** → **New Dashboard**
2. Add panels with the queries above
3. Save dashboard as "Voice RAG Bot Metrics"

---

## 📈 Example Dashboard Panels

### Panel 1: Real-Time TTFB
- **Type**: Time series
- **Query**: `rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m])`
- **Title**: "Average TTFB Over Time"
- **Unit**: milliseconds

### Panel 2: Token Usage
- **Type**: Bar chart
- **Query**: `sum by (call_id, token_type) (voice_llm_tokens_total)`
- **Title**: "LLM Token Usage by Call"

### Panel 3: Cost Tracking
- **Type**: Stat
- **Query**: `sum(voice_cost_usd)`
- **Title**: "Total Estimated Cost"
- **Unit**: USD

### Panel 4: Processing Time
- **Type**: Heatmap
- **Query**: `voice_processing_milliseconds_bucket`
- **Title**: "Processing Time Distribution"

---

## 🔔 Set Up Alerts

### Alert 1: High TTFB (> 2 seconds)

```yaml
alert: HighTTFB
expr: rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m]) > 2000
for: 5m
labels:
  severity: warning
annotations:
  summary: "High TTFB detected"
```

### Alert 2: Cost Threshold (> $10/hour)

```yaml
alert: CostThreshold
expr: sum(rate(voice_cost_usd[1h])) > 10
for: 1h
labels:
  severity: critical
annotations:
  summary: "Cost threshold exceeded"
```

---

## 🧪 Testing

### 1. Start the Bot

```bash
uv run bot.py
```

### 2. Make a Test Call

Connect to the bot and have a conversation.

### 3. Check Logs

Look for Grafana export logs:

```
📊 [Grafana] TTFB: 1234.56ms | Processor: OpenAILLMService | Call ID: 550e8400...
🤖 [Grafana] LLM Tokens: 150 (Prompt: 100, Completion: 50) | Cost: $0.0060
🔊 [Grafana] TTS Characters: 250 | Cost: $0.0038
```

### 4. View in Grafana

1. Go to Grafana Cloud
2. Navigate to **Explore**
3. Query: `voice_calls_total`
4. You should see your metrics!

---

## ❓ Troubleshooting

### Metrics not appearing?

1. **Check environment variables**:
   ```bash
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   echo $OTEL_EXPORTER_OTLP_HEADERS
   ```

2. **Verify token format**:
   - Should start with `Authorization=Basic%20`
   - No extra spaces or newlines

3. **Check logs for errors**:
   ```bash
   uv run bot.py 2>&1 | grep -i "grafana\|otel\|error"
   ```

### Authentication errors?

1. Verify token is correct
2. Check token hasn't expired
3. Ensure proper URL encoding (`%20` for spaces)

### High latency?

- Metrics are exported every 10 seconds
- This is normal and won't affect bot performance
- Adjust in `grafana_metrics.py` if needed

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `grafana_metrics.py` | Grafana metrics exporter (OpenTelemetry) |
| `GRAFANA_INTEGRATION_GUIDE.md` | Complete integration documentation |
| `GRAFANA_QUICKSTART.md` | This quick start guide |

---

## 📚 Documentation

- **Complete Guide**: `GRAFANA_INTEGRATION_GUIDE.md`
- **Metrics Details**: See full guide for all metric types
- **Dashboard Examples**: See full guide for JSON templates
- **Alert Examples**: See full guide for alert configurations

---

## 🎉 You're Done!

Your Voice RAG Bot is now sending metrics to Grafana Cloud!

**Next Steps**:
1. ✅ Create your first dashboard
2. ✅ Set up critical alerts
3. ✅ Monitor call performance
4. ✅ Track costs in real-time

**Need Help?**
- Check `GRAFANA_INTEGRATION_GUIDE.md` for detailed documentation
- Review logs for export status
- Verify Grafana Cloud connection

---

**Last Updated**: 2025-11-25
**Grafana Region**: ap-south-1 (Mumbai)
**Export Interval**: 10 seconds
