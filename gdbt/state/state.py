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

    @classmethod
    def load(cls, source: str, providers: typing.Dict[str, typing.Any]) -> "State":
        try:
            provider = providers[source]
        except KeyError:
            raise gdbt.errors.ProviderNotFound(source)
        resources = provider.get()
        return cls(resources)

    def push(self, source: str, providers: typing.Dict[str, typing.Any]) -> None:
        try:
            provider = providers[source]
        except KeyError:
            raise gdbt.errors.ProviderNotFound(source)
        provider.put(self.resources, providers)
