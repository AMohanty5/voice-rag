"""
Example: Accessing Metrics Programmatically

This example demonstrates how to access and use metrics data from the MetricsLogger
for custom analytics, monitoring, or alerting purposes.
"""

from metrics_logger import MetricsLogger
from datetime import datetime
import json


def example_metrics_analysis():
    """
    Example of how to analyze metrics data from the MetricsLogger.
    
    In a real application, you would:
    1. Keep a reference to the metrics_logger instance
    2. Periodically call get_summary_stats()
    3. Send data to your monitoring system
    """
    
    # In bot.py, you have access to the metrics_logger instance
    # This is just a demonstration of what you can do with it
    
    # Simulated metrics logger (in real use, this comes from your pipeline)
    metrics_logger = MetricsLogger()
    
    # Simulate some metrics (in reality, these come from the pipeline)
    metrics_logger.total_llm_tokens = {"prompt": 5420, "completion": 340}
    metrics_logger.total_tts_characters = 1580
    metrics_logger.ttfb_measurements = [245.32, 230.15, 250.80, 235.60]
    metrics_logger.processing_times = [150.25, 145.30, 155.10, 148.90]
    
    # Get summary statistics
    stats = metrics_logger.get_summary_stats()
    
    print("=" * 80)
    print("METRICS ANALYSIS EXAMPLE")
    print("=" * 80)
    print()
    
    # 1. Performance Analysis
    print("📊 PERFORMANCE METRICS")
    print("-" * 80)
    print(f"Average TTFB: {stats['ttfb']['average_ms']:.2f}ms")
    print(f"Min TTFB: {stats['ttfb']['min_ms']:.2f}ms")
    print(f"Max TTFB: {stats['ttfb']['max_ms']:.2f}ms")
    print(f"TTFB Variance: {stats['ttfb']['max_ms'] - stats['ttfb']['min_ms']:.2f}ms")
    print()
    print(f"Average Processing Time: {stats['processing']['average_ms']:.2f}ms")
    print(f"Min Processing Time: {stats['processing']['min_ms']:.2f}ms")
    print(f"Max Processing Time: {stats['processing']['max_ms']:.2f}ms")
    print()
    
    # 2. Usage Analysis
    print("💰 USAGE & COST METRICS")
    print("-" * 80)
    total_tokens = stats['llm_tokens']['total_combined']
    prompt_tokens = stats['llm_tokens']['total_prompt']
    completion_tokens = stats['llm_tokens']['total_completion']
    
    # Calculate costs (GPT-4 pricing)
    prompt_cost = prompt_tokens * 0.00003
    completion_cost = completion_tokens * 0.00006
    total_llm_cost = prompt_cost + completion_cost
    
    print(f"Total LLM Tokens: {total_tokens:,}")
    print(f"  - Prompt: {prompt_tokens:,} tokens (${prompt_cost:.4f})")
    print(f"  - Completion: {completion_tokens:,} tokens (${completion_cost:.4f})")
    print(f"  - Total Cost: ${total_llm_cost:.4f}")
    print()
    
    # TTS costs
    total_chars = stats['tts_characters']['total']
    tts_cost = total_chars * 0.000015
    print(f"Total TTS Characters: {total_chars:,}")
    print(f"  - Cost: ${tts_cost:.4f}")
    print()
    
    # Combined costs
    total_cost = total_llm_cost + tts_cost
    print(f"Total Session Cost: ${total_cost:.4f}")
    print()
    
    # 3. Efficiency Metrics
    print("📈 EFFICIENCY METRICS")
    print("-" * 80)
    if total_tokens > 0:
        cost_per_token = total_llm_cost / total_tokens
        print(f"Cost per Token: ${cost_per_token:.6f}")
    
    if total_chars > 0:
        cost_per_char = tts_cost / total_chars
        print(f"Cost per Character: ${cost_per_char:.6f}")
    
    if stats['session_duration_seconds'] > 0:
        tokens_per_second = total_tokens / stats['session_duration_seconds']
        chars_per_second = total_chars / stats['session_duration_seconds']
        print(f"Tokens per Second: {tokens_per_second:.2f}")
        print(f"Characters per Second: {chars_per_second:.2f}")
    print()
    
    # 4. Export to JSON for monitoring systems
    print("📤 EXPORT TO JSON")
    print("-" * 80)
    
    # Create a monitoring payload
    monitoring_payload = {
        "timestamp": datetime.now().isoformat(),
        "session_duration_seconds": stats['session_duration_seconds'],
        "performance": {
            "ttfb_avg_ms": stats['ttfb']['average_ms'],
            "ttfb_min_ms": stats['ttfb']['min_ms'],
            "ttfb_max_ms": stats['ttfb']['max_ms'],
            "processing_avg_ms": stats['processing']['average_ms'],
        },
        "usage": {
            "llm_tokens_total": total_tokens,
            "llm_tokens_prompt": prompt_tokens,
            "llm_tokens_completion": completion_tokens,
            "tts_characters_total": total_chars,
        },
        "costs": {
            "llm_cost_usd": total_llm_cost,
            "tts_cost_usd": tts_cost,
            "total_cost_usd": total_cost,
        }
    }
    
    print(json.dumps(monitoring_payload, indent=2))
    print()
    
    # 5. Alerting Examples
    print("🚨 ALERTING EXAMPLES")
    print("-" * 80)
    
    # Check for performance issues
    if stats['ttfb']['average_ms'] > 500:
        print("⚠️  WARNING: Average TTFB exceeds 500ms threshold")
    
    # Check for cost overruns
    if total_cost > 1.0:
        print(f"⚠️  WARNING: Session cost (${total_cost:.4f}) exceeds $1.00 budget")
    
    # Check for high variance in TTFB
    ttfb_variance = stats['ttfb']['max_ms'] - stats['ttfb']['min_ms']
    if ttfb_variance > 200:
        print(f"⚠️  WARNING: High TTFB variance ({ttfb_variance:.2f}ms) indicates inconsistent performance")
    
    print()
    print("=" * 80)


def example_real_time_monitoring():
    """
    Example of how to implement real-time monitoring in your bot.
    
    You would add this logic to your bot.py to periodically check metrics
    and send them to a monitoring service.
    """
    
    print("\n" + "=" * 80)
    print("REAL-TIME MONITORING EXAMPLE")
    print("=" * 80)
    print()
    
    print("In your bot.py, you can add periodic monitoring:")
    print()
    print("```python")
    print("import asyncio")
    print()
    print("async def periodic_metrics_report(metrics_logger, interval_seconds=60):")
    print("    '''Send metrics to monitoring system every N seconds'''")
    print("    while True:")
    print("        await asyncio.sleep(interval_seconds)")
    print("        stats = metrics_logger.get_summary_stats()")
    print("        ")
    print("        # Send to your monitoring service")
    print("        # await send_to_datadog(stats)")
    print("        # await send_to_prometheus(stats)")
    print("        # await send_to_cloudwatch(stats)")
    print("        ")
    print("        # Or log for analysis")
    print("        logger.info(f'Periodic Metrics: {json.dumps(stats)}')")
    print()
    print("# Start the monitoring task")
    print("asyncio.create_task(periodic_metrics_report(metrics_logger, interval_seconds=60))")
    print("```")
    print()


def example_custom_metric_processor():
    """
    Example of extending the MetricsLogger for custom metrics.
    """
    
    print("\n" + "=" * 80)
    print("CUSTOM METRICS PROCESSOR EXAMPLE")
    print("=" * 80)
    print()
    
    print("You can extend MetricsLogger to add custom metrics:")
    print()
    print("```python")
    print("from metrics_logger import MetricsLogger")
    print("from pipecat.metrics.metrics import MetricsData")
    print()
    print("class EnhancedMetricsLogger(MetricsLogger):")
    print("    def __init__(self):")
    print("        super().__init__()")
    print("        self.custom_metrics = {}")
    print("    ")
    print("    async def _process_metrics_frame(self, frame):")
    print("        # Call parent processing first")
    print("        await super()._process_metrics_frame(frame)")
    print("        ")
    print("        # Add your custom metric handling")
    print("        for metric_data in frame.data:")
    print("            if isinstance(metric_data, YourCustomMetricType):")
    print("                # Process your custom metric")
    print("                self.custom_metrics[metric_data.name] = metric_data.value")
    print("                logger.info(f'Custom Metric: {metric_data.name} = {metric_data.value}')")
    print("```")
    print()


if __name__ == "__main__":
    # Run the examples
    example_metrics_analysis()
    example_real_time_monitoring()
    example_custom_metric_processor()
    
    print("\n" + "=" * 80)
    print("For more information, see METRICS_GUIDE.md")
    print("=" * 80)
