import typing

import attr
import dpath.util  # type: ignore

import gdbt.errors
import gdbt.provider.provider


@attr.s
class Iterator:
    path: str = attr.ib()

    def iterable(
        self,
        providers: typing.Dict[str, gdbt.provider.provider.EvaluationProvider],
        evaluations: typing.Dict[str, typing.Any],
        lookups: typing.Dict[str, typing.Any],
    ) -> typing.Generator[typing.Any, None, None]:
        namespace = {
            "evaluations": evaluations,
            "lookups": lookups,
        }
        try:
            iterable = dpath.util.get(namespace, self.path, separator=".")
        except KeyError:
            raise gdbt.errors.VariableNotFound(self.path)
        try:
            for item in iterable:
                yield item
        except TypeError:
            raise gdbt.errors.VariableNotIterable(self.path)
