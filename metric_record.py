import os
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# otel metrics 
OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "llm-telemetry-service")
exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)


metric_reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15000) # 15-second fast flush

# Set up the global Meter Provider
provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("signoz-akash-llm-telemetry-meter")

# LLM SERVER
# Counter to keep track of total tokens processed over time
server_token_counter = meter.create_counter(
    name="llm_tokens_total",
    description="Total number of tokens processed by the LLM",
    unit="{tokens}"
)

# Histogram to measure distribution of inference response times
server_inference_duration = meter.create_histogram(
    name="llm_inference_duration",
    description="Time taken by the model to generate a response",
    unit="s"
)

# LLM CLIENT METRICS
# Counter to log all request occurrences (and split by success/failure via attributes)
client_request_counter = meter.create_counter(
    name="llm_client_requests_total",
    description="Total number of HTTP requests sent by the client",
    unit="{requests}"
)

# Histogram to track total round-trip latency from the client's perspective
client_latency_histogram = meter.create_histogram(
    name="llm_client_request_duration_seconds",
    description="Total execution latency of the client request call",
    unit="s"
)