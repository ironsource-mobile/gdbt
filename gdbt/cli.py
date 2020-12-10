#!/usr/bin/env python3
import signal
import time
import typing

import click
import halo  # type: ignore
import rich.console
import rich.traceback

import gdbt
import gdbt.errors
import gdbt.provider.provider
import gdbt.state.diff
import gdbt.state.plan
import gdbt.state.state
import gdbt.stencil.load

console = rich.console.Console(highlight=False)
rich.traceback.install()


@click.group()
def main():
    pass


@click.command()
def version() -> None:
    """Get GDBT version"""
    console.print(f"GDBT version {gdbt.__version__}")


@click.command()
@click.option(
    "-c",
    "--config-dir",
    type=click.STRING,
    default=".",
    help="Configuration directory",
)
@click.option(
    "-d",
    "--debug",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Debug mode",
)
def validate(config_dir: str, debug: bool) -> None:
    """Validate the configuration"""
    try:
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Loading config"
            config = gdbt.stencil.load.load_config(config_dir)
            spinner.text = "Loading resources"
            stencils = gdbt.stencil.load.load_resources(config_dir)
            spinner.text = "Resolving resources"
            for key, value in stencils.items():
                value.resolve(
                    key,
                    config.providers,
                    typing.cast(typing.Dict[str, typing.Any], config.evaluations),
                    typing.cast(typing.Dict[str, typing.Any], config.lookups),
                )
        console.print("\n[bold green]Configuration is valid\n")
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        if debug:
            console.print_exception()
        raise SystemExit(1)


@click.command()
@click.option(
    "-c",
    "--config-dir",
    type=click.STRING,
    default=".",
    help="Configuration directory",
)
@click.option(
    "-d",
    "--debug",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Debug mode",
)
def plan(config_dir: str, debug: bool) -> None:
    """Plan the changes"""
    try:
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Loading config"
            config = gdbt.stencil.load.load_config(config_dir)

            spinner.text = "Loading resources"
            stencils = gdbt.stencil.load.load_resources(config_dir)

            spinner.text = "Resolving resources"
            resources = {}
            for key, value in stencils.items():
                stencil_resources = value.resolve(
                    key,
                    config.providers,
                    typing.cast(typing.Dict[str, typing.Any], config.evaluations),
                    typing.cast(typing.Dict[str, typing.Any], config.lookups),
                )
                resources.update(stencil_resources)
            state_desired = gdbt.state.state.State(resources)

            spinner.text = "Loading state"
            state_current = gdbt.state.state.State.load(
                config.state,
                config.providers,
            )

            spinner.text = "Preparing the plan"
            state_diff = gdbt.state.diff.StateDiff(state_current, state_desired)
            state_diff_rendered = state_diff.render(config.providers)
            changes = len(state_diff.outcomes(config.providers).values())

        if changes == 0:
            console.print("\n[bold green]Dashboards are up to date![/]\n")
            return

        console.print("\n[b]Planned changes:[/b]\n")
        console.print(state_diff_rendered)
        console.print("\nRun [bold green]gdbt apply[/] to apply these changes\n")
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        if debug:
            console.print_exception()
        raise SystemExit(1)


@click.command()
@click.option(
    "-c",
    "--config-dir",
    type=click.STRING,
    default=".",
    help="Configuration directory",
)
@click.option(
    "-y",
    "--auto-approve",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Do not ask for confirmation",
)
@click.option(
    "-d",
    "--debug",
    type=click.BOOL,
    default=False,
    is_flag=True,
    help="Debug mode",
)
def apply(config_dir: str, auto_approve: bool, debug: bool) -> None:
    """Apply the changes"""
    try:
        with halo.Halo(text="Loading", spinner="dots") as spinner:
            spinner.text = "Loading config"
            config = gdbt.stencil.load.load_config(config_dir)

            spinner.text = "Loading resources"
            stencils = gdbt.stencil.load.load_resources(config_dir)

            spinner.text = "Resolving resources"
            resources = {}
            for key, value in stencils.items():
                stencil_resources = value.resolve(
                    key,
                    config.providers,
                    typing.cast(typing.Dict[str, typing.Any], config.evaluations),
                    typing.cast(typing.Dict[str, typing.Any], config.lookups),
                )
                resources.update(stencil_resources)
            state_desired = gdbt.state.state.State(resources)

            spinner.text = "Loading state"
            state_current = gdbt.state.state.State.load(
                config.state,
                config.providers,
            )

            spinner.text = "Preparing the plan"
            state_diff = gdbt.state.diff.StateDiff(state_current, state_desired)
            state_diff_rendered = state_diff.render(config.providers)
            changes = len(state_diff.outcomes(config.providers).values())

        if changes == 0:
            console.print("\n[bold green]Dashboards are up to date![/]\n")
            return

        console.print("\n[b]Pending changes:[/b]\n")
        console.print(state_diff_rendered)
        console.print("\n")

        if not auto_approve:
            click.confirm("Apply?", abort=True)
            console.print("\n")

        # Disable interruptions
        for s in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
            signal.signal(s, signal.SIG_IGN)

        t_start = time.time()
        plan = gdbt.state.plan.Plan(state_diff)
        plan.apply(config.state, config.providers)
        t_end = time.time()
        duration = t_end - t_start

        console.print(
            f"\n[bold green]Done! Modified {changes} resources in {duration:.2f} seconds.\n"
        )
    except gdbt.errors.Error as exc:
        console.print(f"[red][b]ERROR[/b] {exc.text}")
        if debug:
            console.print_exception()
        raise SystemExit(1)


main.add_command(version)
main.add_command(validate)
main.add_command(plan)
main.add_command(apply)

if __name__ == "__main__":
    main()
