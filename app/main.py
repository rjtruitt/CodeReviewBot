import uvicorn
from fastapi import FastAPI
from app.routers import router as app_router
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

app = FastAPI()
app.include_router(app_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
