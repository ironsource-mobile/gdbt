import typing
import urllib.parse

import attr
import consul  # type: ignore
import deserialize  # type: ignore

import gdbt.errors
from gdbt.provider.provider import Provider, StateProvider


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

    def _read(self) -> str:
        client = self.client()
        try:
            _, document = client.kv.get(self.path)
            content = document["Value"].decode("utf-8")
            return content
        except (KeyError, TypeError, consul.ConsulException):
            raise gdbt.errors.ConsulKeyNotFound(self.path)
        except consul.ConsulException as exc:
            raise gdbt.errors.ConsulError(str(exc))

    def _write(self, content: str) -> None:
        client = self.client()
        try:
            client.kv.put(self.path, content)
        except consul.ConsulException as exc:
            raise gdbt.errors.ConsulError(str(exc))

    def lock(self):
        pass

    def unlock(self):
        pass
