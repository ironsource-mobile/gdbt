import typing
import urllib.parse

import attr
import deserialize  # type: ignore
import grafana_api.grafana_api  # type: ignore
import grafana_api.grafana_face  # type: ignore

from gdbt.provider.provider import Provider


@deserialize.downcast_identifier(Provider, "grafana")
@attr.s
class GrafanaProvider(Provider):
    endpoint: str = attr.ib()
    token: typing.Optional[str] = attr.ib()

    @property
    def client(self) -> grafana_api.grafana_face.GrafanaFace:
        endpoint = urllib.parse.urlparse(self.endpoint)
        port = endpoint.port or {"http": 80, "https": 443}.get(endpoint.scheme, None)
        client = grafana_api.grafana_face.GrafanaFace(
            host=endpoint.hostname,
            port=port,
            protocol=endpoint.scheme,
            auth=self.token,
        )
        return client
