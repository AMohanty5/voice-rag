"""
Grafana Cloud Metrics Exporter - OpenTelemetry Integration

This module provides integration with Grafana Cloud using OpenTelemetry Protocol (OTLP).
It captures voice pipeline metrics and sends them to Grafana Cloud for visualization
and monitoring.

Metrics Captured:
- Call-level metrics with unique Call ID
- Model information (LLM, STT, TTS)
- TTFB (Time to First Byte)
- Processing times
- Token and character usage
- Cost estimates
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

# OpenTelemetry imports
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Pipecat imports
from pipecat.frames.frames import Frame, MetricsFrame
from pipecat.metrics.metrics import (
    LLMUsageMetricsData,
    ProcessingMetricsData,
    TTFBMetricsData,
    TTSUsageMetricsData,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class GrafanaMetricsExporter(FrameProcessor):
    """
    Custom processor that exports voice pipeline metrics to Grafana Cloud.
    
    This processor:
    1. Generates unique Call IDs for each session
    2. Captures model information (LLM, STT, TTS)
    3. Sends all metrics to Grafana Cloud via OTLP
    4. Maintains call-level and session-level metrics
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o",
        stt_model: str = "gladia",
        tts_model: str = "cartesia",
        service_name: str = "voice-rag-bot"
    ):
        """
        Initialize Grafana metrics exporter.
        
        Args:
            llm_model: Name of the LLM model being used
            stt_model: Name of the STT model being used
            tts_model: Name of the TTS model being used
            service_name: Name of the service for resource identification
        """
        super().__init__()
        
        # Generate unique Call ID for this session
        self.call_id = str(uuid.uuid4())
        self.session_start = datetime.now()
        
        # Model information
        self.llm_model = llm_model
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.service_name = service_name
        
        # Cumulative metrics
        self.total_llm_tokens = {"prompt": 0, "completion": 0}
        self.total_tts_characters = 0
        self.ttfb_measurements = []
        self.processing_times = []
        self.total_calls = 0
        
        # Initialize OpenTelemetry
        self._setup_opentelemetry()
        
        logger.info("=" * 80)
        logger.info("🔗 Grafana Metrics Exporter Initialized")
        logger.info("=" * 80)
        logger.info(f"📞 Call ID: {self.call_id}")
        logger.info(f"🤖 LLM Model: {self.llm_model}")
        logger.info(f"🎤 STT Model: {self.stt_model}")
        logger.info(f"🔊 TTS Model: {self.tts_model}")
        logger.info(f"📊 Grafana Endpoint: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'Not configured')}")
        logger.info("=" * 80)
    
    def _setup_opentelemetry(self):
        """
        Set up OpenTelemetry with Grafana Cloud configuration.
        """
        # Get Grafana Cloud configuration from environment
        otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "https://otlp-gateway-prod-ap-south-1.grafana.net/otlp"
        )
        
        # Authorization header for Grafana Cloud
        auth_header = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        
        # Create resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.SERVICE_INSTANCE_ID: self.call_id,
            "call.id": self.call_id,
            "model.llm": self.llm_model,
            "model.stt": self.stt_model,
            "model.tts": self.tts_model,
        })
        
        # Parse authorization header
        headers = {}
        if auth_header:
            # Format: "Authorization=Basic%20<token>"
            headers["Authorization"] = auth_header.replace("Authorization=", "").replace("%20", " ")
        
        # Create OTLP exporter
        exporter = OTLPMetricExporter(
            endpoint=f"{otlp_endpoint}/v1/metrics",
            headers=headers
        )
        
        # Create metric reader with 10-second export interval
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)
        
        # Create meter provider
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        
        # Set global meter provider
        metrics.set_meter_provider(provider)
        
        # Get meter for creating instruments
        self.meter = metrics.get_meter(__name__)
        
        # Create metric instruments
        self._create_metrics()
        
        logger.info("✅ OpenTelemetry configured for Grafana Cloud")
    
    def _create_metrics(self):
        """
        Create OpenTelemetry metric instruments.
        """
        # Counter for total calls
        self.calls_counter = self.meter.create_counter(
            name="voice.calls.total",
            description="Total number of voice calls",
            unit="1"
        )
        
        # Histogram for TTFB
        self.ttfb_histogram = self.meter.create_histogram(
            name="voice.ttfb.milliseconds",
            description="Time to First Byte in milliseconds",
            unit="ms"
        )
        
        # Histogram for processing time
        self.processing_histogram = self.meter.create_histogram(
            name="voice.processing.milliseconds",
            description="Processing time in milliseconds",
            unit="ms"
        )
        
        # Counter for LLM tokens
        self.llm_tokens_counter = self.meter.create_counter(
            name="voice.llm.tokens.total",
            description="Total LLM tokens consumed",
            unit="1"
        )
        
        # Counter for TTS characters
        self.tts_characters_counter = self.meter.create_counter(
            name="voice.tts.characters.total",
            description="Total TTS characters processed",
            unit="1"
        )
        
        # Gauge for session duration
        self.session_duration_gauge = self.meter.create_up_down_counter(
            name="voice.session.duration.seconds",
            description="Current session duration in seconds",
            unit="s"
        )
        
        # Counter for estimated costs
        self.cost_counter = self.meter.create_counter(
            name="voice.cost.usd",
            description="Estimated cost in USD",
            unit="USD"
        )
        
        logger.info("✅ Metric instruments created")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process frames and export metrics to Grafana.
        
        Args:
            frame: The frame to process
            direction: Direction of frame flow
        """
        await super().process_frame(frame, direction)
        
        # Process metrics frames
        if isinstance(frame, MetricsFrame):
            await self._process_metrics_frame(frame)
        
        # Always push frame downstream
        await self.push_frame(frame, direction)
    
    async def _process_metrics_frame(self, frame: MetricsFrame):
        """
        Extract metrics from frame and send to Grafana.
        
        Args:
            frame: MetricsFrame containing metric data
        """
        timestamp = datetime.now()
        elapsed_time = (timestamp - self.session_start).total_seconds()
        
        # Common attributes for all metrics
        common_attrs = {
            "call_id": self.call_id,
            "llm_model": self.llm_model,
            "stt_model": self.stt_model,
            "tts_model": self.tts_model,
        }
        
        for metric_data in frame.data:
            
            # TTFB Metrics
            if isinstance(metric_data, TTFBMetricsData):
                ttfb_ms = metric_data.value
                self.ttfb_measurements.append(ttfb_ms)
                
                # Record TTFB histogram
                self.ttfb_histogram.record(
                    ttfb_ms,
                    attributes={
                        **common_attrs,
                        "processor": metric_data.processor,
                        "metric_type": "ttfb"
                    }
                )
                
                logger.info(
                    f"📊 [Grafana] TTFB: {ttfb_ms:.2f}ms | "
                    f"Processor: {metric_data.processor} | "
                    f"Call ID: {self.call_id[:8]}..."
                )
            
            # Processing Time Metrics
            elif isinstance(metric_data, ProcessingMetricsData):
                processing_ms = metric_data.value
                self.processing_times.append(processing_ms)
                
                # Record processing time histogram
                self.processing_histogram.record(
                    processing_ms,
                    attributes={
                        **common_attrs,
                        "processor": metric_data.processor,
                        "metric_type": "processing"
                    }
                )
                
                logger.info(
                    f"⚙️  [Grafana] Processing: {processing_ms:.2f}ms | "
                    f"Processor: {metric_data.processor}"
                )
            
            # LLM Token Usage Metrics
            elif isinstance(metric_data, LLMUsageMetricsData):
                tokens = metric_data.value
                prompt_tokens = tokens.prompt_tokens
                completion_tokens = tokens.completion_tokens
                total_tokens = prompt_tokens + completion_tokens
                
                # Update cumulative totals
                self.total_llm_tokens["prompt"] += prompt_tokens
                self.total_llm_tokens["completion"] += completion_tokens
                
                # Record token usage
                self.llm_tokens_counter.add(
                    prompt_tokens,
                    attributes={
                        **common_attrs,
                        "token_type": "prompt",
                        "processor": metric_data.processor
                    }
                )
                
                self.llm_tokens_counter.add(
                    completion_tokens,
                    attributes={
                        **common_attrs,
                        "token_type": "completion",
                        "processor": metric_data.processor
                    }
                )
                
                # Calculate and record cost
                prompt_cost = prompt_tokens * 0.00003  # GPT-4 pricing
                completion_cost = completion_tokens * 0.00006
                total_cost = prompt_cost + completion_cost
                
                self.cost_counter.add(
                    total_cost,
                    attributes={
                        **common_attrs,
                        "cost_type": "llm",
                        "processor": metric_data.processor
                    }
                )
                
                logger.info(
                    f"🤖 [Grafana] LLM Tokens: {total_tokens} "
                    f"(Prompt: {prompt_tokens}, Completion: {completion_tokens}) | "
                    f"Cost: ${total_cost:.4f}"
                )
            
            # TTS Character Usage Metrics
            elif isinstance(metric_data, TTSUsageMetricsData):
                characters = metric_data.value
                self.total_tts_characters += characters
                
                # Record character usage
                self.tts_characters_counter.add(
                    characters,
                    attributes={
                        **common_attrs,
                        "processor": metric_data.processor
                    }
                )
                
                # Calculate and record cost
                char_cost = characters * 0.000015  # Cartesia pricing
                
                self.cost_counter.add(
                    char_cost,
                    attributes={
                        **common_attrs,
                        "cost_type": "tts",
                        "processor": metric_data.processor
                    }
                )
                
                logger.info(
                    f"🔊 [Grafana] TTS Characters: {characters} | "
                    f"Cost: ${char_cost:.4f}"
                )
        
        # Update session duration
        self.session_duration_gauge.add(
            int(elapsed_time),
            attributes=common_attrs
        )
    
    def get_call_summary(self) -> Dict[str, Any]:
        """
        Get summary of current call metrics.
        
        Returns:
            Dictionary with call summary
        """
        elapsed = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "call_id": self.call_id,
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": elapsed,
            "models": {
                "llm": self.llm_model,
                "stt": self.stt_model,
                "tts": self.tts_model
            },
            "metrics": {
                "llm_tokens": {
                    "prompt": self.total_llm_tokens["prompt"],
                    "completion": self.total_llm_tokens["completion"],
                    "total": sum(self.total_llm_tokens.values())
                },
                "tts_characters": self.total_tts_characters,
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
        }
    
    async def cleanup(self):
        """
        Cleanup and log final call summary.
        """
        summary = self.get_call_summary()
        
        logger.info("=" * 80)
        logger.info("📊 Grafana Metrics - Call Summary")
        logger.info("=" * 80)
        logger.info(f"📞 Call ID: {summary['call_id']}")
        logger.info(f"⏱️  Duration: {summary['session_duration_seconds']:.1f}s")
        logger.info(f"🤖 LLM Model: {summary['models']['llm']}")
        logger.info(f"🎤 STT Model: {summary['models']['stt']}")
        logger.info(f"🔊 TTS Model: {summary['models']['tts']}")
        logger.info(f"📝 Total LLM Tokens: {summary['metrics']['llm_tokens']['total']}")
        logger.info(f"   - Prompt: {summary['metrics']['llm_tokens']['prompt']}")
        logger.info(f"   - Completion: {summary['metrics']['llm_tokens']['completion']}")
        logger.info(f"🔤 Total TTS Characters: {summary['metrics']['tts_characters']}")
        
        if summary['metrics']['ttfb']['count'] > 0:
            logger.info(
                f"⚡ TTFB: Avg={summary['metrics']['ttfb']['average_ms']:.2f}ms, "
                f"Min={summary['metrics']['ttfb']['min_ms']:.2f}ms, "
                f"Max={summary['metrics']['ttfb']['max_ms']:.2f}ms"
            )
        
        logger.info("=" * 80)
        logger.info("✅ Metrics exported to Grafana Cloud")
        logger.info("=" * 80)
        
        await super().cleanup()
