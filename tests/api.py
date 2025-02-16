from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

dist_dir = Path(__file__).parent.resolve().parent / "dist"
if not dist_dir.exists():
    dist_dir.mkdir()
app = FastAPI()
app.mount("/dist", StaticFiles(directory=dist_dir))
