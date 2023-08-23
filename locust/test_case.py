from locust import HttpUser, task, between
from locust import events, runners
import time

from integration_test import compute_failure_csv, compute_exception_csv


@events.quitting.add_listener
def _(environment, **kw):
    if not isinstance(environment.runner, runners.MasterRunner):
        print("***** Locust worker, not responsible of handling the result...")
        time.sleep(10)
        return
    
    csv_paths = []
    csv_paths.append(compute_failure_csv())
    csv_paths.append(compute_exception_csv())
    


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

