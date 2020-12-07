import json
import typing

import attr
import deserialize  # type: ignore

from gdbt.provider.provider import Provider, StateProvider
from gdbt.resource.resource import Resource
from gdbt.state.state import State


@deserialize.downcast_identifier(Provider, "file")
@attr.s
class FileProvider(StateProvider):
    path: str = attr.ib()

    def client(self):
        return None

    def read(self) -> str:
        with open(self.path, "r") as file:
            return file.read()

    def write(self, content: str) -> None:
        with open(self.path, "w") as file:
            file.write(content)

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
