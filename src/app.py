from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel


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