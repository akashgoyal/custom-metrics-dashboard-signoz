# Load model directly
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Optional, List

# OpenTelemetry setup
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


app = FastAPI(title="FT-llm Inference API")

class InferenceRequest(BaseModel):
    prompt: str


class LangModelInstruct:
    
    def __init__(
        self,
        model_name: str = "./llm_models/microsoft_Phi-3.5-mini-instruct"
    ):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype="auto", device_map={"":"cpu"}, trust_remote_code=False)
        
        
    def infer_llama(self, prompt):
        messages = [
            {"role": "user", "content": prompt},
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        
        # Calculate input tokens from the formatted chat template
        input_token_len = inputs["input_ids"].shape[-1]
        
        outputs = self.model.generate(**inputs, max_new_tokens=320)
        
        # Isolate the newly generated tokens
        generation_tokens = outputs[0][input_token_len:]
        output_token_len = generation_tokens.shape[-1]
        
        decoded_output = self.tokenizer.decode(generation_tokens, skip_special_tokens=True)
        print(self.tokenizer.decode(generation_tokens))
        
        return decoded_output, input_token_len, output_token_len

liobj = LangModelInstruct()


@app.post("/generate")
def generate(request: InferenceRequest):
    with tracer.start_as_current_span("generate_endpoint") as span:
        try:
            print(f"Received prompt length: {len(request.prompt)}")
            
            # Record initial request metadata
            span.set_attribute("llm.model_name", liobj.model_name)
            span.set_attribute("llm.input.prompt_char_length", len(request.prompt))
            
            # Run inference and get text + token metrics
            generation, input_tokens, output_tokens = liobj.infer_llama(request.prompt)
            
            # Record detailed token and response metrics to the span
            span.set_attribute("llm.input.token_length", input_tokens)
            span.set_attribute("llm.output.token_length", output_tokens)
            span.set_attribute("llm.output.response_char_length", len(generation))
            
            span.set_status(trace.StatusCode.OK)
            return {"result": generation}
            
        except Exception as e:
            print(f"Error during generation: {str(e)}")
            import traceback
            traceback.print_exc()
            
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            
            raise HTTPException(status_code=500, detail=str(e))
        

if __name__ == "__main__":
    uvicorn.run("llm_server:app", host="0.0.0.0", port=8000)