import abc
import json
import typing

import attr
import deserialize  # type: ignore

import gdbt.provider.provider
import gdbt.resource.resource
import gdbt.templating.template
import gdbt.templating.evaluation
import gdbt.stencil.iterator


@deserialize.downcast_field("kind")
@attr.s(kw_only=True)
class Stencil(abc.ABC):
    kind: str = attr.ib()
    evaluations: typing.Optional[
        typing.Dict[str, gdbt.templating.evaluation.Evaluation]
    ] = attr.ib(default=typing.cast(typing.Optional[typing.Any], {}))
    lookups: typing.Optional[typing.Dict[str, typing.Any]] = attr.ib(
        default=typing.cast(typing.Optional[typing.Any], {})
    )


@attr.s(kw_only=True)
class ResourceStencil(Stencil):
    provider: str = attr.ib()
    loop: typing.Optional[str] = attr.ib()
    model: str = attr.ib()

    @abc.abstractmethod
    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
    ) -> gdbt.resource.resource.Resource:
        pass

    @abc.abstractmethod
    def name_to_uid(self, name: str, loop_item: typing.Any) -> str:
        pass

    def resolve_vars(
        self,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
        evaluations: typing.Dict[str, gdbt.templating.evaluation.Evaluation],
        lookups: typing.Dict[str, typing.Any],
    ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
        if not evaluations:
            evaluations = {}
        if not lookups:
            lookups = {}
        evaluations_resolved = {
            name: value.value(providers)
            for name, value in {
                **evaluations,
                **typing.cast(
                    typing.Dict[str, gdbt.templating.evaluation.Evaluation],
                    self.evaluations or {},
                ),
            }.items()
        }
        lookups_resolved = {
            name: value
            for name, value in {
                **lookups,
                **typing.cast(typing.Dict[str, typing.Any], self.lookups or {}),
            }.items()
        }
        return evaluations_resolved, lookups_resolved

    def resolve_loops(
        self,
        providers: typing.Dict[str, gdbt.provider.provider.EvaluationProvider],
        evaluations: typing.Dict[str, typing.Any],
        lookups: typing.Dict[str, typing.Any],
    ) -> typing.Generator[typing.Optional[str], None, None]:
        if not self.loop:
            yield None
            return
        iterator = gdbt.stencil.iterator.Iterator(typing.cast(str, self.loop)).iterable(
            providers, evaluations, lookups
        )
        for item in iterator:
            yield item

    def resolve(
        self,
        name: str,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
        evaluations: typing.Dict[str, gdbt.templating.evaluation.Evaluation],
        lookups: typing.Dict[str, typing.Any],
    ) -> typing.Dict[str, gdbt.resource.resource.Resource]:
        evaluations, lookups = self.resolve_vars(providers, evaluations, lookups)
        resources = {}
        for item in self.resolve_loops(
            typing.cast(
                typing.Dict[str, gdbt.provider.provider.EvaluationProvider], providers
            ),
            evaluations,
            lookups,
        ):
            uid = self.name_to_uid(name, item)
            model = gdbt.templating.template.Template(self.model).render(
                providers, evaluations, lookups, item
            )
            resource = self.make_resource(self.provider, uid, model, providers)
            resources.update({uid: resource})
        return resources


@deserialize.downcast_identifier(Stencil, "dashboard")
@attr.s(kw_only=True)
class Dashboard(ResourceStencil):
    folder: str = attr.ib()

    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
    ) -> gdbt.resource.resource.Dashboard:
        model_dict = json.loads(model)
        model_dict.pop("id", None)
        folder = self.folder if self.folder.startswith("folder_") else f"folder_{self.folder}"
        resource = gdbt.resource.resource.Dashboard(
            grafana=grafana,
            uid=uid,
            model=model_dict,
            folder=folder,
        )
        return resource

    def name_to_uid(self, name: str, loop_item: typing.Optional[typing.Any] = None) -> str:
        uid = "dashboard_" + name
        if loop_item:
            uid += "_" + str(loop_item)
        return uid


@deserialize.downcast_identifier(Stencil, "folder")
@attr.s(kw_only=True)
class Folder(ResourceStencil):
    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
    ) -> gdbt.resource.resource.Folder:
        model_dict = json.loads(model)
        resource = gdbt.resource.resource.Folder(
            grafana=grafana,
            uid=uid,
            model=model_dict,
        )
        return resource

    def name_to_uid(self, name: str, loop_item: typing.Optional[typing.Any] = None) -> str:
        uid = "folder_" + name
        if loop_item:
            uid += "_" + str(loop_item)
        return uid
