from typing import Any, List

import attr
import deserialize  # type: ignore
import requests

from gdbt.provider.provider import EvaluationProvider, Provider

HTTP_TIMEOUT = 1.0


@deserialize.downcast_identifier(Provider, "prometheus")
@attr.s
class PrometheusProvider(EvaluationProvider):
    endpoint: str

    @property
    def client(self) -> None:
        return None

    def query(self, query: str) -> List[Any]:
        url = self.endpoint.rstrip("/") + "/api/v1/query"
        params = {"query": query}
        response = requests.get(url, params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        answer = response.json().get("data").get("result")
        return answer
