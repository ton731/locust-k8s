FROM python:3.9-alpine

WORKDIR /code

COPY ai-service/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ai-service/serve.py /code/

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "80"]