# MEMOSHIRO: 自然言語に基づくWhiteboard画像検索
smilab mini hackathon 2025

## setup
```sh
pyenv install 3.10.13
pyenv virtualenv 3.10.13 wr
pyenv local wr
python3.10 -m pip install --upgrade pip
pip install poetry
poetry install
```

## env
```sh
MISTRAL_API_KEY=
```

## run
```sh
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
