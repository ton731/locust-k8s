from locust import HttpUser, task, between
import logging
from locust import events


@events.quitting.add_listener
def _(environment, **kw):
    print("***** Uploading results to GCS...")


class QuickstartUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def root(self):
        self.client.get("/")

