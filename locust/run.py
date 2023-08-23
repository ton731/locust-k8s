import subprocess
import os
import multiprocessing
from datetime import datetime
import json
import requests
import csv
import time


def get_request_response(endpoint):
    listen_host = "http://fake-ai-service.stress-test.svc.cluster.local"
    router = "/predict"

    url = listen_host + router + endpoint

    response = requests.get(url)
    if not response:   
        raise Exception("Request get empty response, maybe due to server not correctly running on k8s.")
    
    response_text = json.loads(response.text)
    return response_text


def run_resource_monitoring():
    print("***** Start monitoring...")
    duration_seconds = 150
    interval_seconds = 5
    total_requests = duration_seconds / interval_seconds
    csv_path = "ai_service_resource_usage.csv"

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'CPU_Percent', 'CPU_Count', 'Memory_Percent', 'Memory_Used_Bytes'])

        for _ in range(int(total_requests)):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            resource_usage = get_request_response('/resc-usage')
            print("***** Got resource usage from the AI Service...")
            
            writer.writerow([
                timestamp, 
                resource_usage['cpu_percent'], 
                resource_usage['cpu_count'], 
                resource_usage['memory_percent'], 
                resource_usage['memory_used (bytes)']
            ])
            time.sleep(interval_seconds)

    print("***** Finished monitoring...")


def run_locust():
    LOCUST = "locust"
    TARGET_HOST = "http://fake-ai-service.stress-test.svc.cluster.local"
    LOCUS_OPTS = f"-f /locust-test/test_case.py --headless --host={TARGET_HOST}"
    LOCUST_MODE = os.environ.get("LOCUST_MODE", "standalone")

    if LOCUST_MODE == "master":
        MASTER_OPTS = "--run-time 2m30s --csv /locust-test/result.csv"
        LOCUS_OPTS = f"{LOCUS_OPTS} --master --master-port=5557 {MASTER_OPTS}"

        # Start a new process for resource monitoring only if LOCUST_MODE is "master"
        resource_monitor_process = multiprocessing.Process(target=run_resource_monitoring)
        resource_monitor_process.start()

    elif LOCUST_MODE == "worker":
        LOCUST_MASTER_URL = os.environ.get("LOCUST_MASTER_URL", "")
        WORKER_OPTS = "-u 1000 -r 10"
        LOCUS_OPTS = f"{LOCUS_OPTS} --worker --master-port=5557 --master-host={LOCUST_MASTER_URL} {WORKER_OPTS}"

    command = f"{LOCUST} {LOCUS_OPTS}"
    print(command)

    subprocess.run(command, shell=True)



if __name__ == "__main__":

    run_locust()

