# Load model directly
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Optional, List

app = FastAPI(title="FT-llm Inference API")

class InferenceRequest(BaseModel):
    prompt: str


class LangModelInstruct:
    
    def __init__(
        self,
        model_name: str = "./microsoft_Phi-4-mini-instruct"
    ):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype="auto", device_map="auto", trust_remote_code=False)
        
        
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
        
        outputs = self.model.generate(**inputs, max_new_tokens=32000)
        print(self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
        return self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)

liobj = LangModelInstruct()


@app.post("/generate")
def generate(request: InferenceRequest):
    try:
        print(f"Received prompt length: {len(request.prompt)}")
        generation = liobj.infer_llama(request.prompt)
        return {"result": generation}
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        

if __name__ == "__main__":
    uvicorn.run("llm_server:app", host="0.0.0.0", port=8000)