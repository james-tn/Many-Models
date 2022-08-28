import ray
from ray import serve
from ray.serve.drivers import DAGDriver
from ray.serve.deployment_graph import InputNode
from ray.serve.http_adapters import json_request
import time
# These imports are used only for type hints:
from typing import Dict, List
from starlette.requests import Request
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy1:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy1:"+self.model_name +":" +message

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy2:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy2:"+self.model_name +":" +message
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy3:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy3: "+self.model_name +":" +message
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy4:
  # Take the message to return as an argument to the constructor.
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy4:"+self.model_name +":" +message
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy5:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy5:"+self.model_name +":" +message

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy6:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy6:"+self.model_name +":" +message

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy7:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy7:"+self.model_name +":" +message

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class TestDeploy8:
  def __init__(self):
      self.model_name = "model1"
      print("init ", self.model_name)
      time.sleep(1)
  def reconfigure(self, config: Dict):
      self.model_name = config.get("model_name")
  def message(self, message):
      time.sleep(1)
      return "TestDeploy8:"+self.model_name +":" +message
@serve.deployment(num_replicas=2, ray_actor_options={"num_cpus": 0.2, "num_gpus": 0})
class Dispatcher:
    def __init__(self, model1, model2, model3, model4, model5, model6, model7, model8):
        self.model1 = model1
        self.model2 = model2
        self.model3 = model3
        self.model4 = model4
        self.model5 = model5
        self.model6= model6
        self.model7 = model7
        self.model8 = model8

    async def process(self, message):
        if "1" in message:
            ref = await self.model1.message.remote(message)
        elif "2" in message: 
            ref= await self.model2.message.remote(message)
        elif "3" in message: 
            ref= await self.model3.message.remote(message)
        elif "4" in message: 
            ref= await self.model4.message.remote(message)
        elif "5" in message: 
            ref= await self.model5.message.remote(message)
        elif "6" in message: 
            ref= await self.model6.message.remote(message)
        elif "7" in message: 
            ref= await self.model7.message.remote(message)
        else: ref= await self.model8.message.remote(message)

        return await ref
async def json_resolver(request: Request) -> List:
    return await request.json()


with InputNode() as message:

    deployment1 = TestDeploy1.bind()
    deployment2 = TestDeploy2.bind()
    deployment3 = TestDeploy3.bind()
    deployment4 = TestDeploy4.bind()
    deployment5 = TestDeploy5.bind()
    deployment6 = TestDeploy6.bind()
    deployment7 = TestDeploy7.bind()
    deployment8 = TestDeploy8.bind()
    dispatcher = Dispatcher.bind(deployment1, deployment2,deployment3, deployment4,deployment5, deployment6,deployment7, deployment8)
    output_message = dispatcher.process(message)

deployment_graph = DAGDriver.bind(output_message, http_adapter=json_resolver)