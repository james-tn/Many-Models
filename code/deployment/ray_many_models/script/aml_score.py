import json
# import numpy as np
# import pandas as pd
import mlflow
# Called when the service is loaded
# import time
import requests
from azure.identity import ManagedIdentityCredential 
from azure.ai.ml import MLClient

def init():
    # global ws, handle


    resource_group = "azureml"

    subscription_id = "0e9bace8-7a81-4922-83b5-d995ff706507"
    credential = ManagedIdentityCredential()
    workspace_name = "ws01ent"
    ml_client = MLClient(credential=credential,subscription_id=subscription_id,resource_group_name=resource_group, workspace_name=workspace_name)
    model_operations = ml_client.models
    print("return model" , model_operations.get("sklearn-iris", version=1))

def run(raw_data):
        # Get the input data 
    text_input = json.loads(raw_data)
    # output = ray.get(handle.remote(text_input))
    response = requests.post('http://many-models-serve-svc.default.svc.cluster.local:8000/', json=text_input)

    output = response.text
    return json.dumps({"result":output})
