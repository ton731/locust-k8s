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