import typing

import attr
import deserialize  # type: ignore
import halo  # type: ignore

import gdbt.errors
import gdbt.resource.resource
import gdbt.state.diff
import gdbt.state.state


@attr.s
class Plan:
    diff: gdbt.state.diff.StateDiff = attr.ib()

    def apply(self, providers: typing.Dict[str, typing.Any]) -> gdbt.state.state.State:
        resources = self.diff.current.resources
        outcomes = self.diff.outcomes(providers)
        for key in sorted(outcomes.keys(), reverse=True):
            with halo.Halo(text="Applying changes", spinner="dots") as spinner:
                if outcomes[key].action == "create":
                    spinner.text = f"Creating resource {key}"
                    resource = self.diff.desired.serialize(providers)[key]
                    resource_cls = type(deserialize.deserialize(gdbt.resource.resource.Resource, resource))
                    resource.pop("kind", None)
                    resource_created = resource_cls.create(providers=providers, **resource)
                    resources.update({key: resource_created})
                    spinner.succeed(f"Created resource {key}")
                elif outcomes[key].action == "delete":
                    spinner.text = f"Deleting resource {key}"
                    resource = self.diff.current.resources[key]
                    resource.delete(providers)
                    resources.pop(key, None)
                    spinner.succeed(f"Deleted resource {key}")
                else:
                    spinner.text = f"Updating resource {key}"
                    resource = self.diff.current.resources[key]
                    resource_new = self.diff.desired.resources[key]
                    resource.update(resource_new.model, providers)
                    resources.update({key: resource_new})
                    spinner.succeed(f"Updated resource {key}")
        return gdbt.state.state.State(resources)
