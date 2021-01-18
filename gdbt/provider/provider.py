import abc
import json
import pathlib
import typing

import attr
import deserialize  # type: ignore

import gdbt.errors


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


@attr.s(kw_only=True)
class StateProvider(Provider):
    path: typing.Optional[str] = attr.ib(factory=str)
    _object_extension: typing.Optional[str] = attr.ib(init=False, default=".json")

    @abc.abstractmethod
    def _list(self, path: pathlib.Path) -> typing.Iterable[pathlib.Path]:
        pass

    @abc.abstractmethod
    def _get(self, path: pathlib.Path) -> str:
        pass

    @abc.abstractmethod
    def _put(self, path: pathlib.Path, content: str) -> None:
        pass

    @abc.abstractmethod
    def _remove(self, path: pathlib.Path) -> None:
        pass

    @abc.abstractmethod
    def _lock(self, path: pathlib.Path) -> None:
        pass

    @abc.abstractmethod
    def _unlock(self, path: pathlib.Path) -> None:
        pass

    @property
    @abc.abstractmethod
    def _base_path(self) -> pathlib.Path:
        pass

    def _resolve_path(
        self, path_relative_string: str, folder: bool = False
    ) -> pathlib.Path:
        path_string_stripped = path_relative_string.lstrip("/").strip()
        path_relative = pathlib.Path(path_string_stripped)
        path_base = self._base_path
        if self._object_extension and not folder:
            path_relative = path_relative.with_suffix(self._object_extension)
        path = path_base / path_relative
        return path

    def list(self, subdirectory: str = ".") -> typing.List[str]:
        # path = self._resolve_path(subdirectory, folder=True)
        path = pathlib.Path(subdirectory)
        try:
            files = list(map(str, self._list(path)))
        except json.JSONDecodeError as exc:
            raise gdbt.errors.StateCorrupted(str(exc))
        return files

    def get(self, name: str) -> typing.Dict[str, typing.Any]:
        path = self._resolve_path(name)
        try:
            state = json.loads(self._get(path))
        except json.JSONDecodeError as exc:
            raise gdbt.errors.StateCorrupted(str(exc))
        return state

    def put(
        self,
        name: str,
        state: typing.Dict[str, typing.Any],
    ) -> None:
        path = self._resolve_path(name)
        data = json.dumps(state, indent=2, sort_keys=True)
        self._put(path, data)

    def remove(self, name: str) -> None:
        path = self._resolve_path(name)
        self._remove(path)
