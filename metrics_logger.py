"""
Voice Metrics Logger - Custom Processor for Capturing Voice Pipeline Metrics

This module provides a custom FrameProcessor that captures and logs comprehensive
metrics from the Pipecat voice pipeline, including:
- Time to First Byte (TTFB) for LLM and TTS responses
- Processing time for various pipeline stages
- Token usage for LLM operations
- Character usage for TTS operations
- Smart Turn prediction data
- Additional enrichment metrics

The metrics are logged to the console and can be extended to send to monitoring
systems like Prometheus, DataDog, or custom analytics platforms.
"""

from pipecat.frames.frames import Frame, MetricsFrame
from pipecat.metrics.metrics import (
    LLMUsageMetricsData,
    ProcessingMetricsData,
    TTFBMetricsData,
    TTSUsageMetricsData,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from loguru import logger
from typing import Dict, Any
import json
from datetime import datetime


class MetricsLogger(FrameProcessor):
    """
    Custom processor that captures and logs voice pipeline metrics.
    
    This processor sits in the pipeline and intercepts MetricsFrame objects,
    extracting various performance and usage metrics for monitoring and analysis.
    
    Captured Metrics:
    - TTFB (Time to First Byte): Latency for first response chunk
    - Processing Time: Duration of various processing stages
    - LLM Token Usage: Prompt and completion tokens consumed
    - TTS Character Usage: Characters converted to speech
    - Smart Turn Data: Conversation turn-taking predictions
    
    The metrics are logged with timestamps and can be extended to:
    - Send to monitoring dashboards
    - Store in time-series databases
    - Trigger alerts on anomalies
    - Generate analytics reports
    """
    
    def __init__(self):
        """Initialize the metrics logger with tracking state."""
        super().__init__()
        
        # Cumulative metrics tracking
        self.total_llm_tokens = {"prompt": 0, "completion": 0}
        self.total_tts_characters = 0
        self.ttfb_measurements = []
        self.processing_times = []
        
        # Session start time for elapsed time calculations
        self.session_start = datetime.now()
        
        logger.info("MetricsLogger initialized - monitoring voice pipeline metrics")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process each frame in the pipeline, capturing metrics when present.
        
        Args:
            frame: The frame to process (could be any frame type)
            direction: Direction of frame flow (upstream/downstream)
        """
        # Call parent class processing first
        await super().process_frame(frame, direction)
        
        # Check if this is a MetricsFrame containing performance data
        if isinstance(frame, MetricsFrame):
            await self._process_metrics_frame(frame)
        
        # Always push the frame downstream to continue pipeline flow
        await self.push_frame(frame, direction)
    
    async def _process_metrics_frame(self, frame: MetricsFrame):
        """
        Extract and log metrics from a MetricsFrame.
        
        Args:
            frame: MetricsFrame containing one or more metric data objects
        """
        # Get current timestamp for this metrics event
        timestamp = datetime.now()
        elapsed_time = (timestamp - self.session_start).total_seconds()
        
        # MetricsFrame.data is a list of different metric types
        # We iterate through and handle each type appropriately
        for metric_data in frame.data:
            
            # ================================================================
            # TTFB (Time to First Byte) Metrics
            # ================================================================
            # Measures latency from request to first response chunk
            # Critical for perceived responsiveness
            if isinstance(metric_data, TTFBMetricsData):
                ttfb_ms = metric_data.value
                self.ttfb_measurements.append(ttfb_ms)
                
                # Calculate rolling average for trend analysis
                avg_ttfb = sum(self.ttfb_measurements) / len(self.ttfb_measurements)
                
                logger.info(
                    f"📊 TTFB Metric | "
                    f"Current: {ttfb_ms:.2f}ms | "
                    f"Average: {avg_ttfb:.2f}ms | "
                    f"Processor: {metric_data.processor} | "
                    f"Elapsed: {elapsed_time:.1f}s"
                )
                
                # Log detailed metric data for analysis
                self._log_metric_detail({
                    "type": "ttfb",
                    "value_ms": ttfb_ms,
                    "average_ms": avg_ttfb,
                    "processor": metric_data.processor,
                    "timestamp": timestamp.isoformat(),
                    "elapsed_seconds": elapsed_time
                })
            
            # ================================================================
            # Processing Time Metrics
            # ================================================================
            # Measures duration of processing stages in the pipeline
            # Helps identify bottlenecks
            elif isinstance(metric_data, ProcessingMetricsData):
                processing_ms = metric_data.value
                self.processing_times.append(processing_ms)
                
                # Calculate statistics
                avg_processing = sum(self.processing_times) / len(self.processing_times)
                max_processing = max(self.processing_times)
                
                logger.info(
                    f"⚙️  Processing Metric | "
                    f"Duration: {processing_ms:.2f}ms | "
                    f"Average: {avg_processing:.2f}ms | "
                    f"Max: {max_processing:.2f}ms | "
                    f"Processor: {metric_data.processor}"
                )
                
                self._log_metric_detail({
                    "type": "processing",
                    "value_ms": processing_ms,
                    "average_ms": avg_processing,
                    "max_ms": max_processing,
                    "processor": metric_data.processor,
                    "timestamp": timestamp.isoformat()
                })

                # Specific logging for LLM response time
                if "llm" in metric_data.processor.lower():
                    logger.info(
                        f"⏱️  LLM Response Turn Around Time: {processing_ms:.2f}ms"
                    )
                # Specific logging for STT response time
                elif "stt" in metric_data.processor.lower() or "gladia" in metric_data.processor.lower():
                    logger.info(
                        f"⏱️  STT Response Time: {processing_ms:.2f}ms"
                    )
                # Specific logging for TTS response time
                elif "tts" in metric_data.processor.lower() or "cartesia" in metric_data.processor.lower():
                    logger.info(
                        f"⏱️  TTS Response Time: {processing_ms:.2f}ms"
                    )
            
            # ================================================================
            # LLM Token Usage Metrics
            # ================================================================
            # Tracks tokens consumed by language model operations
            # Important for cost tracking and quota management
            elif isinstance(metric_data, LLMUsageMetricsData):
                tokens = metric_data.value
                prompt_tokens = tokens.prompt_tokens
                completion_tokens = tokens.completion_tokens
                total_tokens = prompt_tokens + completion_tokens
                
                # Update cumulative totals
                self.total_llm_tokens["prompt"] += prompt_tokens
                self.total_llm_tokens["completion"] += completion_tokens
                
                # Calculate cost estimate (GPT-4 pricing as example)
                # Adjust these rates based on your actual model pricing
                prompt_cost = prompt_tokens * 0.00003  # $0.03 per 1K tokens
                completion_cost = completion_tokens * 0.00006  # $0.06 per 1K tokens
                total_cost = prompt_cost + completion_cost
                
                logger.info(
                    f"🤖 LLM Usage Metric | "
                    f"Prompt: {prompt_tokens} tokens | "
                    f"Completion: {completion_tokens} tokens | "
                    f"Total: {total_tokens} tokens | "
                    f"Est. Cost: ${total_cost:.4f} | "
                    f"Processor: {metric_data.processor}"
                )
                
                logger.info(
                    f"📈 Cumulative LLM Usage | "
                    f"Total Prompt: {self.total_llm_tokens['prompt']} | "
                    f"Total Completion: {self.total_llm_tokens['completion']} | "
                    f"Grand Total: {sum(self.total_llm_tokens.values())} tokens"
                )
                
                self._log_metric_detail({
                    "type": "llm_usage",
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": total_cost,
                    "cumulative_prompt_tokens": self.total_llm_tokens["prompt"],
                    "cumulative_completion_tokens": self.total_llm_tokens["completion"],
                    "processor": metric_data.processor,
                    "timestamp": timestamp.isoformat()
                })
            
            # ================================================================
            # TTS Character Usage Metrics
            # ================================================================
            # Tracks characters converted to speech
            # Important for TTS service cost tracking
            elif isinstance(metric_data, TTSUsageMetricsData):
                characters = metric_data.value
                self.total_tts_characters += characters
                
                # Calculate cost estimate (Cartesia pricing as example)
                # Adjust based on your actual TTS service pricing
                cost_per_char = 0.000015  # Example: $15 per 1M characters
                char_cost = characters * cost_per_char
                
                logger.info(
                    f"🔊 TTS Usage Metric | "
                    f"Characters: {characters} | "
                    f"Est. Cost: ${char_cost:.4f} | "
                    f"Processor: {metric_data.processor}"
                )
                
                logger.info(
                    f"📈 Cumulative TTS Usage | "
                    f"Total Characters: {self.total_tts_characters}"
                )
                
                self._log_metric_detail({
                    "type": "tts_usage",
                    "characters": characters,
                    "estimated_cost_usd": char_cost,
                    "cumulative_characters": self.total_tts_characters,
                    "processor": metric_data.processor,
                    "timestamp": timestamp.isoformat()
                })
            
            # ================================================================
            # Additional Metric Types
            # ================================================================
            # Handle any other metric types that might be present
            else:
                logger.debug(
                    f"🔍 Unknown Metric Type | "
                    f"Type: {type(metric_data).__name__} | "
                    f"Frame: {frame}"
                )
                
                # Try to extract any available data
                if hasattr(metric_data, 'value'):
                    logger.debug(f"   Value: {metric_data.value}")
                if hasattr(metric_data, 'processor'):
                    logger.debug(f"   Processor: {metric_data.processor}")
    
    def _log_metric_detail(self, metric_dict: Dict[str, Any]):
        """
        Log detailed metric data in JSON format for structured logging.
        
        This can be parsed by log aggregation tools like ELK, Splunk, etc.
        
        Args:
            metric_dict: Dictionary containing metric details
        """
        # Log as JSON for easy parsing by monitoring tools
        logger.debug(f"METRIC_JSON: {json.dumps(metric_dict)}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all captured metrics.
        
        Returns:
            Dictionary containing aggregated metrics and statistics
        """
        return {
            "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "llm_tokens": {
                "total_prompt": self.total_llm_tokens["prompt"],
                "total_completion": self.total_llm_tokens["completion"],
                "total_combined": sum(self.total_llm_tokens.values())
            },
            "tts_characters": {
                "total": self.total_tts_characters
            },
            "ttfb": {
                "count": len(self.ttfb_measurements),
                "average_ms": sum(self.ttfb_measurements) / len(self.ttfb_measurements) if self.ttfb_measurements else 0,
                "min_ms": min(self.ttfb_measurements) if self.ttfb_measurements else 0,
                "max_ms": max(self.ttfb_measurements) if self.ttfb_measurements else 0
            },
            "processing": {
                "count": len(self.processing_times),
                "average_ms": sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0,
                "min_ms": min(self.processing_times) if self.processing_times else 0,
                "max_ms": max(self.processing_times) if self.processing_times else 0
            }
        }
    
    async def cleanup(self):
        """
        Cleanup method called when processor is being shut down.
        
        Logs final summary statistics before shutdown.
        """
        logger.info("=" * 80)
        logger.info("MetricsLogger Session Summary")
        logger.info("=" * 80)
        
        stats = self.get_summary_stats()
        logger.info(f"Session Duration: {stats['session_duration_seconds']:.1f} seconds")
        logger.info(f"Total LLM Tokens: {stats['llm_tokens']['total_combined']}")
        logger.info(f"  - Prompt: {stats['llm_tokens']['total_prompt']}")
        logger.info(f"  - Completion: {stats['llm_tokens']['total_completion']}")
        logger.info(f"Total TTS Characters: {stats['tts_characters']['total']}")
        
        if stats['ttfb']['count'] > 0:
            logger.info(f"TTFB Stats: Avg={stats['ttfb']['average_ms']:.2f}ms, "
                       f"Min={stats['ttfb']['min_ms']:.2f}ms, "
                       f"Max={stats['ttfb']['max_ms']:.2f}ms")
        
        if stats['processing']['count'] > 0:
            logger.info(f"Processing Stats: Avg={stats['processing']['average_ms']:.2f}ms, "
                       f"Min={stats['processing']['min_ms']:.2f}ms, "
                       f"Max={stats['processing']['max_ms']:.2f}ms")
        
        logger.info("=" * 80)
        
        await super().cleanup()
