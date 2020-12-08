import abc
import json
import typing

import deserialize  # type: ignore

import gdbt.errors
from gdbt.resource.resource import Resource
from gdbt.state.state import State


@deserialize.downcast_field("kind")
class Provider(abc.ABC):
    @property
    @abc.abstractmethod
    def client(self):
        pass


class EvaluationProvider(Provider):
    @abc.abstractmethod
    def query(self, query: str) -> typing.List[typing.Any]:
        pass


class StateProvider(Provider):
    @abc.abstractmethod
    def _read(self) -> str:
        pass

    @abc.abstractmethod
    def _write(self, content: str) -> None:
        pass

    def get(self) -> State:
        try:
            resources_dict = json.loads(self._read())
            resources = {
                name: deserialize.deserialize(Resource, resource)
                for name, resource in resources_dict.items()
            }
        except (json.JSONDecodeError, deserialize.DeserializeException) as exc:
            raise gdbt.errors.StateFormatInvalid(str(exc))
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
        self._write(json.dumps(resources_dict, indent=2, sort_keys=True))
