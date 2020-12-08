import abc
import typing

import attr
import deserialize  # type: ignore
import jsonpath_ng  # type: ignore

import gdbt.errors
import gdbt.provider.provider


@deserialize.downcast_field("kind")
@attr.s
class Evaluation(abc.ABC):
    source: str = attr.ib()

    def value(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> typing.Any:
        try:
            provider = providers[self.source]
        except KeyError:
            raise gdbt.errors.ProviderNotFound(self.source) from None
        return self.evaluate(
            typing.cast(gdbt.provider.provider.EvaluationProvider, provider)
        )

    @abc.abstractmethod
    def evaluate(
        self, provider: gdbt.provider.provider.EvaluationProvider
    ) -> typing.Any:
        pass


@deserialize.downcast_identifier(Evaluation, "prometheus")
@attr.s
class PrometheusEvaluation(Evaluation):
    metric: str = attr.ib()
    label: str = attr.ib()

    def evaluate(
        self, provider: gdbt.provider.provider.EvaluationProvider
    ) -> typing.Any:
        filter = jsonpath_ng.parse(f"$[*].metric.{self.label}")
        metric_values = provider.query(self.metric)
        values = [item.value for item in filter.find(metric_values)]
        return values
