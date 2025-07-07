import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from yandex_cloud_ml_sdk import YCloudML
import concurrent.futures


class GenerateRequest(BaseModel):
    comment: str
    max_tokens: int = 128

class GenerateResponse(BaseModel):
    probability: str


YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")
if not YANDEX_API_KEY:
    raise RuntimeError("YANDEX_API_KEY not set")
if not FOLDER_ID:
    raise RuntimeError("FOLDER_ID not set")

WORKERS = int(os.environ.get("WORKERS", 4))
executor = concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS)

app = FastAPI(title="YandexGPT API Service")

system_prompt = """Вам на вход предоставлен комментарий пользователя. Ваша задача — оценить степень его необъективности (субъективности) и вернуть единственное вещественное число от 0.0 до 1.0, равное вероятности того, что комментарий не является объективным.

При анализе учитывайте следующие признаки необъективности:
1. Эмоциональная или оценочная лексика (например: «ужасно», «превосходно», «абсолютно глупо»).
2. Личные местоимения и выражения мнения без фактов («я считаю», «мне кажется», «по моему»).
3. Оскорбительные или уничижительные высказывания («идиот», «тупица» и т. п.).
4. Необоснованные обобщения («все», «никто», «всегда», «никогда») без конкретных данных.
5. Спекуляции и предположения, не подкреплённые фактами («должно быть», «вероятно»).

Выход:
— Единственное число от 0.0 (полностью объективно) до 1.0 (полностью субъективно).
— Никакого дополнительного текста.

Пример:
Комментарий: «Эта статья просто отвратительная, автор — полный некомпетент»
→ 0.92

Текста комментария:
"""

def predict_sync(comment: str, max_tokens: int = 128) -> str:
    sdk = YCloudML(folder_id=FOLDER_ID, auth=YANDEX_API_KEY)
    model = sdk.models.completions('yandexgpt')
    model = model.configure(max_tokens=max_tokens)
    prompt = system_prompt + comment
    proba = model.run(prompt)
    return proba[0].text

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
            proba = await loop.run_in_executor(executor, predict_sync, request.comment, request.max_tokens)
        else:
            proba = predict_sync(request.comment, request.max_tokens)
        return GenerateResponse(result=proba)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)