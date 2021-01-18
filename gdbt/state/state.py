import concurrent.futures
import pathlib
import typing

import attr

import gdbt.errors
from gdbt.code import Configuration
from gdbt.provider import StateProvider
from gdbt.resource import ResourceGroup, ResourceGroupMeta, ResourceMeta

STATE_VERSION = 2


@attr.s
class State:
    resource_meta: ResourceGroupMeta = attr.ib()
    grafana: str = attr.ib(factory=str)
    kind: str = attr.ib(factory=str)
    state_version: int = attr.ib(default=STATE_VERSION)

    @state_version.validator
    def _validate_state_version(self, _, version: int) -> None:
        if version != STATE_VERSION:
            raise gdbt.errors.StateVersionIncompatible(str(version))

    @classmethod
    def pull(cls, name: str, provider: StateProvider) -> "State":
        state_data = provider.get(name)
        if not state_data:
            return cls(typing.cast(ResourceGroupMeta, {}))
        try:
            state = cls(**state_data)
            return state
        except TypeError as exc:
            raise gdbt.errors.StateCorrupted(str(exc))

    def push(
        self,
        name: str,
        provider: StateProvider,
    ) -> None:
        self.state_version = STATE_VERSION
        provider.put(name, self.serialized)

    def remove(self, name: str, provider: StateProvider) -> None:
        provider.remove(name)

    @property
    def serialized(self) -> typing.Dict[str, typing.Any]:
        data = {
            "grafana": self.grafana,
            "kind": self.kind,
            "resource_meta": self.resource_meta,
            "state_version": self.state_version,
        }
        return data


@attr.s
class StateLoader:
    configuration: Configuration = attr.ib()

    @property
    def provider(self) -> StateProvider:
        provider_list = self.configuration.providers
        try:
            provider = provider_list[self.configuration.state.provider]
            return typing.cast(StateProvider, provider)
        except AttributeError:
            raise gdbt.errors.ConfigError("Missing state.provider value")
        except KeyError:
            raise gdbt.errors.ProviderNotFound(self.configuration.state.provider)

    def load(
        self, path: typing.Optional[pathlib.Path] = None
    ) -> typing.Dict[str, State]:
        if not path:
            path = pathlib.Path(".")
        threads = self.configuration.concurrency.threads
        pool = concurrent.futures.ThreadPoolExecutor(threads)
        state_list = self.provider.list(str(path))
        states = {}
        state_futures = {}
        for state_name in state_list:
            state_future = pool.submit(State.pull, state_name, self.provider)
            state_futures.update({state_name: state_future})
        concurrent.futures.wait(
            state_futures.values(), timeout=self.configuration.concurrency.timeout
        )
        for state_name in state_list:
            state_future = state_futures[state_name]
            if state_future.exception() is not None:
                raise state_future.exception()  # type: ignore
            states.update({state_name: state_future.result()})
        return states

    def upload(
        self, path: pathlib.Path, resources: typing.Mapping[str, ResourceGroup]
    ) -> None:
        threads = self.configuration.concurrency.threads
        pool = concurrent.futures.ThreadPoolExecutor(threads)
        state_futures = []
        for group_name, group_resources in resources.items():
            if not group_resources:
                state = State(typing.cast(ResourceGroupMeta, {}))
                state_future = pool.submit(state.remove, group_name, self.provider)
                state_futures.append(state_future)
                continue
            group_meta: ResourceGroupMeta = typing.cast(ResourceGroupMeta, {})
            grafana = list(group_resources.values())[0].grafana
            kind = list(group_resources.values())[0]._kind
            for resource_name, resource in group_resources.items():
                resource_meta = typing.cast(
                    ResourceMeta,
                    {
                        "uid": resource.uid,
                        "grafana": resource.grafana,
                        "kind": resource._kind,
                    },
                )
                group_meta.update({resource_name: resource_meta})
            state = State(group_meta, grafana, kind)
            state_future = pool.submit(state.push, group_name, self.provider)
            state_futures.append(state_future)
        results = concurrent.futures.wait(
            state_futures, timeout=self.configuration.concurrency.timeout
        )
        for result in results[0]:
            if result.exception() is not None:
                raise result.exception()  # type: ignore
