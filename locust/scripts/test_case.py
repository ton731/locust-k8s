from locust import HttpUser, task, between
from locust import events, runners
from datetime import datetime
import time

from integration_test import load_config, compute_failure_csv, compute_exception_csv, create_charts_pdf, check_app_version, compute_final_report, remove_files_except_final_report, upload_pdf


@events.quitting.add_listener
def _(environment, **kw):
    if not isinstance(environment.runner, runners.MasterRunner):
        print("***** Locust worker, not responsible of handling the result...")
        time.sleep(10)
        return
    
    start_time = datetime.now()
    config_path = 'config.yaml'
    config = load_config(config_path)
    app_version = check_app_version(config)

    csv_paths = []
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

