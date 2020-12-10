import typing

import attr
import deserialize  # type: ignore
import halo  # type: ignore
import rich.style

import gdbt.errors
import gdbt.resource.resource
import gdbt.state.diff
import gdbt.state.state

STYLE_BOLD = rich.style.Style(bold=True)


@attr.s
class Plan:
    diff: gdbt.state.diff.StateDiff = attr.ib()

    def apply(self, source: str, providers: typing.Dict[str, typing.Any]) -> None:
        resources = self.diff.current.resources
        outcomes = self.diff.outcomes(providers)
        for key in sorted(outcomes.keys(), reverse=True):
            with halo.Halo(text="Applying changes", spinner="dots") as spinner:
                if outcomes[key].action == "create":
                    kind, name = key.split("_", 1)
                    spinner.text = f"Creating {kind} {STYLE_BOLD.render(name)}"
                    resource = self.diff.desired.serialize(providers)[key]
                    resource_cls = type(
                        deserialize.deserialize(
                            gdbt.resource.resource.Resource, resource
                        )
                    )
                    resource.pop("kind", None)
                    resource_created = resource_cls.create(
                        providers=providers, **resource
                    )
                    resources.update({key: resource_created})
                    spinner.text = "Updating state"
                    gdbt.state.state.State(resources).push(source, providers)
                    spinner.succeed(f"Created {kind} {STYLE_BOLD.render(name)}")
                elif outcomes[key].action == "remove":
                    kind, name = key.split("_", 1)
                    spinner.text = f"Deleting {kind} {STYLE_BOLD.render(name)}"
                    resource = self.diff.current.resources[key]
                    resource.delete(providers)
                    resources.pop(key, None)
                    spinner.text = "Updating state"
                    gdbt.state.state.State(resources).push(source, providers)
                    spinner.succeed(f"Deleted {kind} {STYLE_BOLD.render(name)}")
                else:
                    kind, name = key.split("_", 1)
                    spinner.text = f"Updating {kind} {STYLE_BOLD.render(name)}"
                    resource = self.diff.current.resources[key]
                    resource_new = self.diff.desired.resources[key]
                    resource.update(resource_new.model, providers)
                    resources.update({key: resource_new})
                    spinner.text = "Updating state"
                    gdbt.state.state.State(resources).push(source, providers)
                    spinner.succeed(f"Updated {kind} {STYLE_BOLD.render(name)}")
