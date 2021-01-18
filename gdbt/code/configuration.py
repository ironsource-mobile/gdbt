"""Configuration module.

TODO:
    - docstrings
    - see TODOs
"""

import pathlib
import typing

import attr
import config
import deserialize  # type: ignore
import envtoml  # type: ignore

import gdbt.errors
from gdbt.provider import Provider

CONFIG_FILENAME = "config.toml"


@attr.s
class Configuration:
    providers: typing.Dict[str, Provider] = attr.ib()
    state: "StateConfiguration" = attr.ib()
    concurrency: "ConcurrencyConfiguration" = attr.ib()


@attr.s
class StateConfiguration:
    provider: str = attr.ib()
    lock_timeout: typing.Optional[typing.Union[int, float]] = attr.ib()


@deserialize.default("threads", 100)
@deserialize.default("timeout", 60.0)
@attr.s
class ConcurrencyConfiguration:
    threads: typing.Optional[int] = attr.ib(default=100)
    timeout: typing.Optional[float] = attr.ib(default=60.0)


@attr.s
class ConfigurationLoader:
    path: pathlib.Path = attr.ib(factory=pathlib.Path)

    @staticmethod
    def list_files(path: pathlib.Path) -> typing.Generator[pathlib.Path, None, None]:
        path = path.expanduser().resolve()
        for dir in [path, *path.parents]:
            config_path = dir / CONFIG_FILENAME
            if config_path.is_file():
                yield config_path

    @staticmethod
    def resolve_env(
        files: typing.Iterable[pathlib.Path],
    ) -> typing.Generator[typing.Dict[str, typing.Any], None, None]:
        for file in files:
            yield envtoml.load(file)

    @staticmethod
    def merge_configurations(
        configs: typing.Iterable[typing.Dict[str, typing.Any]]
    ) -> config.configuration_set.ConfigurationSet:
        if not configs:
            raise gdbt.errors.ConfigEmpty
        configuration = config.config(*configs)
        return configuration

    def deserialize(self) -> Configuration:
        try:
            configuration_data = self.merge_configurations(
                self.resolve_env(self.list_files(self.path))
            )
            configuration = deserialize.deserialize(
                Configuration, configuration_data.as_attrdict()
            )
        except (
            TypeError,
            envtoml.toml.TomlDecodeError,
            deserialize.DeserializeException,
        ) as exc:
            raise gdbt.errors.ConfigFormatInvalid(str(exc))
        return configuration


def load(
    path: typing.Optional[typing.Union[pathlib.Path, str]] = None
) -> Configuration:
    if not path:
        path = pathlib.Path(".")
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(typing.cast(str, path))
    configuration = ConfigurationLoader(path).deserialize()
    return configuration
