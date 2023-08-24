# How to run stress test with Locust in Kubernetes?


## 1. Automatically
The script will create a namespace and run the AI and Locust service. Once the status of locust master & worker become `complete`, the script will turn off the services and delete the namespace to set the Kubernetes cluster back to the original condition.
```python
python master-script.py
```

---
## 2. Manually

### Start the stress test
- Create a namespace in K8s cluster.
    - `kubectl create namespace stress-test`
- Create gcp-service-key under namespace
    - `kubectl create secret generic gcp-service-key --from-file=gcloud-service-key.json=<path_to_gcloud-service-key.json> -n stress-test`
- Start the fake AI service.
    - `kubectl apply -f ai-service`
- Start the Locust master and worker.
    - `kubectl apply -f locust`


### Debugging
- Get the target pod names.
    - `kubectl get pod -n stress-test`
- Print the logs of the pod.
    - `kubectl logs -n stress-test <pod-name>`
- Get into the pod environment.
    - `kubectl exec -it -n stress-test <pod-name> -- /bin/bash`


### Remove the services
- Remove the fake AI service.
    - `kubectl delete -f ai-service`
- Remove the Locust master and worker.
    - `kubectl delete -f locust`
- Delete the namespace.
    - `kubectl delete namespace stress-test`


### Current status
- Locust master and workers will stop once the time is up, and the pod will stop. However, in order to keep 1 replica alive, K8s will restart the deployments, making the locust keep starting and stopping. So we have to come up with some method to run the stress test exactly once and then close the Locust and AI service.


