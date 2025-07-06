import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from yandex_cloud_ml_sdk import YCloudML
import concurrent.futures


class GenerateRequest(BaseModel):
    comment: str
    max_tokens: int = 128

class GenerateResponse(BaseModel):
    result: str


YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")
if not YANDEX_API_KEY:
    raise RuntimeError("YANDEX_API_KEY not set")
if not FOLDER_ID:
    raise RuntimeError("FOLDER_ID not set")

WORKERS = int(os.environ.get("WORKERS", 4))
executor = concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS)

app = FastAPI(title="YandexGPT API Service")

def predict_sync(comment: str, max_tokens: int = 128) -> str:
    sdk = YCloudML(folder_id=FOLDER_ID, auth=YANDEX_API_KEY)
    model = sdk.models.completions('yandexgpt')
    model = model.configure(max_tokens=max_tokens)
    prompt = "Тебе на вход дан комментарий пользователя. Твоя задача - оценить его объективность. Выведи в ответе только одно вещественное число от 0 до 1, вероятность того, что комментарий не объективен. Комментарий: " + comment
    result = model.run(prompt)
    return result[0].text

@app.post("/llm_predict", response_model=GenerateResponse)
async def predict(request: GenerateRequest):
    if not request.comment:
        raise HTTPException(status_code=400, detail="No comment provided")
    try:
        loop = None
        try:
            import asyncio
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop:
            result = await loop.run_in_executor(executor, predict_sync, request.comment, request.max_tokens)
        else:
            result = predict_sync(request.comment, request.max_tokens)
        return GenerateResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)