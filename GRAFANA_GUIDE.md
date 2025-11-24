# Grafana Cloud Integration - Complete Guide

This guide details the integration of Grafana Cloud with the Voice RAG Bot using OpenTelemetry Protocol (OTLP). It consolidates setup instructions, metrics details, dashboard configuration, and troubleshooting.

---

## 🎯 Overview

The bot exports comprehensive metrics to **Grafana Cloud** for real-time monitoring, visualization, and alerting.

### Key Features
- ✅ **Real-time Monitoring**: Track call performance live.
- ✅ **Cost Tracking**: Monitor estimated costs for LLM and TTS.
- ✅ **Performance Analysis**: Identify bottlenecks with TTFB and processing time metrics.
- ✅ **Usage Analytics**: Track token and character usage.

---

## ⚙️ Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Grafana Cloud - Metrics Monitoring
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_base64_encoded_instance_id:token>
```

**Note**: Replace `<your_base64_encoded_instance_id:token>` with the Base64 encoding of `YOUR_INSTANCE_ID:YOUR_TOKEN`.

### 2. Install Dependencies

```bash
uv sync
```
(Installs `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`)

### 3. Run the Bot

```bash
uv run bot.py
```

---

## 📊 Metrics Reference

### 1. Call Identification
- **Unique Call ID**: Generated per session (UUID).
- **Models**: LLM (`gpt-4o`), STT (`gladia`), TTS (`cartesia`).
- **Service Name**: `voice-rag-bot`.

### 2. Performance Metrics
- **TTFB**: `voice.ttfb.milliseconds` (Histogram) - Latency to first response.
- **Processing Time**: `voice.processing.milliseconds` (Histogram) - Duration of pipeline stages.

### 3. Usage Metrics
- **LLM Tokens**: `voice.llm.tokens.total` (Counter) - Prompt and completion tokens.
- **TTS Characters**: `voice.tts.characters.total` (Counter) - Characters synthesized.

### 4. Cost Metrics
- **Estimated Cost**: `voice.cost.usd` (Counter) - Real-time cost estimates.

### 5. Session Metrics
- **Session Duration**: `voice.session.duration.seconds` (UpDownCounter).
- **Total Calls**: `voice.calls.total` (Counter).

---

## 📈 Dashboard Setup

### Example PromQL Queries

**Average TTFB**:
```promql
rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m])
```

**Total Cost**:
```promql
sum(voice_cost_usd)
```

**Token Usage by Call**:
```promql
sum by (call_id, token_type) (voice_llm_tokens_total)
```

### Alerts Configuration

**High TTFB (> 2s)**:
```yaml
expr: rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m]) > 2000
```

**Cost Threshold (> $10/h)**:
```yaml
expr: sum(rate(voice_cost_usd[1h])) > 10
```

---

## ❓ Troubleshooting

### Authentication Errors
**Error**: `authentication error: invalid authentication credentials`

**Solution**:
1. **Check Format**: Ensure header is `Authorization=Basic <token>`.
2. **Check Encoding**: Token must be `Base64(INSTANCE_ID:TOKEN)`.
   - **Wrong**: `Base64(TOKEN)`
   - **Correct**: `Base64(123456:glc_...)`
3. **No URL Encoding**: Use space, not `%20` in `.env`.

### Metrics Not Appearing
1. Check `OTEL_EXPORTER_OTLP_ENDPOINT` is correct.
2. Verify logs show: `✅ OpenTelemetry configured for Grafana Cloud`.
3. Check network connectivity.

---

## 🔧 Implementation Details

- **Exporter**: `GrafanaMetricsExporter` (custom OpenTelemetry exporter).
- **Protocol**: OTLP/HTTP.
- **Export Interval**: 10 seconds.
- **Region**: `ap-south-1` (Mumbai).

**Data Flow**:
```
Pipeline → MetricsFrame → GrafanaMetricsExporter → OpenTelemetry SDK → OTLP Exporter → Grafana Cloud
```

---

**Last Updated**: 2025-11-25
