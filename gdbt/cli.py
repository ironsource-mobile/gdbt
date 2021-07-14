#!/usr/bin/env python3
import os
import pathlib
import signal
import time
import typing

import click
import halo  # type: ignore
import requests
import rich.console  # type: ignore
import rich.style  # type: ignore
import rich.traceback  # type: ignore
import semver  # type: ignore

import gdbt
import gdbt.code.configuration
import gdbt.code.templates
import gdbt.errors
import gdbt.resource
import gdbt.state

UPDATE_URL = "https://api.github.com/repos/ironsource-mobile/gdbt/releases/latest"
UPDATE_COMMAND = 'bash -c "$(curl -fsSL https://raw.githubusercontent.com/ironsource-mobile/gdbt/main/install.sh)"'

console = rich.console.Console(highlight=False)
rich.traceback.install()


@click.group()
def main():
    pass


def check_for_updates():
    url = UPDATE_URL
    update = ""
    try:
        current_version = gdbt.__version__
        upstream_version = (
            requests.get(url, timeout=2).json().get("name", current_version).lstrip("v")
        )
        if semver.compare(upstream_version, current_version) == 1:
            update = upstream_version
    except (ValueError, requests.exceptions.RequestException):
        pass
    finally:
        if update:
            console.print(f"\n[green]New version [bold]{update}[/] is available\n")
            console.print(
                f"You can update GDBT by running:\n[bold]{UPDATE_COMMAND}[/]\n"
            )


@click.command()
def version() -> None:
    """Get GDBT version"""
    console.print(f"GDBT version {gdbt.__version__}")
    console.print(f"Supported state version: {gdbt.state.state.STATE_VERSION}")
    check_for_updates()


@click.command()
@click.option(
    "-s",
    "--scope",
    type=click.STRING,
    default=".",
    help="Scope",
)
@click.option(
    "-u",
    "--update",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Update evaluation lock",
)
def validate(scope: str, update: bool) -> None:
    """Validate the configuration"""
    try:
        check_for_updates()
        console.out("")
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Evaluating paths"
            path_current = pathlib.Path(scope).expanduser().resolve()
            path_base = gdbt.code.templates.TemplateLoader(path_current).base_path

            spinner.text = "Loading configuration"
            configuration = gdbt.code.configuration.load(path_current)
            templates = gdbt.code.templates.load(path_current)

            spinner.text = "Resolving resources"
            for name, template in templates.items():
                template.resolve(name, configuration, str(path_base), update)

            spinner.succeed(
                rich.style.Style(color="green", bold=True).render(
                    "Configuration is valid!\n"
                )
            )
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        raise SystemExit(1)


@click.command()
@click.option(
    "-s",
    "--scope",
    type=click.STRING,
    default=".",
    help="Scope",
)
@click.option(
    "-u",
    "--update",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Update evaluation lock",
)
def plan(scope: str, update: bool) -> None:
    """Plan the changes"""
    try:
        check_for_updates()
        console.out("")
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Evaluating paths"
            path_current = pathlib.Path(scope).expanduser().resolve()
            path_base = gdbt.code.templates.TemplateLoader(path_current).base_path
            path_relative = path_current.relative_to(path_base)

            spinner.text = "Loading configuration"
            configuration = gdbt.code.configuration.load(path_current)
            templates = gdbt.code.templates.load(path_current)

            spinner.text = "Resolving resources"
            resources_desired = {
                name: typing.cast(
                    gdbt.resource.ResourceGroup,
                    template.resolve(name, configuration, str(path_base), update),
                )
                for name, template in templates.items()
            }

            spinner.text = "Loading resource state"
            states = gdbt.state.StateLoader(configuration).load(path_relative)
            resources_current_meta = {
                name: state.resource_meta for name, state in states.items()
            }

            spinner.text = "Refreshing resource state"
            resources_current = gdbt.resource.ResourceLoader(configuration).load(
                resources_current_meta
            )

            spinner.text = "Calculating plan"
            plan = gdbt.state.Plan.plan(resources_current, resources_desired)
            summary = gdbt.state.Plan.summary(
                resources_current, resources_desired, plan
            )
            spinner.text = "Rendering plan"
            plan_rendered, changes_pending = gdbt.state.PlanRenderer(plan).render(
                summary
            )

            if not changes_pending:
                spinner.succeed(
                    rich.style.Style(color="green", bold=True).render(
                        "Dashboards are up to date!\n"
                    )
                )
                return

        console.out(plan_rendered)
        os._exit(0)
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        raise SystemExit(1)


@click.command()
@click.option(
    "-s",
    "--scope",
    type=click.STRING,
    default=".",
    help="Scope",
)
@click.option(
    "-y",
    "--auto-approve",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Apply without confirmation",
)
@click.option(
    "-u",
    "--update",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Update evaluation lock",
)
def apply(scope: str, auto_approve: bool, update: bool) -> None:
    """Apply the changes"""
    try:
        check_for_updates()
        console.out("")
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Evaluating paths"
            path_current = pathlib.Path(scope).expanduser().resolve()
            path_base = gdbt.code.templates.TemplateLoader(path_current).base_path
            path_relative = path_current.relative_to(path_base)

            spinner.text = "Loading configuration"
            configuration = gdbt.code.configuration.load(path_current)
            templates = gdbt.code.templates.load(path_current)

            spinner.text = "Resolving resources"
            resources_desired = {
                name: typing.cast(
                    gdbt.resource.ResourceGroup,
                    template.resolve(name, configuration, str(path_base), update),
                )
                for name, template in templates.items()
            }

            spinner.text = "Loading resource state"
            states = gdbt.state.StateLoader(configuration).load(path_relative)
            resources_current_meta = {
                name: state.resource_meta for name, state in states.items()
            }

            spinner.text = "Refreshing resource state"
            resources_current = gdbt.resource.ResourceLoader(configuration).load(
                resources_current_meta
            )

            spinner.text = "Calculating plan"
            plan = gdbt.state.Plan.plan(resources_current, resources_desired)
            summary = gdbt.state.Plan.summary(
                resources_current, resources_desired, plan
            )
            spinner.text = "Rendering plan"
            plan_rendered, changes_pending = gdbt.state.PlanRenderer(plan).render(
                summary
            )

            if not changes_pending:
                spinner.succeed(
                    rich.style.Style(color="green", bold=True).render(
                        "Dashboards are up to date!\n"
                    )
                )
                return

        console.out(plan_rendered)

        if not auto_approve:
            click.confirm("Apply?", abort=True)
            console.print("\n")

        for s in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
            signal.signal(s, signal.SIG_IGN)

        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Applying changes"
            t_start = time.time()
            gdbt.state.PlanRunner(summary).apply(
                configuration, resources_current, resources_desired
            )

            spinner.text = "Uploading resource state"
            gdbt.state.StateLoader(configuration).upload(
                path_relative, resources_desired
            )
            t_end = time.time()
            duration = t_end - t_start
            spinner.succeed(
                rich.style.Style(color="green", bold=True).render(
                    f"Done! Apply took {duration:.2f} seconds.\n"
                )
            )
        os._exit(0)
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        raise SystemExit(1)


@click.command()
@click.option(
    "-s",
    "--scope",
    type=click.STRING,
    default=".",
    help="Scope",
)
@click.option(
    "-y",
    "--auto-approve",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Apply without confirmation",
)
def destroy(scope: str, auto_approve: bool) -> None:
    """Destroy resources"""
    try:
        check_for_updates()
        console.out("")
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Evaluating paths"
            path_current = pathlib.Path(scope).expanduser().resolve()
            path_base = gdbt.code.templates.TemplateLoader(path_current).base_path
            path_relative = path_current.relative_to(path_base)

            spinner.text = "Loading configuration"
            configuration = gdbt.code.configuration.load(path_current)

            spinner.text = "Loading resource state"
            states = gdbt.state.StateLoader(configuration).load(path_relative)
            resources_current_meta = {
                name: state.resource_meta for name, state in states.items()
            }

            spinner.text = "Refreshing resource state"
            resources_current = gdbt.resource.ResourceLoader(configuration).load(
                resources_current_meta
            )

            spinner.text = "Calculating plan"
            plan = gdbt.state.Plan.plan(resources_current, {})
            summary = gdbt.state.Plan.summary(resources_current, {}, plan)
            spinner.text = "Rendering plan"
            plan_rendered, changes_pending = gdbt.state.PlanRenderer(plan).render(
                summary
            )

            if not changes_pending:
                spinner.succeed(
                    rich.style.Style(color="green", bold=True).render(
                        "Dashboards are up to date!\n"
                    )
                )
                return

        console.out(plan_rendered)

        if not auto_approve:
            click.confirm("Apply?", abort=True)
            console.print("\n")

        for s in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
            signal.signal(s, signal.SIG_IGN)

        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Applying changes"
            t_start = time.time()
            gdbt.state.PlanRunner(summary).apply(configuration, resources_current, {})

            spinner.text = "Uploading resource state"
            gdbt.state.StateLoader(configuration).upload(
                path_relative,
                {
                    group_name: typing.cast(gdbt.resource.ResourceGroup, {})
                    for group_name in resources_current
                },
            )
            t_end = time.time()
            duration = t_end - t_start
            spinner.succeed(
                rich.style.Style(color="green", bold=True).render(
                    f"Done! Apply took {duration:.2f} seconds.\n"
                )
            )
        os._exit(0)
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        raise SystemExit(1)


main.add_command(version)
main.add_command(validate)
main.add_command(plan)
main.add_command(apply)
main.add_command(destroy)

if __name__ == "__main__":
    main()
