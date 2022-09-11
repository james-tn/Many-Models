from turtle import update
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
import threading, queue
from collections import deque
tenant_id = os.getenv('TENANT_ID')
subscription_id =os.getenv('SUBSCRIPTION_ID')
resource_group = os.getenv('RESOURCE_GROUP')
workspace_name = os.getenv('WORKSPACE_NAME')
service_principal_id = os.getenv('SERVICE_PRINCIPAL_ID')
service_principal_password =  os.getenv('SERVICE_PRINCIPAL_PASSWORD')

def download_model(model_name, ws):
    if  os.path.exists(model_name):
        return
    os.makedirs(model_name, exist_ok=True)
    model = Model(ws,"sklearn-iris")
    model.download(target_dir=model_name,exist_ok=True)
#repsenting a deployment scoring. Assumption is model name = tenant name for simpicity.
class Deployment:
    def __init__(self):
        self.model_name= "default"
        sp = ServicePrincipalAuthentication(tenant_id=tenant_id, 
                                            service_principal_id=service_principal_id, 
                                            service_principal_password=service_principal_password) 
        self.ws = Workspace(subscription_id=subscription_id,
                        resource_group=resource_group,
                        workspace_name=workspace_name,
                    auth=sp)

    def reconfigure(self, config: Dict):
        model_name = config.get("tenant","default")
        download_model(model_name, self.ws)
        self.model = joblib.load(os.path.join(model_name, "model.joblib"))
        self.model_name = model_name

    def predict(self, data,model_name):
        #if model name is equal to deploy's configured model name, the model is already loaded
        if model_name == self.model_name:
            return {"deployment": self.__class__.__name__,"model": model_name, "prediction":self.model.predict(data)}
        else:
            download_model(model_name, self.ws)
            self.model = joblib.load(os.path.join(model_name, "model.joblib"))
            time.sleep(0.5) # adding more latency to simulate loading large model
            return {"deployment": self.__class__.__name__,"model": model_name, "prediction":self.model.predict(data)}
@serve.deployment(num_replicas=1)
class Deployment1(Deployment):
    pass
@serve.deployment(num_replicas=1)
class Deployment2(Deployment):
    pass
@serve.deployment(num_replicas=1)
class Deployment3(Deployment):
    pass
@serve.deployment(num_replicas=1)
class Deploymentx(Deployment):
    pass
#serve as shared memory object for tenant map and tenant queue
@serve.deployment(num_replicas=1)
class SharedMemory:
    def __init__(self):
        self.tenant_map = {"tenant1":"deployment1", "tenant2":"deployment2","tenant3":"deployment3"}
        self.tenant_queue = deque(maxlen=3)
        self.tenant_queue.append("tenant1")
        self.tenant_queue.append("tenant2")
        self.tenant_queue.append("tenant3")
    def tenant_queue_remove(self, item):
        self.tenant_queue.remove(item)
    def tenant_queue_append(self, item):
        self.tenant_queue.append(item)
    def tenant_queue_popleft(self):
        return self.tenant_queue.popleft()
    def tenant_map_pop(self, item):
        return self.tenant_map.pop(item)
    def set_tenant_map(self, tenant, deployment_name):
        self.tenant_map[tenant]=deployment_name
    def get_tenant_map(self, tenant):
        return self.tenant_map.get(tenant, "default")
@serve.deployment(num_replicas=2)
class Dispatcher:
    def __init__(self, deployment1: ClassNode, deployment2: ClassNode, deployment3: ClassNode, deploymentx: ClassNode,sharedmemory: ClassNode):
        self.deployment_map = {"deployment1":deployment1, "deployment2":deployment2,"deployment3":deployment3, "default":deploymentx}
        self.sharedmemory = sharedmemory

        self.q = queue.Queue()
        threading.Thread(target=self.append, daemon=True).start()

    def append(self):

        while True:
            new_item = self.q.get()
        
            if new_item in self.tenant_queue:
                #the tenant is already in the queue, just move it up to higher priority
                ray.get(self.sharedmemory.tenant_queue_remove.remote(new_item))
                ray(self.sharedmemory.tenant_queue_append.remote(new_item))
            else: #if this tenant is not yet in the hot queue
                #  kick out old tenant
                out_item = ray.get(self.sharedmemory.tenant_queue_popleft.remote())
                ray.get(self.sharedmemory.tenant_queue_append.remote(new_item))
                # update mapping table to route traffic of out_item to cold scoring
                current_deployment_name = ray.get(self.sharedmemory.tenant_map_pop.remote(out_item))
                current_deployment = self.deployment_map.get(current_deployment_name)
                # promote the new_item's deployment to hot
                ray.get(current_deployment.reconfigure.remote({"tenant":new_item}))
                #update mapping 
                ray.get(self.sharedmemory.set_tenant_map.remote(new_item,current_deployment_name))

        

    def process(self, raw_input):
        #assuming model name is same with tenant
        tenant = raw_input.get('tenant')
        # threading.Thread(target=self.append, daemon=True, args=(tenant)).start()
        data = raw_input.get("data")
        deployment_name = ray.get(self.sharedmemory.get_tenant_map.remote(tenant))
        deployment= self.deployment_map.get(deployment_name)
        result = ray.get(deployment.predict.remote(data, tenant))
        self.q.put(tenant)

        return result
async def json_resolver(request: Request) -> List:
    return await request.json()


with InputNode() as message:
    # message, amount = query[0], query[1]
    deployment1 = Deployment1.bind()
    deployment2 = Deployment2.bind()
    deployment3 = Deployment3.bind()
    deploymentx = Deploymentx.bind()
    sharedmemory = SharedMemory.bind()
    dispatcher = Dispatcher.bind(deployment1, deployment2,deployment3,deploymentx,sharedmemory)
    output_message = dispatcher.process.bind(message)

deployment_graph = DAGDriver.bind(output_message, http_adapter=json_resolver)