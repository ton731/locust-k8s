from locust import HttpUser, task, between
from locust import events, runners
from datetime import datetime
import time

from integration_test import load_config, compute_failure_csv, compute_exception_csv, create_charts_pdf, check_app_version, compute_final_report, remove_files_except_final_report, upload_pdf, merge_csv_files


@events.init_command_line_parser.add_listener
def init_parser(parser):
    parser.add_argument('--usage_csv', help="specify the path of usage csv")
    parser.add_argument('--start_time', help="specify the start time of locust")


@events.quitting.add_listener
def _(environment, **kw):
    if not isinstance(environment.runner, runners.MasterRunner):
        print("***** Locust worker, not responsible of handling the result...")
        time.sleep(10)
        return
    
    start_time_str = environment.parsed_options.start_time
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
    config_path = 'config.yaml'
    config = load_config(config_path)
    app_version = check_app_version(config)

    csv_paths = []
    csv_paths.append(merge_csv_files(environment.parsed_options.usage_csv, start_time))
    csv_paths.append(compute_failure_csv())
    csv_paths.append(compute_exception_csv())
    charts_pdf_path = create_charts_pdf()
    final_report_pdf = compute_final_report(csv_paths, app_version, charts_pdf_path, config)

    remove_files_except_final_report(final_report_pdf)
    gcs_path = upload_pdf(final_report_pdf, config_path, start_time)


class QuickstartUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def root(self):
        self.client.get("/")

    @task
    def predict(self):
        print("*** Start getting /predict endpoint")
        self.client.post("/predict", json={
            "text": "tonyyy",
        })

