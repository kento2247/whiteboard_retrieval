from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.domain.vector_store import VectorStore

vector_store = VectorStore()

app = FastAPI()

# "static" フォルダを静的ファイル用にマウント
app.mount("/static", StaticFiles(directory="static"), name="static")


# データモデル（例：画像とテキストペア）
class ImageTextPair(BaseModel):
    image_url: str
    description: str


# index.html を返すルートエンドポイント
@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse("static/index.html")


@app.get("/search", response_class=FileResponse)
async def read_search():
    return FileResponse("static/search.html")


@app.get("/record", response_class=FileResponse)
async def read_record():
    return FileResponse("static/record.html")


@app.get("/list", response_class=FileResponse)
async def read_list():
    return FileResponse("static/list.html")


@app.post("/api/debate/{debate_id}/image")
async def add_image_to_debate(
    debate_id: int,
    file: UploadFile = File(...)
):
    try:
        file_path = f"static/uploads/{file.filename}"
        Path("static/uploads").mkdir(parents=True, exist_ok=True)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        image_id = vector_store.process_and_add_image(debate_id, file_path)
        
        return {"message": "Successfully added image", "image_id": image_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_images(query: str):
    try:
        results = vector_store.search_by_text(query)
        return {
            "results": [
                {
                    "image_path": path,
                    "distance": dist,
                    "ocr": ocr,
                    "tldr": tldr
                }
                for path, dist, ocr, tldr in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
