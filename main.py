from fastapi import FastAPI
from pydantic import BaseModel
from generated_text_detector.utils.model.roberta_classifier import RobertaClassifier
from generated_text_detector.utils.preprocessing import preprocessing_text
from transformers import AutoTokenizer
import torch
import torch.nn.functional as F

class CommentRequest(BaseModel):
    comment: str

class PredictionResponse(BaseModel):
    probability: float

app = FastAPI(title="AI Text Detector API")

model = RobertaClassifier.from_pretrained("SuperAnnotate/ai-detector")
tokenizer = AutoTokenizer.from_pretrained("SuperAnnotate/ai-detector")
model.eval()

@app.post("/predict", response_model=PredictionResponse)
def predict(request: CommentRequest):
    text = preprocessing_text(request.comment)

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

    return PredictionResponse(probability=proba)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)