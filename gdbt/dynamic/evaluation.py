import abc
import json
import pathlib
import typing

import attr
import deserialize  # type: ignore

from gdbt.provider import EvaluationProvider


@deserialize.downcast_field("kind")
@attr.s
class Evaluation(abc.ABC):
    source: str = attr.ib()

    @abc.abstractmethod
    def evaluate(self, provider: EvaluationProvider) -> typing.Any:
        pass

    @property
    @abc.abstractmethod
    def hash(self) -> str:
        pass


@attr.s
class EvaluationLock:
    name: str = attr.ib()

    @property
    def path(self) -> pathlib.Path:
        return pathlib.Path(self.name).with_suffix(".lock")

    def load(
        self, name: str, hash: str
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        try:
            with open(self.path, "r") as f_lock:
                data = json.load(f_lock).get(name)
        except FileNotFoundError:
            return None
        if not data:
            return None
        if data["hash"] != hash:
            return None
        return data["data"]

    def dump(
        self,
        evaluations: typing.Mapping[str, typing.Any],
        hashes: typing.Mapping[str, str],
    ) -> None:
        data = {
            name: {"data": evaluations.get(name), "hash": hashes.get(name)}
            for name in evaluations.keys()
            if evaluations.get(name)
        }
        if not data:
            return
        with open(self.path, "w") as f_lock:
            json.dump(data, f_lock, sort_keys=True, indent=2, ensure_ascii=True)
