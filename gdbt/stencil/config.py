import typing

import attr
import deserialize  # type: ignore

import gdbt.provider.provider
from gdbt.stencil.stencil import Stencil


@deserialize.downcast_identifier(Stencil, "config")
@attr.s
class Config(Stencil):
    providers: typing.Dict[str, gdbt.provider.provider.Provider] = attr.ib()
    state: str = attr.ib()
