import os
import yaml
import time
import base64
from kubernetes import client, config


namespace_name = "stress-test"
config.load_kube_config()
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()


def create_namespace(namespace_name):
    namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
    try:
        core_v1.create_namespace(namespace)
        print(f"Namespace {namespace_name} created.")
    except client.rest.ApiException as e:
        print(f"Error creating namespace {namespace_name}: {e}")


def create_gcp_service_key(key_file_path, secret_name, namespace):
    with open(key_file_path, 'rb') as file:
            key_data = file.read()
        
    encoded_key_data = base64.b64encode(key_data).decode('utf-8')
    secret_metadata = client.V1ObjectMeta(name=secret_name, namespace=namespace)
    secret = client.V1Secret(data={"gcloud-service-key.json": encoded_key_data}, metadata=secret_metadata)
    
    try:
        core_v1.create_namespaced_secret(namespace=namespace, body=secret)
        print(f"Secret {secret_name} created in namespace {namespace}.")
    except client.rest.ApiException as e:
        print(f"Error creating secret {secret_name} in namespace {namespace}: {e}")
    
    return secret_name
    
    
def delete_namespace(namespace_name):
    try:
        core_v1.delete_namespace(name=namespace_name)
        print(f"Namespace {namespace_name} deleted.")
    except client.rest.ApiException as e:
        print(f"Error deleting namespace {namespace_name}: {e}")


def apply_from_file(yaml_path):
    with open(yaml_path, "r") as f:
        resource_yaml = f.read()
        resource = yaml.safe_load(resource_yaml)
        resource_kind = resource.get("kind")

        try:
            if resource_kind == "Deployment":
                apps_v1.create_namespaced_deployment(
                    namespace=namespace_name, body=resource
                )
            elif resource_kind == "Service":
                core_v1.create_namespaced_service(
                    namespace=namespace_name, body=resource
                )
            elif resource_kind == "Job":
                batch_v1.create_namespaced_job(
                    namespace=namespace_name, body=resource
                )
            print(f"Resource from {yaml_path} applied.")
            
        except client.rest.ApiException as e:
            print(f"Error applying resource from {yaml_path}: {e}")


def apply_from_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith((".yml", ".yaml")):
            yaml_path = os.path.join(folder_path, filename)
            apply_from_file(yaml_path)
                  
            
def delete_from_file(yaml_path):
    with open(yaml_path, "r") as f:
        resource_yaml = f.read()
        resource = yaml.safe_load(resource_yaml)
        resource_kind = resource.get("kind")
        resource_name = resource["metadata"]["name"]

        try:
            if resource_kind == "Deployment":
                apps_v1.delete_namespaced_deployment(
                    namespace=namespace_name, name=resource_name
                )
            elif resource_kind == "Service":
                core_v1.delete_namespaced_service(
                    namespace=namespace_name, name=resource_name
                )
            elif resource_kind == "Job":
                batch_v1.delete_namespaced_job(
                    namespace=namespace_name, name=resource_name
                )
            print(f"Resource from {yaml_path} deleted.")
            
        except client.rest.ApiException as e:
            print(f"Error deleting resource from {yaml_path}: {e}")


def delete_from_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith((".yml", ".yaml")):
            yaml_path = os.path.join(folder_path, filename)
            delete_from_file(yaml_path)            


def monitor_job_status(*job_names):
    while True:
        try:
            completed = []
            for job_name in job_names:
                job = batch_v1.read_namespaced_job_status(job_name, namespace_name)
                job_status = job.status

                if job_status.succeeded is not None and job_status.succeeded > 0:
                    completed.append(True)
                else:
                    completed.append(False)
            
            print("Status completed:", completed)
            if all(completed):
                break

        except client.rest.ApiException as e:
            print(f"Error reading Job status: {e}")

        time.sleep(10)  # Sleep for a few seconds before checking again




def main():
    # create the namespace
    create_namespace(namespace_name)

    # create the gcp service key in namespace
    create_gcp_service_key('sa-skyshih.json', 'gcp-service-key', namespace_name)
    
    # start the AI and Locust service
    apply_from_folder("ai-service")
    time.sleep(30)
    apply_from_folder("locust")
    
    # monitor the status of locust
    monitor_job_status("locust-master", "locust-worker")
    
    # delete the AI service
    delete_from_folder("ai-service")
    delete_from_folder("locust")
    
    # delete the namespace
    delete_namespace(namespace_name)
    



if __name__ == "__main__":
    main()
