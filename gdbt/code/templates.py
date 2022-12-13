import abc
import hashlib
import json
import pathlib
import typing

import attr
import config
import deserialize  # type: ignore
import dpath.util  # type: ignore
import jinja2
import yaml

import gdbt.errors
from gdbt.code.configuration import Configuration, ConfigurationLoader
from gdbt.dynamic import Evaluation, EvaluationLock, Lookup
from gdbt.provider import EvaluationProvider
from gdbt.resource import Resource

TEMPLATE_VARIABLE_DELIMITER_LEFT = "{$"
TEMPLATE_VARIABLE_DELIMITER_RIGHT = "$}"


@deserialize.downcast_field("kind")
@attr.s(kw_only=True)
class Template(abc.ABC):
    kind: str = attr.ib()
    provider: str = attr.ib()
    evaluations: typing.Optional[typing.Dict[str, Evaluation]] = attr.ib(
        factory=typing.cast(typing.Any, dict)
    )
    lookups: typing.Optional[typing.Dict[str, Lookup]] = attr.ib(
        factory=typing.cast(typing.Any, dict)
    )
    loop: typing.Optional[str] = attr.ib()
    model: str = attr.ib()

    @abc.abstractmethod
    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
    ) -> Resource:
        pass

    def resolve_vars(
        self, configuration: Configuration, base: str, name: str, update: bool = False
    ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
        try:
            evaluations_resolved = {}
            lock = EvaluationLock(base, name)
            for evaluation_name, evaluation in (self.evaluations or {}).items():
                evaluation_source = typing.cast(
                    EvaluationProvider, configuration.providers[evaluation.source]
                )
                evaluation_hash = evaluation.hash
                evaluation_value = lock.load(evaluation_name, evaluation_hash)
                if evaluation_value is None or update:
                    evaluation_value = evaluation.evaluate(evaluation_source)
                    update = True
                evaluations_resolved.update({evaluation_name: evaluation_value})
            if update:
                lock.dump(
                    evaluations_resolved,
                    {k: v.hash for k, v in (self.evaluations or {}).items()},
                )
        except KeyError as exc:
            raise gdbt.errors.ProviderNotFound(str(exc)) from None
        lookups_resolved = {name: value for name, value in (self.lookups or {}).items()}
        return evaluations_resolved, lookups_resolved

    def resolve_loops(
        self,
        evaluations: typing.Dict[str, Evaluation],
        lookups: typing.Dict[str, Lookup],
    ) -> typing.Generator[typing.Optional[str], None, None]:
        if not self.loop:
            yield None
            return
        iterator = Iterator(typing.cast(str, self.loop)).iterable(evaluations, lookups)
        for item in iterator:
            yield item

    def resolve(
        self,
        name: str,
        configuration: Configuration,
        base: str,
        update: bool,
    ) -> typing.Dict[str, Resource]:
        evaluations, lookups = self.resolve_vars(configuration, base, name, update)
        resources = {}
        for item in self.resolve_loops(evaluations, lookups):
            resource_name = name
            if item:
                resource_name += f":{item}"
            uid = self.format_uid(resource_name)
            model = Model(self.model).render(evaluations, lookups, configuration, item)
            resource = self.make_resource(self.provider, uid, model)
            resources.update({resource_name: resource})
        return resources

    def format_uid(self, name: str) -> str:
        uid_hash = hashlib.md5()
        uid_hash.update(name.encode())
        uid = "gdbt_" + uid_hash.hexdigest()
        return uid


@deserialize.downcast_identifier(Template, "dashboard")
@attr.s(kw_only=True)
class Dashboard(Template):
    folder: str = attr.ib()

    kind = "dashboard"

    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
    ) -> gdbt.resource.resource.Dashboard:
        try:
            model_dict = json.loads(model)
        except json.JSONDecodeError as e:
            with open('/tmp/invalid_json', 'w') as f:
                f.write(model + '\n')
            print(model + '\n')
            print('Error: Invalid JSON: %s. Generated invalid JSON can be viewed in /tmp/invalid_json and was '
                  'printed above this error message.' % e)
            raise
        model_dict.pop("id", None)
        folder_uid = self.format_uid(self.folder)
        resource = gdbt.resource.resource.Dashboard(
            grafana=grafana,
            uid=uid,
            model=model_dict,
            folder=folder_uid,
        )
        return resource


@deserialize.downcast_identifier(Template, "folder")
@attr.s(kw_only=True)
class Folder(Template):
    kind = "folder"

    def make_resource(
        self,
        grafana: str,
        uid: str,
        model: str,
    ) -> gdbt.resource.resource.Folder:
        model_dict = json.loads(model)
        resource = gdbt.resource.resource.Folder(
            grafana=grafana,
            uid=uid,
            model=model_dict,
        )
        return resource


@attr.s
class Model:
    template: str = attr.ib()

    def render(
        self,
        evaluations: typing.Dict[str, Evaluation],
        lookups: typing.Dict[str, Lookup],
        configuration: Configuration,
        loop_item: typing.Optional[typing.Any] = None,
    ) -> str:
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            variable_start_string=TEMPLATE_VARIABLE_DELIMITER_LEFT,
            variable_end_string=TEMPLATE_VARIABLE_DELIMITER_RIGHT,
        )
        template = env.from_string(self.template)
        rendered = template.render(
            providers=configuration.providers,
            evaluations=evaluations,
            lookups=lookups,
            loop=dict(item=loop_item),
        )
        return rendered


@attr.s
class Iterator:
    path: str = attr.ib()

    def iterable(
        self,
        evaluations: typing.Dict[str, Evaluation],
        lookups: typing.Dict[str, Lookup],
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


@attr.s
class TemplateLoader:
    path: pathlib.Path = attr.ib(factory=pathlib.Path)

    @property
    def base_path(self) -> pathlib.Path:
        try:
            configuration_loader = ConfigurationLoader(self.path)
            base_path = list(configuration_loader.list_files(self.path))[-1].parent
            return base_path
        except IndexError:
            raise gdbt.errors.ConfigFileNotFound

    @staticmethod
    def list_files(path: pathlib.Path) -> typing.Generator[pathlib.Path, None, None]:
        path = path.expanduser().resolve()
        files = path.glob("**/*.yaml")
        return files

    @staticmethod
    def tag_files(
        files: typing.Iterable[pathlib.Path], base_path: pathlib.Path
    ) -> typing.Dict[str, pathlib.Path]:
        files_tagged: typing.Dict[str, pathlib.Path] = {}
        for file in files:
            file_tag = str(file.relative_to(base_path).with_suffix(""))
            files_tagged.update({file_tag: file})
        return files_tagged

    @staticmethod
    def load_files(
        files: typing.Dict[str, pathlib.Path]
    ) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        files_data: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for file_tag, file in files.items():
            file_data = config.config_from_yaml(
                str(file), read_from_file=True
            ).as_attrdict()
            files_data.update({file_tag: file_data})
        return files_data

    def deserialize(self) -> typing.Dict[str, Template]:
        try:
            templates: typing.Dict[str, Template] = {}
            template_files = self.tag_files(self.list_files(self.path), self.base_path)
            templates_data = self.load_files(template_files)
            for template_tag, template_data in templates_data.items():
                template = deserialize.deserialize(Template, template_data)
                templates.update({template_tag: template})
        except (
            TypeError,
            yaml.YAMLError,
            deserialize.DeserializeException,
        ) as exc:
            raise gdbt.errors.ConfigFormatInvalid(str(exc))
        return templates


def load(
    path: typing.Optional[typing.Union[pathlib.Path, str]] = None
) -> typing.Dict[str, Template]:
    if not path:
        path = pathlib.Path(".")
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(typing.cast(str, path))
    templates = TemplateLoader(path).deserialize()
    return templates
