import json
import typing
import urllib.parse

import attr
import consul  # type: ignore
import deserialize  # type: ignore

import gdbt.errors
from gdbt.provider.provider import Provider, StateProvider
from gdbt.resource.resource import Resource
from gdbt.state.state import State


@deserialize.downcast_identifier(Provider, "consul")
@attr.s
class ConsulProvider(StateProvider):
    endpoint: str = attr.ib()
    path: str = attr.ib()
    token: typing.Optional[str] = attr.ib()
    datacenter: typing.Optional[str] = attr.ib()

    def client(self):
        endpoint = urllib.parse.urlparse(self.endpoint)
        port = endpoint.port or {"http": 80, "https": 443}.get(endpoint.scheme, None)
        client = consul.Consul(
            host=endpoint.hostname,
            port=port,
            scheme=endpoint.scheme,
            token=self.token,
            dc=self.datacenter,
        )
        return client

    def read(self) -> str:
        client = self.client()
        try:
            _, document = client.kv.get(self.path)
            content = document["Value"].decode("utf-8")
            return content
        except (KeyError, TypeError, consul.ConsulException):
            raise gdbt.errors.ConsulKeyNotFoundError(self.path)
        except consul.ConsulException as exc:
            raise gdbt.errors.ConsulError(str(exc))

    def write(self, content: str) -> None:
        client = self.client()
        try:
            client.kv.put(self.path, content)
        except consul.ConsulException as exc:
            raise gdbt.errors.ConsulError(str(exc))

    def get(self) -> State:
        resources_dict = json.loads(self.read())
        resources = {
            name: deserialize.deserialize(Resource, resource)
            for name, resource in resources_dict.items()
        }
        return State(resources)

    def put(
        self,
        state: State,
        providers: typing.Dict[str, Provider],
    ) -> None:
        resources_dict = {
            name: resource.serialize(providers)
            for name, resource in state.resources.items()
        }
        self.write(json.dumps(resources_dict, indent=2, sort_keys=True))
