import collections
import concurrent.futures
import enum
import typing

import attr
import dictdiffer  # type: ignore
import flatten_dict  # type: ignore
import rich.style

from gdbt.code import Configuration
from gdbt.resource import Resource, ResourceGroup

ACTION_SYMBOLS = {"CREATE": "+", "REMOVE": "-", "UPDATE": "~"}
ACTION_COLORS = {
    "CREATE": "green",
    "REMOVE": "red",
    "UPDATE": "yellow",
    "GREY": "grey66",
}


class Plan(collections.UserDict):
    @classmethod
    def _resources(
        cls,
        resources_current: typing.Mapping[str, ResourceGroup],
        resources_desired: typing.Mapping[str, ResourceGroup],
    ) -> typing.Set[str]:
        resources = set()
        resources_current_flat = flatten_dict.flatten(
            resources_current, reducer=lambda *x: x[-1]
        )
        resources_desired_flat = flatten_dict.flatten(
            resources_desired, reducer=lambda *x: x[-1]
        )
        resources = set(resources_current_flat.keys()).union(
            set(resources_desired_flat.keys())
        )
        return resources

    @classmethod
    def _normalize(
        cls, diff: typing.Sequence
    ) -> typing.Dict[str, typing.Tuple["Plan.Outcome", typing.Any, typing.Any]]:
        normalized = {}
        for item in diff:
            path, value_current, value_desired = "", None, None
            (action, path_elements, values) = item
            if action == "change":
                (value_current, value_desired) = values
                path = ".".join(map(str, path_elements))
            if action in ("add", "remove"):
                (key, value) = values[0]
                (value_current, value_desired) = (
                    (None, value) if action == "add" else (value, None)
                )
                path = ".".join(map(str, path_elements + [key]))
            outcome = cls.Outcome(action)
            if path in ("kind", "grafana", "uid", "folder"):
                continue
            normalized.update({path: (outcome, value_current, value_desired)})
        return normalized

    @classmethod
    def plan(
        cls,
        resources_current: typing.Mapping[str, ResourceGroup],
        resources_desired: typing.Mapping[str, ResourceGroup],
    ) -> "Plan":
        resources = cls._resources(resources_current, resources_desired)
        resources_current_flat = flatten_dict.flatten(
            resources_current, reducer=lambda *x: x[-1]
        )
        resources_desired_flat = flatten_dict.flatten(
            resources_desired, reducer=lambda *x: x[-1]
        )
        plan_dict = {}
        for resource in resources:
            try:
                current = resources_current_flat[resource].serialized
            except KeyError:
                current = {}
            try:
                desired = resources_desired_flat[resource].serialized
            except KeyError:
                desired = {}
            diff = list(
                dictdiffer.diff(current, desired, expand=True, dot_notation=False)
            )
            if diff:
                plan_dict.update({resource: cls._normalize(diff)})
        plan = cls(plan_dict)
        return plan

    @classmethod
    def summary(
        cls,
        resources_current: typing.Mapping,
        resources_desired: typing.Mapping,
        plan: "Plan",
    ) -> typing.Dict[str, "Plan.Outcome"]:
        resources = cls._resources(resources_current, resources_desired)
        resources_current_flat = flatten_dict.flatten(
            resources_current, reducer=lambda *x: x[-1]
        )
        resources_desired_flat = flatten_dict.flatten(
            resources_desired, reducer=lambda *x: x[-1]
        )
        summary_unsorted: typing.Dict[str, typing.Dict] = {
            "folder": {},
            "dashboard": {},
        }
        for resource in resources:
            if resource not in plan:
                continue
            if resource not in resources_desired_flat:
                summary_unsorted[resources_current_flat[resource]._kind].update(
                    {resource: Plan.Outcome.REMOVE}
                )
                continue
            if resource not in resources_current_flat:
                summary_unsorted[resources_desired_flat[resource]._kind].update(
                    {resource: Plan.Outcome.CREATE}
                )
                continue
            summary_unsorted[resources_desired_flat[resource]._kind].update(
                {resource: Plan.Outcome.UPDATE}
            )
        summary_sorted: typing.Dict[str, Plan.Outcome] = collections.OrderedDict()
        for kind in ("folder", "dashboard"):
            summary_sorted.update(**summary_unsorted[kind])
        return summary_sorted

    class Outcome(enum.Enum):
        CREATE = "add"
        REMOVE = "remove"
        UPDATE = "change"


@attr.s
class PlanRenderer:
    plan: Plan = attr.ib()

    def _render_action_symbol(self, outcome: Plan.Outcome) -> str:
        action_symbol = ACTION_SYMBOLS[outcome.name]
        action_color = ACTION_COLORS[outcome.name]
        rendered = rich.style.Style(color=action_color).render(action_symbol)
        return rendered

    def _render_action_verb(self, outcome: Plan.Outcome, passive=True) -> str:
        action_verb = outcome.name.lower()
        if passive:
            action_verb += "d"
        action_color = ACTION_COLORS[outcome.name]
        rendered = rich.style.Style(color=action_color).render(action_verb)
        return rendered

    def _render_value(self, value: typing.Any, type: str) -> str:
        action_color = (
            ACTION_COLORS["REMOVE"] if type == "current" else ACTION_COLORS["CREATE"]
        )
        value_str = str(value)
        if len(value_str) > 32:
            value_str = value_str[:32] + "\u2026"
        rendered = rich.style.Style(color=action_color).render(str(value))
        rendered_quoted = '"' + rendered + '"'
        return rendered_quoted

    def _render_value_set(
        self,
        outcome: Plan.Outcome,
        value_current: typing.Any,
        value_desired: typing.Any,
    ) -> str:
        value_current_rendered = self._render_value(value_current, "current")
        value_desired_rendered = self._render_value(value_desired, "desired")
        value_arrow_rendered = rich.style.Style(color=ACTION_COLORS["GREY"]).render(
            "=>"
        )
        value_set_templates = {
            "CREATE": f"{value_desired_rendered}",
            "REMOVE": f"{value_current_rendered}",
            "UPDATE": f"{value_current_rendered} {value_arrow_rendered} {value_desired_rendered}",
        }
        rendered = value_set_templates[outcome.name]
        return rendered

    def _render_key_value(
        self,
        key: str,
        outcome: Plan.Outcome,
        value_current: typing.Any,
        value_desired: typing.Any,
        max_width: int,
    ) -> str:
        symbol = self._render_action_symbol(outcome)
        key_justified = (key + ":").ljust(max_width + 1)
        value_set = self._render_value_set(outcome, value_current, value_desired)
        rendered = f"  {symbol} {key_justified}  {value_set}"
        return rendered

    def _render_header(self, name: str, outcome: Plan.Outcome) -> str:
        symbol = self._render_action_symbol(outcome)
        name_rendered = rich.style.Style(bold=True).render(name)
        verb = self._render_action_verb(outcome)
        rendered = f"{symbol} {name_rendered} will be {verb}"
        if outcome is Plan.Outcome.UPDATE:
            rendered += ":"
        return rendered

    def _render_single(
        self,
        name: str,
        summary: Plan.Outcome,
        plan: typing.Mapping[str, typing.Tuple[Plan.Outcome, typing.Any, typing.Any]],
    ) -> str:
        lines = []
        lines.append(self._render_header(name, summary))
        if summary is Plan.Outcome.UPDATE:
            body_max_width = len(max(plan.keys(), key=len))
            for key, value in plan.items():
                (outcome, value_current, value_desired) = value
                item = self._render_key_value(
                    key, outcome, value_current, value_desired, body_max_width
                )
                lines.append(item)
            lines.append("\n")
        rendered = "\n".join(lines)
        return rendered

    def _render_body(self, summaries: typing.Mapping[str, Plan.Outcome]) -> str:
        blocks = []
        for resource in sorted(self.plan.keys(), key=lambda x: x.lower()):
            plan = self.plan[resource]
            summary = summaries[resource]
            block_rendered = self._render_single(resource, summary, plan)
            blocks.append(block_rendered)
        rendered = "\n".join(blocks).strip()
        return rendered

    def _render_summary(self, summaries: typing.Mapping[str, Plan.Outcome]) -> str:
        summary_items = []
        for outcome in (Plan.Outcome.CREATE, Plan.Outcome.UPDATE, Plan.Outcome.REMOVE):
            count = list(summaries.values()).count(outcome)
            if not count:
                continue
            color = ACTION_COLORS[outcome.name]
            verb = rich.style.Style(color=color).render(
                self._render_action_verb(outcome)
            )
            summary_items.append(f"{count} resources will be {verb}")
        summary_header = rich.style.Style(bold=True).render("Summary:")
        summary_body = ", ".join(summary_items)
        summary = f"{summary_header} {summary_body}."
        return summary

    def _render_footer(self) -> str:
        command = "gdbt apply"
        command_rendered = rich.style.Style(
            bold=True, color=ACTION_COLORS["CREATE"]
        ).render(command)
        footer_rendered = f"Run {command_rendered} to apply these changes"
        return footer_rendered

    def render(
        self, summaries: typing.Mapping[str, Plan.Outcome]
    ) -> typing.Tuple[str, bool]:
        if not self.plan:
            message = "Dashboards are up to date!"
            message_rendered = rich.style.Style(
                bold=True, color=ACTION_COLORS["CREATE"]
            ).render(message)
            rendered = "\n" + message_rendered + "\n"
            return rendered, False
        header = "Planned changes:"
        header_rendered = rich.style.Style(bold=True).render(header)
        body_rendered = self._render_body(summaries)
        summary_rendered = self._render_summary(summaries)
        footer_rendered = self._render_footer()
        parts_rendered = [
            header_rendered,
            body_rendered,
            summary_rendered,
            footer_rendered,
        ]
        plan_rendered = "\n" + "\n\n".join(parts_rendered) + "\n\n"
        return plan_rendered, True


@attr.s
class PlanRunner:
    summary: typing.Mapping[str, Plan.Outcome] = attr.ib()

    def resources(
        self,
        resources_current: typing.Mapping[str, ResourceGroup],
        resources_desired: typing.Mapping[str, ResourceGroup],
    ) -> typing.Dict[str, Resource]:
        resources = {}
        resources_current_flat = flatten_dict.flatten(
            resources_current, reducer=lambda *x: x[-1]
        )
        resources_desired_flat = flatten_dict.flatten(
            resources_desired, reducer=lambda *x: x[-1]
        )
        for resource_name, outcome in self.summary.items():
            if outcome == Plan.Outcome.REMOVE:
                resource = resources_current_flat[resource_name]
                resources.update({resource_name: resource})
                continue
            resource = resources_desired_flat[resource_name]
            resources.update({resource_name: resource})
        return resources

    def apply(
        self,
        configuration: Configuration,
        resources_current: typing.Mapping[str, ResourceGroup],
        resources_desired: typing.Mapping[str, ResourceGroup],
    ) -> None:
        threads = configuration.concurrency.threads
        pool = concurrent.futures.ThreadPoolExecutor(threads)
        action_futures = []
        resources = self.resources(resources_current, resources_desired)
        for name, resource in resources.items():
            outcome = self.summary[name]
            if outcome in (Plan.Outcome.CREATE, Plan.Outcome.UPDATE):
                resource_serialized = resource.serialized
                resource_serialized.pop("kind", None)
                if outcome == Plan.Outcome.CREATE:
                    future = pool.submit(
                        resource.create,
                        configuration=configuration,
                        **resource_serialized,
                    )
                else:
                    future = pool.submit(
                        resource.update,
                        configuration=configuration,
                        model=resource_serialized["model"],
                    )
                action_futures.append(future)
            if outcome == Plan.Outcome.REMOVE:
                future = pool.submit(resource.delete, configuration=configuration)  # type: ignore
                action_futures.append(future)
        results, _ = concurrent.futures.wait(
            action_futures, timeout=configuration.concurrency.timeout
        )
        for result in results:
            if result.exception() is not None:
                raise result.exception()  # type: ignore
