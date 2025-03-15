#!/usr/bin/env python
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

dist_dir = Path(__file__).parent.resolve().parent / "dist"
app = FastAPI()
app.mount("/dist", StaticFiles(directory=dist_dir, check_dir=False))


if __name__ == "__main__":
    uvicorn.run("__main__:app")
