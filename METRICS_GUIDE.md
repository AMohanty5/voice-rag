# Voice Metrics Monitoring Guide

This document explains the comprehensive metrics monitoring system implemented in the Voice RAG Bot.

## Overview

The metrics system captures detailed performance and usage data from the voice pipeline, including:
- ⏱️ **TTFB (Time to First Byte)**: Latency measurements for LLM and TTS responses
- ⚙️ **Processing Time**: Duration of various pipeline stages
- 🤖 **LLM Token Usage**: Prompt and completion tokens consumed
- 🔊 **TTS Character Usage**: Characters converted to speech
- 📊 **Smart Turn Prediction**: Conversation turn-taking data
- 💰 **Cost Estimates**: Real-time cost tracking for API usage

## Configuration

### Pipeline Parameters

The following metrics settings are enabled in `bot.py`:

```python
task = PipelineTask(
    pipeline,
    params=PipelineParams(
        enable_metrics=True,              # Track performance metrics (TTFB, processing time)
        enable_usage_metrics=True,        # Track API usage (tokens, characters, costs)
        report_only_initial_ttfb=True,    # Report only first TTFB for better performance
    ),
)
```

#### Parameter Descriptions

1. **`enable_metrics=True`**
   - Enables performance metrics collection
   - Captures TTFB and processing time data
   - Essential for latency monitoring

2. **`enable_usage_metrics=True`**
   - Enables API usage tracking
   - Captures token and character consumption
   - Critical for cost management

3. **`report_only_initial_ttfb=True`**
   - Reports only the first TTFB measurement per response
   - Reduces metric overhead for streaming responses
   - Provides sufficient data for latency analysis

## Custom Metrics Processor

### MetricsLogger Class

The `MetricsLogger` is a custom `FrameProcessor` that intercepts and logs all metrics flowing through the pipeline.

**Location**: `metrics_logger.py`

**Key Features**:
- Real-time metric logging with timestamps
- Cumulative statistics tracking
- Cost estimation for LLM and TTS usage
- JSON-formatted detailed logs for analysis
- Session summary on shutdown

### Integration in Pipeline

The `MetricsLogger` is positioned at the end of the pipeline to capture all metrics:

```python
pipeline = Pipeline([
    transport.input(),              # Audio input
    rtvi,                           # RTVI protocol
    stt,                            # Speech-to-Text
    rag_processor,                  # RAG context injection
    context_aggregator.user(),      # User message
    llm,                            # LLM generation
    tts,                            # Text-to-Speech
    transport.output(),             # Audio output
    context_aggregator.assistant(), # Assistant message
    metrics_logger,                 # 📊 Metrics capture
])
```

## Captured Metrics

### 1. TTFB (Time to First Byte)

**What it measures**: Latency from request to first response chunk

**Why it matters**: Critical for perceived responsiveness

**Log format**:
```
📊 TTFB Metric | Current: 245.32ms | Average: 230.15ms | Processor: OpenAILLMService | Elapsed: 12.3s
```

**Tracked data**:
- Current TTFB value (milliseconds)
- Rolling average TTFB
- Source processor (LLM or TTS)
- Elapsed session time

### 2. Processing Time

**What it measures**: Duration of processing stages in the pipeline

**Why it matters**: Helps identify bottlenecks

**Log format**:
```
⚙️  Processing Metric | Duration: 150.25ms | Average: 145.30ms | Max: 180.50ms | Processor: RAGProcessor
```

**Tracked data**:
- Current processing duration
- Average processing time
- Maximum processing time
- Source processor

### 3. LLM Token Usage

**What it measures**: Tokens consumed by language model operations

**Why it matters**: Essential for cost tracking and quota management

**Log format**:
```
🤖 LLM Usage Metric | Prompt: 1250 tokens | Completion: 85 tokens | Total: 1335 tokens | Est. Cost: $0.0425 | Processor: OpenAILLMService
📈 Cumulative LLM Usage | Total Prompt: 5420 | Total Completion: 340 | Grand Total: 5760 tokens
```

**Tracked data**:
- Prompt tokens (input)
- Completion tokens (output)
- Total tokens per request
- Estimated cost per request
- Cumulative session totals

**Cost calculation** (GPT-4 example):
- Prompt tokens: $0.03 per 1,000 tokens
- Completion tokens: $0.06 per 1,000 tokens

### 4. TTS Character Usage

**What it measures**: Characters converted to speech

**Why it matters**: Important for TTS service cost tracking

**Log format**:
```
🔊 TTS Usage Metric | Characters: 142 | Est. Cost: $0.0021 | Processor: CartesiaTTSService
📈 Cumulative TTS Usage | Total Characters: 1580
```

**Tracked data**:
- Characters per TTS request
- Estimated cost per request
- Cumulative session total

**Cost calculation** (Cartesia example):
- $15 per 1 million characters ($0.000015 per character)

### 5. Smart Turn Prediction Data

**What it measures**: Conversation turn-taking predictions

**Why it matters**: Improves natural conversation flow

**Note**: This data is captured automatically by the `LocalSmartTurnAnalyzerV3` configured in the transport parameters.

## Enrichment Metrics

The `MetricsLogger` automatically enriches all metrics with:

- **Timestamps**: ISO 8601 format for precise timing
- **Elapsed Time**: Seconds since session start
- **Rolling Averages**: For trend analysis
- **Min/Max Values**: For outlier detection
- **Processor Attribution**: Source of each metric

## Session Summary

When the bot shuts down, a comprehensive session summary is logged:

```
================================================================================
MetricsLogger Session Summary
================================================================================
Session Duration: 125.3 seconds
Total LLM Tokens: 8450
  - Prompt: 7200
  - Completion: 1250
Total TTS Characters: 3420
TTFB Stats: Avg=235.45ms, Min=180.20ms, Max=310.80ms
Processing Stats: Avg=145.30ms, Min=95.10ms, Max=220.50ms
================================================================================
```

## Log Levels

The metrics system uses different log levels:

- **`INFO`**: Primary metrics (TTFB, processing, usage)
- **`DEBUG`**: Detailed JSON metrics for analysis
- **`WARNING`**: Anomalies or threshold violations (future enhancement)

## JSON Structured Logging

All metrics are also logged in JSON format for easy parsing:

```json
{
  "type": "llm_usage",
  "prompt_tokens": 1250,
  "completion_tokens": 85,
  "total_tokens": 1335,
  "estimated_cost_usd": 0.0425,
  "cumulative_prompt_tokens": 5420,
  "cumulative_completion_tokens": 340,
  "processor": "OpenAILLMService",
  "timestamp": "2025-11-24T18:20:13.123456"
}
```

These logs can be:
- Parsed by log aggregation tools (ELK, Splunk)
- Sent to monitoring dashboards (Grafana, DataDog)
- Stored in time-series databases (InfluxDB, Prometheus)
- Analyzed for trends and anomalies

## Usage Examples

### Running the Bot with Metrics

```bash
# Start the bot (metrics are enabled by default)
uv run bot.py
```

### Viewing Metrics in Real-Time

Metrics are logged to the console in real-time. You'll see output like:

```
2025-11-24 18:20:13 | INFO | MetricsLogger initialized - monitoring voice pipeline metrics
2025-11-24 18:20:15 | INFO | 📊 TTFB Metric | Current: 245.32ms | Average: 245.32ms | ...
2025-11-24 18:20:15 | INFO | 🤖 LLM Usage Metric | Prompt: 1250 tokens | Completion: 85 tokens | ...
2025-11-24 18:20:15 | INFO | 🔊 TTS Usage Metric | Characters: 142 | Est. Cost: $0.0021 | ...
```

### Accessing Summary Statistics

The `MetricsLogger` provides a `get_summary_stats()` method that returns aggregated metrics:

```python
stats = metrics_logger.get_summary_stats()
print(f"Total tokens used: {stats['llm_tokens']['total_combined']}")
print(f"Average TTFB: {stats['ttfb']['average_ms']:.2f}ms")
```

## Future Enhancements

Potential extensions to the metrics system:

1. **Alerting**: Trigger alerts when metrics exceed thresholds
2. **Dashboard Integration**: Send metrics to Grafana/DataDog
3. **Database Storage**: Store metrics in time-series database
4. **Cost Budgets**: Set and enforce cost limits
5. **Performance Optimization**: Automatically adjust based on metrics
6. **A/B Testing**: Compare metrics across different configurations
7. **User Analytics**: Track per-user or per-session metrics

## Customization

### Adjusting Cost Estimates

Update the cost calculation in `metrics_logger.py`:

```python
# For LLM (update based on your model pricing)
prompt_cost = prompt_tokens * 0.00003  # Your rate per token
completion_cost = completion_tokens * 0.00006  # Your rate per token

# For TTS (update based on your service pricing)
cost_per_char = 0.000015  # Your rate per character
```

### Adding Custom Metrics

To capture additional metrics, extend the `MetricsLogger` class:

```python
class MetricsLogger(FrameProcessor):
    async def _process_metrics_frame(self, frame: MetricsFrame):
        for metric_data in frame.data:
            # Add your custom metric handling here
            if isinstance(metric_data, YourCustomMetricType):
                # Process and log your custom metric
                pass
```

### Filtering Metrics

To reduce log verbosity, you can filter specific metric types:

```python
# Only log LLM and TTS usage, skip TTFB and processing
if isinstance(metric_data, (LLMUsageMetricsData, TTSUsageMetricsData)):
    # Log only usage metrics
    pass
```

## Troubleshooting

### Metrics Not Appearing

1. **Check PipelineParams**: Ensure `enable_metrics=True` and `enable_usage_metrics=True`
2. **Check Pipeline**: Verify `metrics_logger` is in the pipeline
3. **Check Log Level**: Ensure logger is set to INFO or DEBUG

### High Metric Overhead

1. **Use `report_only_initial_ttfb=True`**: Reduces TTFB reporting frequency
2. **Filter Metrics**: Only log critical metrics
3. **Adjust Log Level**: Use INFO instead of DEBUG for production

### Cost Estimates Inaccurate

1. **Update Pricing**: Check current API pricing and update cost calculations
2. **Account for Model**: Different models have different pricing
3. **Include All Costs**: Consider API overhead, network costs, etc.

## Best Practices

1. **Monitor Regularly**: Review metrics daily to catch issues early
2. **Set Baselines**: Establish normal ranges for each metric
3. **Alert on Anomalies**: Set up alerts for unusual patterns
4. **Optimize Iteratively**: Use metrics to guide performance improvements
5. **Track Costs**: Monitor cumulative costs to avoid surprises
6. **Archive Logs**: Store historical metrics for trend analysis

## References

- [Pipecat Metrics Documentation](https://docs.pipecat.ai/metrics)
- [Pipecat Pipeline Architecture](https://docs.pipecat.ai/pipeline)
- [OpenAI Pricing](https://openai.com/pricing)
- [Cartesia Pricing](https://cartesia.ai/pricing)

---

**Last Updated**: 2025-11-24
**Version**: 1.0
