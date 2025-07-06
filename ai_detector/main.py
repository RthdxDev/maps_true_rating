from fastapi import FastAPI
from pydantic import BaseModel
from generated_text_detector.utils.model.roberta_classifier import RobertaClassifier
from generated_text_detector.utils.preprocessing import preprocessing_text
from transformers import AutoTokenizer
import torch
import torch.nn.functional as F
import concurrent.futures
import asyncio
import os


class CommentRequest(BaseModel):
    comment: str

class PredictionResponse(BaseModel):
    probability: float


app = FastAPI(title="AI Text Detector API")

model = RobertaClassifier.from_pretrained("SuperAnnotate/ai-detector")
tokenizer = AutoTokenizer.from_pretrained("SuperAnnotate/ai-detector")
model.eval()

WORKERS = int(os.environ.get("WORKERS", 4))
executor = concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS)

def predict_sync(comment: str) -> float:
    text = preprocessing_text(comment)
    tokens = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=512,
        padding="longest",
        truncation=True,
        return_token_type_ids=True,
        return_tensors="pt"
    )
    with torch.no_grad():
        _, logits = model(**tokens)
        proba = torch.sigmoid(logits).squeeze(1).item()
    return proba

@app.post("/anti_llm_predict", response_model=PredictionResponse)
async def predict(request: CommentRequest):
    try:
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop:
            proba = await loop.run_in_executor(executor, predict_sync, request.comment)
        else:
            proba = predict_sync(request.comment)
        return PredictionResponse(probability=proba)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)