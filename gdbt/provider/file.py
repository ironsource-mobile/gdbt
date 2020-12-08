import attr
import deserialize  # type: ignore

import gdbt.errors
from gdbt.provider.provider import Provider, StateProvider


@deserialize.downcast_identifier(Provider, "file")
@attr.s
class FileProvider(StateProvider):
    path: str = attr.ib()

    def client(self):
        return None

    def _read(self) -> str:
        try:
            with open(self.path, "r") as file:
                return file.read()
        except FileNotFoundError:
            raise gdbt.errors.FileNotFound(self.path)
        except PermissionError:
            raise gdbt.errors.FileAccessDenied(self.path)
        except OSError as exc:
            raise gdbt.errors.FileError(str(exc))

    def _write(self, content: str) -> None:
        try:
            with open(self.path, "w") as file:
                file.write(content)
        except PermissionError:
            raise gdbt.errors.FileAccessDenied(self.path)
        except OSError as exc:
            raise gdbt.errors.FileError(str(exc))
