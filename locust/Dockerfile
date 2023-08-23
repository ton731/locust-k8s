FROM locustio/locust:2.16.1

WORKDIR /locust-test

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY test_case.py .
COPY run.py .

# Start Locust using LOCUS_OPTS environment variable
ENTRYPOINT ["python", "./run.py"]