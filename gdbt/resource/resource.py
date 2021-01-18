import abc
import concurrent.futures
import typing

import attr
import backoff  # type: ignore
import deserialize  # type: ignore
import grafana_api.grafana_api  # type: ignore

import gdbt.errors
from gdbt.code import Configuration

IGNORED_KEYS = ("id", "uid", "version")

ResourceGroup = typing.NewType("ResourceGroup", typing.Dict[str, "Resource"])
ResourceMeta = typing.NewType("ResourceMeta", typing.Dict[str, str])
ResourceGroupMeta = typing.NewType("ResourceGroupMeta", typing.Dict[str, ResourceMeta])


@deserialize.downcast_field("kind")
@attr.s
class Resource(abc.ABC):
    grafana: str = attr.ib()
    uid: str = attr.ib()
    model: typing.Dict[str, typing.Any] = attr.ib()

    @abc.abstractclassmethod
    def create(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> "Resource":
        pass

    @abc.abstractclassmethod
    def get(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> "Resource":
        pass

    @abc.abstractclassmethod
    def exists(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> bool:
        pass

    @abc.abstractmethod
    def id(self, configuration: Configuration) -> int:
        pass

    @abc.abstractmethod
    def update(
        self,
        model: typing.Dict[str, typing.Any],
        configuration: Configuration,
    ) -> "Resource":
        pass

    @abc.abstractmethod
    def delete(self, configuration: Configuration) -> None:
        pass

    @property
    @abc.abstractmethod
    def serialized(self) -> typing.Dict[str, typing.Any]:
        pass

    @property
    def _kind(self) -> str:
        return type(self).__name__.lower()

    @staticmethod
    def client(grafana: str, configuration: Configuration) -> typing.Any:
        try:
            provider = configuration.providers[grafana]
        except KeyError:
            raise gdbt.errors.ProviderNotFound(grafana)
        return provider

    @classmethod
    def _model_strip(
        cls, model: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        model_stripped = model.copy()
        for field in IGNORED_KEYS:
            try:
                del model_stripped[field]
            except KeyError:
                pass
        return model_stripped


@deserialize.downcast_identifier(Resource, "folder")
class Folder(Resource):
    @classmethod
    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def create(  # type: ignore
        cls,
        grafana: str,
        uid: str,
        model: typing.Dict[str, typing.Any],
        configuration: Configuration,
    ) -> "Folder":
        try:
            model_stripped = cls._model_strip(model)
            title = model_stripped["title"]
            cls.client(grafana, configuration).client.folder.create_folder(title, uid)
        except KeyError:
            raise gdbt.errors.DataError("Folder model missing 'title' key")
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            if exc.status_code != 412:
                raise gdbt.errors.GrafanaError(str(exc))
        folder = cls.get(grafana, uid, configuration)
        return folder

    @classmethod
    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaResourceNotFound, max_time=60
    )
    def get(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> "Folder":
        try:
            title = cls.client(grafana, configuration).client.folder.get_folder(uid)[
                "title"
            ]
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        model = {"title": title}
        model_stripped = cls._model_strip(model)
        folder = cls(grafana, uid, model_stripped)
        return folder

    @classmethod
    def exists(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> bool:
        try:
            cls.client(grafana, configuration).client.folder.get_folder(uid)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                return False
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        return True

    @classmethod
    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaResourceNotFound, max_time=60
    )
    def get_by_id(
        cls,
        grafana: str,
        id: int,
        configuration: Configuration,
    ) -> "Folder":
        try:
            data = cls.client(grafana, configuration).client.folder.get_folder_by_id(id)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(f"ID: {id}")
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        model = {"title": data["title"]}
        model_stripped = cls._model_strip(model)
        uid = data["uid"]
        folder = cls(grafana, uid, model_stripped)
        return folder

    def id(self, configuration: Configuration) -> int:
        try:
            id = self.client(self.grafana, configuration).client.folder.get_folder(
                self.uid
            )["id"]
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(self.uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        return id

    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def update(
        self,
        model: typing.Dict[str, typing.Any],
        configuration: Configuration,
    ) -> "Folder":
        try:
            model_stripped = self._model_strip(model)
            title = model_stripped["title"]
            self.client(self.grafana, configuration).client.folder.update_folder(
                self.uid, title, overwrite=True
            )
            return self
        except KeyError:
            raise gdbt.errors.DataError("Folder model missing 'title' key")
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(self.uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))

    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def delete(self, configuration: Configuration) -> None:
        try:
            self.client(self.grafana, configuration).client.folder.delete_folder(
                self.uid
            )
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                return
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))

    @property
    def serialized(self) -> typing.Dict[str, typing.Any]:
        model_stripped = self._model_strip(self.model)
        representation = {
            "kind": self._kind,
            "grafana": self.grafana,
            "uid": self.uid,
            "model": model_stripped,
        }
        return representation


@deserialize.downcast_identifier(Resource, "dashboard")
@attr.s
class Dashboard(Resource):
    folder: str = attr.ib()

    @classmethod
    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def create(  # type: ignore
        cls,
        grafana: str,
        uid: str,
        model: typing.Dict[str, typing.Any],
        folder: str,
        configuration: Configuration,
    ) -> "Dashboard":
        model_stripped = cls._model_strip(model)
        model_stripped.update({"id": None, "uid": uid, "version": 1})
        meta = {
            "dashboard": model_stripped,
            "folderId": Folder.get(grafana, folder, configuration).id(configuration),
            "overwrite": True,
        }
        try:
            cls.client(grafana, configuration).client.dashboard.update_dashboard(meta)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        return cls.get(grafana, uid, configuration)

    @classmethod
    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaResourceNotFound, max_time=60
    )
    def get(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> "Dashboard":
        try:
            dashboard = cls.client(
                grafana, configuration
            ).client.dashboard.get_dashboard(uid)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        model = dashboard["dashboard"]
        model_stripped = cls._model_strip(model)
        folder = Folder.get_by_id(
            grafana, dashboard["meta"]["folderId"], configuration
        ).uid
        dashboard = cls(grafana, uid, model_stripped, folder)
        return dashboard

    @classmethod
    def exists(
        cls,
        grafana: str,
        uid: str,
        configuration: Configuration,
    ) -> bool:
        try:
            cls.client(grafana, configuration).client.dashboard.get_dashboard(uid)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                return False
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        return True

    def id(self, configuration: Configuration) -> int:
        try:
            dashboard = self.client(
                self.grafana, configuration
            ).client.dashboard.get_dashboard(self.uid)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(self.uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        id = dashboard["dashboard"]["id"]
        return id

    def version(self, configuration: Configuration) -> int:
        try:
            dashboard = self.client(
                self.grafana, configuration
            ).client.dashboard.get_dashboard(self.uid)
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(self.uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))
        version = dashboard["dashboard"]["version"]
        return version

    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def update(
        self,
        model: typing.Dict[str, typing.Any],
        configuration: Configuration,
    ) -> "Dashboard":
        try:
            version_new = self.version(configuration) + 1
        except TypeError:
            version_new = 1
        model_stripped = self._model_strip(model)
        model_stripped.update(
            {"id": self.id(configuration), "uid": self.uid, "version": version_new}
        )
        meta = {
            "dashboard": model_stripped,
            "folderId": Folder.get(self.grafana, self.folder, configuration).id(
                configuration
            ),
            "overwrite": True,
        }
        try:
            self.client(self.grafana, configuration).client.dashboard.update_dashboard(
                meta
            )
            return self
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                raise gdbt.errors.GrafanaResourceNotFound(self.uid)
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))

    @backoff.on_exception(
        backoff.expo, exception=gdbt.errors.GrafanaServerError, max_time=60
    )
    def delete(self, configuration: Configuration) -> None:
        try:
            self.client(self.grafana, configuration).client.dashboard.delete_dashboard(
                self.uid
            )
        except grafana_api.grafana_api.GrafanaException as exc:
            if exc.status_code == 404:
                return
            if exc.status_code in (429, 500, 503, 504):
                raise gdbt.errors.GrafanaServerError(exc.message)
            raise gdbt.errors.GrafanaError(str(exc))

    @property
    def serialized(self) -> typing.Dict[str, typing.Any]:
        model_stripped = self._model_strip(self.model)
        representation = {
            "kind": self._kind,
            "grafana": self.grafana,
            "uid": self.uid,
            "model": model_stripped,
            "folder": self.folder,
        }
        return representation


@attr.s
class ResourceLoader:
    configuration: Configuration = attr.ib()

    RESOURCE_KINDS = {"dashboard": Dashboard, "folder": Folder}

    def load(
        self, resources_meta: typing.Mapping[str, ResourceGroupMeta]
    ) -> typing.Dict[str, ResourceGroup]:
        threads = self.configuration.concurrency.threads
        pool = concurrent.futures.ThreadPoolExecutor(threads)
        resources = {}
        resource_futures = {}
        for group_name, group_meta in resources_meta.items():
            resource_group_futures = {}
            for resource_name, resource_meta in group_meta.items():
                try:
                    resource_cls = typing.cast(
                        Resource, self.RESOURCE_KINDS[resource_meta["kind"]]
                    )
                except KeyError:
                    raise gdbt.errors.ConfigError(
                        f"Invalid resource kind: {resource_meta['kind']}"
                    )
                resource_future = pool.submit(
                    resource_cls.get,
                    resource_meta["grafana"],
                    resource_meta["uid"],
                    self.configuration,
                )
                resource_group_futures.update({resource_name: resource_future})
            resource_futures.update({group_name: resource_group_futures})
        for group_name, group_futures in resource_futures.items():
            group_resources = {}
            for resource_name, resource_future in group_futures.items():
                exc = resource_future.exception()
                if isinstance(exc, gdbt.errors.GrafanaResourceNotFound):
                    continue
                if exc is not None:
                    raise exc
                resource = resource_future.result(
                    timeout=self.configuration.concurrency.timeout
                )
                group_resources.update({resource_name: resource})
            resources.update({group_name: group_resources})
        return typing.cast(typing.Dict[str, ResourceGroup], resources)
