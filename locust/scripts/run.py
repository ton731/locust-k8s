import subprocess
import os
from multiprocessing import Process, Event
from datetime import datetime

from integration_test import compute_rescusage_csv, load_config, get_csv_path


def run_locust(config, completion_event, csv_path_output):
    LOCUST = "locust"
    TARGET_HOST = config['listen_host']
    LOCUS_OPTS = f"-f /locust-test/test_case.py --headless --host={TARGET_HOST}"
    LOCUST_MODE = os.environ.get("LOCUST_MODE", "standalone")
    DURATION = config['duration']
    USER = config['num_user']
    SPAWN_RATE = config['spawn_rate']
    start_time = datetime.now()

    if LOCUST_MODE == "master":
        MASTER_OPTS = f'--run-time {DURATION} --csv reports/result --usage_csv {csv_path_output} --start_time "{start_time}"'
        LOCUS_OPTS = f"{LOCUS_OPTS} --master --master-port=5557 {MASTER_OPTS}"

    elif LOCUST_MODE == "worker":
        LOCUST_MASTER_URL = os.environ.get("LOCUST_MASTER_URL", "")
        WORKER_OPTS = f"-u {USER} -r {SPAWN_RATE}"
        LOCUS_OPTS = f"{LOCUS_OPTS} --worker --master-port=5557 --master-host={LOCUST_MASTER_URL} {WORKER_OPTS}"

    command = f"{LOCUST} {LOCUS_OPTS}"
    print(command)

    subprocess.run(command, shell=True)
    
    if LOCUST_MODE == "master":
        # Wait for the compute_rescusage_csv function to complete
        completion_event.wait()


def parallel_run_resc_and_locust(config):
    LOCUST_MODE = os.environ.get("LOCUST_MODE", "standalone")

    # Create an event to signal completion of compute_rescusage_csv
    completion_event = Event()

    if LOCUST_MODE == "master":
        # Start a new process for resource monitoring only if LOCUST_MODE is "master"
        resource_monitor_process = Process(target=compute_rescusage_csv, args=(config, completion_event))
        resource_monitor_process.start()

    # Get the result from the queue
    csv_path_output = get_csv_path() + '_usage.csv'
    print(f'Resource usage save at: {csv_path_output}')

    # Prepare the locust command and start it in a separate process
    command_process = Process(target=run_locust, args=(config, completion_event, csv_path_output))
    command_process.start()

    if LOCUST_MODE == "master":
        # Wait for both processes to finish before proceeding further
        resource_monitor_process.join()
    
    command_process.join()


if __name__ == "__main__":
    config = load_config('config.yaml')
    os.makedirs('reports', exist_ok=True)
    parallel_run_resc_and_locust(config)

