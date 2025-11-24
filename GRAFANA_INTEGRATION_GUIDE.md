# Grafana Cloud Metrics Integration Guide

## Overview

The Voice RAG Bot now exports comprehensive metrics to **Grafana Cloud** using OpenTelemetry Protocol (OTLP). This enables real-time monitoring, visualization, and alerting for all voice pipeline metrics.

---

## What's Exported to Grafana

### 1. **Unique Call ID**
- Generated automatically for each session using UUID
- Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Allows tracking individual calls and sessions
- Included in all metric attributes

### 2. **Model Information**
Every metric includes:
- **LLM Model**: `gpt-4o` (OpenAI)
- **STT Model**: `gladia` (Speech-to-Text)
- **TTS Model**: `cartesia` (Text-to-Speech)

### 3. **Metrics Captured**

#### Performance Metrics
- **TTFB (Time to First Byte)**: Latency from request to first response
  - Metric: `voice.ttfb.milliseconds`
  - Type: Histogram
  - Unit: milliseconds

- **Processing Time**: Duration of pipeline stages
  - Metric: `voice.processing.milliseconds`
  - Type: Histogram
  - Unit: milliseconds

#### Usage Metrics
- **LLM Token Usage**: Tokens consumed by language model
  - Metric: `voice.llm.tokens.total`
  - Type: Counter
  - Attributes: `token_type` (prompt/completion)

- **TTS Character Usage**: Characters converted to speech
  - Metric: `voice.tts.characters.total`
  - Type: Counter
  - Unit: characters

#### Session Metrics
- **Session Duration**: Current session length
  - Metric: `voice.session.duration.seconds`
  - Type: UpDownCounter
  - Unit: seconds

- **Total Calls**: Number of calls processed
  - Metric: `voice.calls.total`
  - Type: Counter

#### Cost Metrics
- **Estimated Costs**: Real-time cost tracking
  - Metric: `voice.cost.usd`
  - Type: Counter
  - Attributes: `cost_type` (llm/tts)
  - Unit: USD

---

## Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Grafana Cloud - OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <your_base64_encoded_token>
```

**Note**: Replace `<your_base64_encoded_token>` with your actual Grafana Cloud token.

**Configuration Details**:
- **Endpoint**: `https://otlp-gateway-prod-ap-south-1.grafana.net/otlp`
- **Region**: `ap-south-1` (Mumbai, India)
- **Token**: Stored securely in your `.env` file

### 2. Install Dependencies

```bash
# Install OpenTelemetry packages
uv sync
```

This will install:
- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-http`

---

## Architecture

### Data Flow

```
Voice Pipeline
    ↓
MetricsFrame Generated
    ↓
GrafanaMetricsExporter
    ↓
OpenTelemetry SDK
    ↓
OTLP HTTP Exporter
    ↓
Grafana Cloud (ap-south-1)
    ↓
Grafana Dashboards
```

### Pipeline Integration

```python
Pipeline([
    transport.input(),
    rtvi,
    stt,                    # Gladia STT
    language_switcher,
    rag_processor,
    context_aggregator.user(),
    llm,                    # OpenAI GPT-4
    tts,                    # Cartesia TTS
    transport.output(),
    context_aggregator.assistant(),
    metrics_logger,         # Console logging
    grafana_exporter,       # Grafana Cloud export ← NEW
])
```

---

## Metrics Details

### 1. Call Identification

Every metric includes these attributes:

```python
{
    "call_id": "550e8400-e29b-41d4-a716-446655440000",
    "llm_model": "gpt-4o",
    "stt_model": "gladia",
    "tts_model": "cartesia",
    "service_name": "voice-rag-bot"
}
```

### 2. TTFB Metrics

```python
# Metric Name: voice.ttfb.milliseconds
# Type: Histogram
# Attributes:
{
    "call_id": "...",
    "llm_model": "gpt-4o",
    "stt_model": "gladia",
    "tts_model": "cartesia",
    "processor": "OpenAILLMService",  # Which processor generated TTFB
    "metric_type": "ttfb"
}
```

**Use Cases**:
- Monitor response latency
- Identify slow processors
- Track performance over time
- Set up latency alerts

### 3. Processing Time Metrics

```python
# Metric Name: voice.processing.milliseconds
# Type: Histogram
# Attributes:
{
    "call_id": "...",
    "processor": "RAGProcessor",  # Which stage is being measured
    "metric_type": "processing"
}
```

**Use Cases**:
- Identify bottlenecks
- Optimize slow stages
- Track pipeline efficiency

### 4. LLM Token Usage

```python
# Metric Name: voice.llm.tokens.total
# Type: Counter
# Attributes:
{
    "call_id": "...",
    "llm_model": "gpt-4o",
    "token_type": "prompt",  # or "completion"
    "processor": "OpenAILLMService"
}
```

**Use Cases**:
- Track token consumption
- Monitor costs
- Optimize prompt sizes
- Quota management

### 5. TTS Character Usage

```python
# Metric Name: voice.tts.characters.total
# Type: Counter
# Attributes:
{
    "call_id": "...",
    "tts_model": "cartesia",
    "processor": "CartesiaTTSService"
}
```

**Use Cases**:
- Track TTS usage
- Monitor costs
- Optimize response lengths

### 6. Cost Tracking

```python
# Metric Name: voice.cost.usd
# Type: Counter
# Attributes:
{
    "call_id": "...",
    "cost_type": "llm",  # or "tts"
    "llm_model": "gpt-4o",  # or tts_model
    "processor": "..."
}
```

**Pricing Used**:
- **GPT-4**: $0.03/1K prompt tokens, $0.06/1K completion tokens
- **Cartesia TTS**: $0.000015/character

---

## Grafana Dashboard Setup

### 1. Access Grafana Cloud

1. Go to https://grafana.com
2. Log in to your account
3. Navigate to your workspace

### 2. Create Dashboard

#### Panel 1: Real-Time TTFB

```promql
# Query
rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m])

# Visualization: Time series
# Title: "Average TTFB Over Time"
# Unit: milliseconds
# Group by: processor
```

#### Panel 2: Token Usage by Call

```promql
# Query
sum by (call_id, token_type) (voice_llm_tokens_total)

# Visualization: Bar chart
# Title: "LLM Token Usage by Call"
# Group by: call_id, token_type
```

#### Panel 3: Cost Tracking

```promql
# Query
sum by (cost_type) (voice_cost_usd)

# Visualization: Stat panel
# Title: "Total Estimated Cost"
# Unit: USD
# Decimals: 4
```

#### Panel 4: Active Calls

```promql
# Query
voice_calls_total

# Visualization: Stat panel
# Title: "Total Calls Processed"
```

#### Panel 5: Processing Time Heatmap

```promql
# Query
voice_processing_milliseconds_bucket

# Visualization: Heatmap
# Title: "Processing Time Distribution"
```

### 3. Example Dashboard JSON

Save this as a dashboard template:

```json
{
  "dashboard": {
    "title": "Voice RAG Bot Metrics",
    "panels": [
      {
        "title": "Average TTFB",
        "targets": [
          {
            "expr": "rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m])"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "Total Cost",
        "targets": [
          {
            "expr": "sum(voice_cost_usd)"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

---

## Alerts Configuration

### Alert 1: High TTFB

```yaml
alert: HighTTFB
expr: rate(voice_ttfb_milliseconds_sum[5m]) / rate(voice_ttfb_milliseconds_count[5m]) > 2000
for: 5m
labels:
  severity: warning
annotations:
  summary: "High TTFB detected (> 2 seconds)"
  description: "Average TTFB is {{ $value }}ms for call {{ $labels.call_id }}"
```

### Alert 2: High Token Usage

```yaml
alert: HighTokenUsage
expr: rate(voice_llm_tokens_total[5m]) > 10000
for: 5m
labels:
  severity: warning
annotations:
  summary: "High token usage detected"
  description: "Token usage rate is {{ $value }} tokens/5min"
```

### Alert 3: Cost Threshold

```yaml
alert: CostThreshold
expr: sum(voice_cost_usd) > 10
for: 1h
labels:
  severity: critical
annotations:
  summary: "Cost threshold exceeded ($10/hour)"
  description: "Current cost: ${{ $value }}"
```

---

## Querying Metrics

### PromQL Examples

#### 1. Average TTFB by Model

```promql
avg by (llm_model) (
  rate(voice_ttfb_milliseconds_sum[5m]) / 
  rate(voice_ttfb_milliseconds_count[5m])
)
```

#### 2. Token Usage per Call

```promql
sum by (call_id) (voice_llm_tokens_total)
```

#### 3. Cost per Hour

```promql
sum(rate(voice_cost_usd[1h]))
```

#### 4. Processing Time Percentiles

```promql
histogram_quantile(0.95, 
  rate(voice_processing_milliseconds_bucket[5m])
)
```

#### 5. Calls by Model

```promql
count by (llm_model, stt_model, tts_model) (voice_calls_total)
```

---

## Troubleshooting

### Issue: Metrics not appearing in Grafana

**Solutions**:
1. Check environment variables are set correctly
2. Verify Grafana token is valid
3. Check network connectivity to Grafana Cloud
4. Review logs for export errors:
   ```bash
   uv run bot.py 2>&1 | grep -i "grafana\|otel"
   ```

### Issue: Authentication errors

**Solutions**:
1. Verify token format in `.env`:
   ```bash
   OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20<your_token>
   ```
2. Ensure no extra spaces or newlines
3. Check token hasn't expired

### Issue: High export latency

**Solutions**:
1. Metrics are exported every 10 seconds by default
2. Adjust export interval in `grafana_metrics.py`:
   ```python
   reader = PeriodicExportingMetricReader(
       exporter, 
       export_interval_millis=5000  # 5 seconds
   )
   ```

---

## Best Practices

### 1. Call ID Management
- Each session gets a unique Call ID
- Use Call ID to correlate metrics across panels
- Filter dashboards by Call ID for debugging

### 2. Cost Monitoring
- Set up alerts for cost thresholds
- Review daily/weekly cost trends
- Optimize based on cost per call

### 3. Performance Optimization
- Monitor TTFB trends
- Identify slow processors
- Set SLAs and track compliance

### 4. Dashboard Organization
- Create separate dashboards for:
  - Real-time monitoring
  - Cost analysis
  - Performance analysis
  - Call-level debugging

---

## Example Logs

### Startup Logs

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

### Runtime Logs

```
📊 [Grafana] TTFB: 1234.56ms | Processor: OpenAILLMService | Call ID: 550e8400...
🤖 [Grafana] LLM Tokens: 150 (Prompt: 100, Completion: 50) | Cost: $0.0060
🔊 [Grafana] TTS Characters: 250 | Cost: $0.0038
```

### Shutdown Logs

```
================================================================================
📊 Grafana Metrics - Call Summary
================================================================================
📞 Call ID: 550e8400-e29b-41d4-a716-446655440000
⏱️  Duration: 125.3s
🤖 LLM Model: gpt-4o
🎤 STT Model: gladia
🔊 TTS Model: cartesia
📝 Total LLM Tokens: 1500
   - Prompt: 1000
   - Completion: 500
🔤 Total TTS Characters: 2500
⚡ TTFB: Avg=1234.56ms, Min=890.12ms, Max=2345.67ms
================================================================================
✅ Metrics exported to Grafana Cloud
================================================================================
```

---

## Next Steps

1. **Install Dependencies**: Run `uv sync`
2. **Configure Environment**: Add Grafana credentials to `.env`
3. **Run Bot**: Test metrics export with `uv run bot.py`
4. **Create Dashboard**: Set up Grafana dashboard
5. **Configure Alerts**: Set up critical alerts
6. **Monitor**: Watch metrics in real-time

---

**Last Updated**: 2025-11-25
**Grafana Region**: ap-south-1 (Mumbai)
**Export Protocol**: OTLP/HTTP
