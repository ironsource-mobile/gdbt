import typing

import attr
import deepdiff  # type: ignore

import gdbt.provider.provider
import gdbt.state.state

ACTION_SYMBOLS = {"create": "+", "remove": "-", "update": "~"}


@attr.s
class Outcome:
    value: typing.Any = attr.ib()
    color = ""
    action = ""

    def render(self, key: str, padding: int) -> str:
        text = f"  [{self.color}]{ACTION_SYMBOLS[self.action]}[/] "
        text += (key + ":").ljust(padding + 1)
        text += self.render_value()
        return text

    def render_value(self) -> str:
        text = f'  "[{self.color}]{self.truncate_value(self.value)}[/]"'
        return text

    def render_heading(self, heading: str) -> str:
        kind, name = heading.split("_", 1)
        text = f"[{self.color}]{ACTION_SYMBOLS[self.action]}[/]"
        text += f" {kind.title()} [b]{name}[/]"
        text += f" will be [{self.color}]{self.action}d[/]:"
        return text

    def truncate_value(self, value: typing.Any) -> typing.Any:
        allowed = (str, int, float, bool)
        # placeholders = {"dict": "{...}", "list": "[...]"}
        # truncated = (
        #     placeholders.get(type(value).__name__, "...")
        #     if type(value) not in allowed
        #     else value
        # )
        if type(value) in allowed:
            return value
        value = str(value)
        truncated = (value[:64] + "...") if len(value) > 64 else value
        return truncated


class Added(Outcome):
    color = "green"
    action = "create"


class Removed(Outcome):
    color = "red"
    action = "remove"


@attr.s
class Changed(Outcome):
    value_old: typing.Any = attr.ib()

    color = "yellow"
    action = "update"

    def render_value(self) -> str:
        text = f'  "[{Removed.color}]{self.truncate_value(self.value_old)}[/]"'
        text += " [grey66]=>[/]"
        text += f' "[{Added.color}]{self.truncate_value(self.value)}[/]"'
        return text


class UpToDate(Exception):
    def __init__(self, message: str = "") -> None:
        self.message = message


@attr.s
class StateDiff:
    current: gdbt.state.state.State = attr.ib()
    desired: gdbt.state.state.State = attr.ib()

    def serialized(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
        current = self.current.serialize(providers)
        desired = self.desired.serialize(providers)
        return current, desired

    def keys(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> typing.Set[str]:
        current, desired = self.serialized(providers)
        keys = set(current.keys()).union(set(desired.keys()))
        return keys

    def diff(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> typing.Dict[str, typing.Dict[str, Outcome]]:
        current, desired = self.serialized(providers)
        result = {
            key: self._diff_convert(
                deepdiff.DeepDiff(
                    current.get(key, {}),
                    desired.get(key, {}),
                    verbose_level=2,
                    ignore_order=True,
                    report_repetition=True,
                )
            )
            for key in self.keys(providers)
        }
        result = {k: v for k, v in result.items() if v}
        return result

    def outcomes(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> typing.Dict[str, Outcome]:
        outcomes = {}
        for key, value in self.diff(providers).items():
            outcome: Outcome
            if all([isinstance(v, Added) for v in value.values()]):
                outcome = Added("")
            elif all([isinstance(v, Removed) for v in value.values()]):
                outcome = Removed("")
            else:
                outcome = Changed("", "")
            outcomes.update({key: outcome})
        return outcomes

    def render(
        self, providers: typing.Dict[str, gdbt.provider.provider.Provider]
    ) -> str:
        blocks = []
        diff = self.diff(providers)
        for i in sorted(diff.keys()):
            lines = []
            lines.append(self.outcomes(providers)[i].render_heading(i))
            for j in sorted(diff[i].keys()):
                if j in ("kind", "folder", "grafana", "uid"):
                    continue
                lines.append(diff[i][j].render(j, len(max(diff[i], key=len))))
            if len(lines) <= 1:
                continue
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def _diff_convert(
        self, deepdiff_tree: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, Outcome]:
        def path_convert(path_square: str) -> str:
            path = (
                path_square.replace("'", "")
                .replace("]", "")
                .replace("[", ".")
                .removeprefix("root.")
            )
            return path

        tree: typing.Dict[str, Outcome] = {}
        for key, value in (
            deepdiff_tree.get("dictionary_item_added", {})
            | deepdiff_tree.get("iterable_item_added", {})
        ).items():
            tree.update({path_convert(key): Added(value)})
        for key, value in (
            deepdiff_tree.get("dictionary_item_removed", {})
            | deepdiff_tree.get("iterable_item_removed", {})
        ).items():
            tree.update({path_convert(key): Removed(value)})
        for key, value in (
            deepdiff_tree.get("values_changed", {})
            | deepdiff_tree.get("type_changes", {})
        ).items():
            tree.update(
                {path_convert(key): Changed(value["new_value"], value["old_value"])}
            )
        return tree
