from locust import HttpUser, task, between
from locust import events, runners
import time


@events.quitting.add_listener
def _(environment, **kw):
    if not isinstance(environment.runner, runners.MasterRunner):
        print("***** Locust worker, not responsible of handling the result...")
        time.sleep(10)
        return
    
    print("***** Uploading results to GCS...")
    


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

