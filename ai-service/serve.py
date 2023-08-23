from typing import Union, Dict, Any, AnyStr
from fastapi import FastAPI
import random
import uvicorn


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
        "cpu_percent": random.randint(1, 100),
        "cpu_count": random.randint(1, 3),
        "memory_percent": random.randint(1, 100),
        "memory_used (bytes)": random.randint(50, 100000),
    }


def main():
    uvicorn.run("serve:app", host="0.0.0.0", port=80)


if __name__ == "__main__":
    main()


