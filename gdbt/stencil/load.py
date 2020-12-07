import pathlib
import typing

import deserialize  # type: ignore
import ruamel.yaml  # type: ignore

import gdbt.stencil.config
from gdbt.stencil.stencil import Stencil, ResourceStencil

yaml = ruamel.yaml.YAML(typ="safe")


def load_config(config_dir: str = "") -> gdbt.stencil.config.Config:
    path = pathlib.Path(config_dir) / "config.yaml"
    config = deserialize.deserialize(Stencil, yaml.load(path))
    return config


def load_resources(config_dir: str = ".") -> typing.Dict[str, ResourceStencil]:
    path = pathlib.Path(config_dir) / "resources"
    stencils = {}
    for p in path.glob("**/*.yaml"):
        stencil = deserialize.deserialize(Stencil, yaml.load(p))
        stencils.update({p.stem: stencil})
    return stencils
