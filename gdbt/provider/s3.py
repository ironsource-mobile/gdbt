import typing

import attr
import boto3  # type: ignore
import boto3.resources.base  # type: ignore
import botocore.exceptions  # type: ignore
import deserialize  # type: ignore

import gdbt.errors
from gdbt.provider.provider import Provider, StateProvider

STATE_OBJECT_PATH = "state.json"


@deserialize.downcast_identifier(Provider, "s3")
@attr.s
class S3Provider(StateProvider):
    bucket: str = attr.ib()
    access_key_id: typing.Optional[str] = attr.ib()
    secret_access_key: typing.Optional[str] = attr.ib()

    def client(self) -> boto3.resources.base.ServiceResource:
        return boto3.resource(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

    def _read(self) -> str:
        s3 = self.client()
        try:
            object = s3.Object(self.bucket, STATE_OBJECT_PATH)
            content = object.get()["Body"].read().decode("utf-8")
            return content
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "NoSuchKey": gdbt.errors.S3ObjectNotFound(STATE_OBJECT_PATH),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
                "default": gdbt.errors.S3Error(exc.response.get("message")),
            }
            raise (errors.get(exc.response["Error"]["Code"], errors["default"]))

    def _write(self, content: str) -> None:
        s3 = self.client()
        try:
            object = s3.Object(self.bucket, STATE_OBJECT_PATH)
            object.put(Body=content.encode("utf-8"))
        except botocore.exceptions.ClientError as exc:
            errors = {
                "NoSuchBucket": gdbt.errors.S3BucketNotFound(self.bucket),
                "AccessDenied": gdbt.errors.S3AccessDenied(self.bucket),
                "default": gdbt.errors.S3Error(exc.response.get("message")),
            }
            raise (errors.get(exc.response["Error"]["Code"], errors["default"]))
