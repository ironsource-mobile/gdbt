import typing

import attr

import gdbt.errors
import gdbt.resource.resource


@attr.s
class State:
    resources: typing.Dict[str, gdbt.resource.resource.Resource] = attr.ib()

    def serialize(
        self, providers: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        serialized = {
            name: resource.serialize(providers)
            for name, resource in self.resources.items()
        }
        return serialized


def load(source: str, providers: typing.Dict[str, typing.Any]) -> State:
    try:
        provider = providers[source]
    except KeyError:
        raise gdbt.errors.ProviderNotFound(source)
    state = provider.get()
    return state


def push(source: str, providers: typing.Dict[str, typing.Any], state: State) -> None:
    try:
        provider = providers[source]
    except KeyError:
        raise gdbt.errors.ProviderNotFound(source)
    provider.put(state, providers)
