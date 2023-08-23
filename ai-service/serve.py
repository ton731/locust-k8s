from typing import Union, Dict, Any, AnyStr
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/predict")
def predict(input_data: Dict[AnyStr, Any]):
    print("In the /predict endpoint...")
    return {"name": "Tony Chou"}


@app.get("/predict/health-check")
def health_check():
    return {"app_version": '1325456312'}


@app.get("/predict/resc-usage")
def resc_usage():
    return {
        "cpu_percent": 10,
        "cpu_count": 2,
        "memory_percent": 12,
        "memory_used (bytes)": 123,
    }
