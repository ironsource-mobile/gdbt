import pathlib
import typing

import deserialize  # type: ignore
import ruamel.yaml  # type: ignore

import gdbt.errors
import gdbt.stencil.config
from gdbt.stencil.stencil import ResourceStencil, Stencil

yaml = ruamel.yaml.YAML(typ="safe")


def load_config(config_dir: str = "") -> gdbt.stencil.config.Config:
    path = pathlib.Path(config_dir) / "config.yaml"
    try:
        config = deserialize.deserialize(Stencil, yaml.load(path))
    except FileNotFoundError:
        raise gdbt.errors.ConfigFileNotFound(str(path))
    except (ruamel.yaml.YAMLError, deserialize.DeserializeException) as exc:
        raise gdbt.errors.ConfigFormatInvalid(str(exc))
    return config


def load_resources(config_dir: str = ".") -> typing.Dict[str, ResourceStencil]:
    path = pathlib.Path(config_dir) / "resources"
    stencils = {}
    try:
        for p in path.glob("**/*.yaml"):
            stencil = deserialize.deserialize(Stencil, yaml.load(p))
            stencils.update({p.stem: stencil})
    except (ruamel.yaml.YAMLError, deserialize.DeserializeException) as exc:
        raise gdbt.errors.ConfigFormatInvalid(str(exc))
    return stencils
