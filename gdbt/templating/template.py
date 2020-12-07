import typing

import attr
import jinja2

import gdbt.provider.provider


@attr.s
class Template:
    template: str = attr.ib()

    def render(
        self,
        providers: typing.Dict[str, gdbt.provider.provider.Provider],
        evaluations: typing.Dict[str, typing.Any],
        lookups: typing.Dict[str, typing.Any],
        loop_item: typing.Optional[typing.Any] = None,
    ) -> str:
        template = jinja2.Template(self.template)
        rendered = template.render(
            providers=providers,
            evaluations=evaluations,
            lookups=lookups,
            item=loop_item,
        )
        return rendered
