import abc
import typing

import deserialize  # type: ignore

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
    def get(self) -> State:
        pass

    @abc.abstractmethod
    def put(
        self,
        state: State,
        providers: typing.Dict[str, Provider],
    ) -> None:
        pass
