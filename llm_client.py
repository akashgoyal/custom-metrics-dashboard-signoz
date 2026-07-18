import os
import time
import httpx

# otel 
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
##

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000/generate")

# sample prompts 
BASE_PROMPTS = [
    "Tell me a short joke about coding.",
    "Explain quantum computing in one simple sentence.",
    "Write a short, five-word poem about artificial intelligence.",
    "What is the ultimate answer to life, the universe, and everything?",
    "Give me a quick tip to improve Python code performance right now."
] * 5

def run_batch_inference():
    # Parent span for the whole batch execution
    with tracer.start_as_current_span("client_batch_inference") as batch_span:
        print("Starting client inference batch...")
        
        with httpx.Client() as client:
            for i, prompt in enumerate(BASE_PROMPTS):
                # Child span for each specific request cycle
                span_name = f"client_request_call_{i+1}"
                with tracer.start_as_current_span(span_name) as request_span:
                    
                    # Add request context to the span metadata
                    request_span.set_attribute("client.prompt_text", prompt)
                    request_span.set_attribute("client.prompt_char_length", len(prompt))
                    
                    payload = {"prompt": prompt}
                    start_time = time.perf_counter()
                    
                    try:
                        print(f"\n[Call {i+1}] Sending prompt ({len(prompt)} chars)...")
                        response = client.post(SERVER_URL, json=payload, timeout=60.0)
                        
                        # Calculate exact elapsed duration for this client transaction
                        elapsed_time = time.perf_counter() - start_time
                        request_span.set_attribute("client.elapsed_time_seconds", elapsed_time)
                        request_span.set_attribute("client.http_status_code", response.status_code)
                        
                        if response.status_code == 200:
                            result = response.json().get("result", "")
                            print(f"[Call {i+1}] Success in {elapsed_time:.3f}s!")
                            request_span.set_status(trace.StatusCode.OK)
                        else:
                            print(f"[Call {i+1}] Failed with status code: {response.status_code}")
                            request_span.set_status(
                                trace.StatusCode.ERROR, 
                                description=f"HTTP Error {response.status_code}"
                            )
                            
                    except Exception as e:
                        elapsed_time = time.perf_counter() - start_time
                        print(f"[Call {i+1}] Exception encountered: {str(e)}")
                        
                        request_span.set_attribute("client.elapsed_time_seconds", elapsed_time)
                        request_span.record_exception(e)
                        request_span.set_status(trace.StatusCode.ERROR, description=str(e))

if __name__ == "__main__":
    # Ensure your llm_server.py is running on port 8000 before executing this
    run_batch_inference()