import ray
from ray import serve
from ray.serve.drivers import DAGDriver
from ray.serve.deployment_graph import InputNode
from typing import Dict, List
from starlette.requests import Request
from ray.serve.deployment_graph import ClassNode
from azureml.core.model import Model
from azureml.core import Workspace
from azureml.core.authentication import ServicePrincipalAuthentication
import time
import sklearn
import joblib
import os


def download_model():
    tenant_id = os.getenv('TENANT_ID')
    subscription_id =os.getenv('SUBSCRIPTION_ID')
    resource_group = os.getenv('RESOURCE_GROUP')
    workspace_name = os.getenv('WORKSPACE_NAME')
    service_principal_id = os.getenv('SERVICE_PRINCIPAL_ID')
    service_principal_password =  os.getenv('SERVICE_PRINCIPAL_PASSWORD')
    sp = ServicePrincipalAuthentication(tenant_id=tenant_id, 
                                        service_principal_id=service_principal_id, 
                                        service_principal_password=service_principal_password) 
    ws = Workspace(subscription_id=subscription_id,
                    resource_group=resource_group,
                    workspace_name=workspace_name,
                auth=sp)
    model = Model(ws,"sklearn-iris")
    model.download(exist_ok=True)
    
@serve.deployment(num_replicas=1)
class Deployment1:
    def __init__(self):
        self.model_name= "default"

    def reconfigure(self, config: Dict):
        self.model_name = config.get("tenant","default")
        download_model()
        self.model = joblib.load("model.joblib")

    def predict(self, data):
        return {"deployment": self.__class__.__name__,"model": self.model_name, "prediction":self.model.predict(data)}
@serve.deployment(num_replicas=1)
class Deployment2:
    def __init__(self):
        self.model_name= "default"


    def reconfigure(self, config: Dict):
        self.model_name = config.get("tenant","default")
        download_model()
        self.model = joblib.load("model.joblib")

    def predict(self, data):
        return {"deployment": self.__class__.__name__,"model": self.model_name, "prediction":self.model.predict(data)}

@serve.deployment(num_replicas=2)
class Dispatcher:
    # def __init__(self, model1, model2, model3, model4, model5, model6, model7, model8):
    def __init__(self, deployment1: ClassNode, deployment2: ClassNode):

        self.deployment1 = deployment1
        self.deployment2 = deployment2
        self.tenant_map = {"tenant1":self.deployment1, "tenant2":self.deployment2}
        self.default_deployment = deployment1
    # def reconfigure(self, config: Dict):
    #     self.tenant_map = config

    def process(self, raw_input):
        tenant = raw_input.get('tenant')
        data = raw_input.get("data")
        deployment = self.tenant_map.get(tenant, self.default_deployment)
        result = ray.get(deployment.predict.remote(data))
        return result
async def json_resolver(request: Request) -> List:
    return await request.json()


with InputNode() as message:
    # message, amount = query[0], query[1]
    deployment1 = Deployment1.bind()
    deployment2 = Deployment2.bind()
    dispatcher = Dispatcher.bind(deployment1, deployment2)
    output_message = dispatcher.process.bind(message)

deployment_graph = DAGDriver.bind(output_message, http_adapter=json_resolver)