import attr
import deserialize  # type: ignore

from gdbt.provider.provider import Provider, StateProvider


@deserialize.downcast_identifier(Provider, "file")
@attr.s
class FileProvider(StateProvider):
    path: str = attr.ib()

    def client(self):
        return None

    def _read(self) -> str:
        with open(self.path, "r") as file:
            return file.read()

    def _write(self, content: str) -> None:
        with open(self.path, "w") as file:
            file.write(content)
