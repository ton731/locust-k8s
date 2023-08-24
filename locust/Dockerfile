FROM gcr.io/jubo-ai/ai-integration_test:latest

WORKDIR /locust-test

COPY scripts/integration_test.py .
COPY scripts/test_case.py .
COPY scripts/config.yaml .
COPY scripts/run.py .

# Start Locust using LOCUS_OPTS environment variable
ENTRYPOINT ["python", "./run.py"]