import pathlib
import typing

import attr
import botocore.exceptions  # type: ignore
import deserialize  # type: ignore
import s3path  # type: ignore

import gdbt.errors
from gdbt.provider import Provider, StateProvider

STATE_OBJECT_EXTENSION = ".json"


@deserialize.downcast_identifier(Provider, "s3")
@deserialize.default("_object_extension", STATE_OBJECT_EXTENSION)
@attr.s
class S3Provider(StateProvider):
    bucket: str = attr.ib()
    _object_extension = STATE_OBJECT_EXTENSION

    def client(self):
        pass

    @property
    def _base_path(self) -> s3path.S3Path:
        s3_path = s3path.S3Path("/" + self.bucket.strip("/"))
        base_path = s3_path / (self.path or ".")
        return base_path

    def _list(self, path: pathlib.Path) -> typing.Generator[pathlib.Path, None, None]:
        try:
            base_path = typing.cast(pathlib.Path, self._base_path)
            for object in (base_path / path).glob(f"**/*{self._object_extension}"):
                if object.is_file():
                    yield object.relative_to(base_path).with_suffix("")
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
            }
            raise (
                errors.get(
                    exc.response["Error"]["Code"],
                    gdbt.errors.S3Error(exc.response["Error"]["Message"]),
                )
            )

    def _get(self, path: pathlib.Path) -> str:
        try:
            base_path = typing.cast(pathlib.Path, self._base_path)
            object = base_path / path
            content = object.read_text()
            return content
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "NoSuchKey": gdbt.errors.S3ObjectNotFound(str(path)),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
            }
            raise (
                errors.get(
                    exc.response["Error"]["Code"],
                    gdbt.errors.S3Error(exc.response["Error"]["Message"]),
                )
            )

    def _put(self, path: pathlib.Path, content: str) -> None:
        try:
            base_path = typing.cast(pathlib.Path, self._base_path)
            object = base_path / path
            object.write_text(content)
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
            }
            raise (
                errors.get(
                    exc.response["Error"]["Code"],
                    gdbt.errors.S3Error(exc.response["Error"]["Message"]),
                )
            )

    def _remove(self, path: pathlib.Path):
        try:
            base_path = typing.cast(pathlib.Path, self._base_path)
            object = base_path / path
            object.unlink(missing_ok=True)
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
            }
            raise (
                errors.get(
                    exc.response["Error"]["Code"],
                    gdbt.errors.S3Error(exc.response["Error"]["Message"]),
                )
            )

    def _lock(self, path: pathlib.Path) -> None:
        pass

    def _unlock(self, path: pathlib.Path) -> None:
        pass
