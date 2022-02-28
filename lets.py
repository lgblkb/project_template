#!/usr/bin/env python3
import os
from typing import Optional

import typer
from box import Box

from provision.utils.base import project_folder, commands_folder, run_cmd

__version__ = '1.0.0'
app = typer.Typer()
state = dict(verbose=0)
context_settings = {"allow_extra_args": True, "ignore_unknown_options": True}


@app.command(context_settings=context_settings, help="Build project's docker image")
def build(ctx: typer.Context):
    run_cmd(commands_folder / 'docker_build.sh', ctx=ctx)


envs_folder = project_folder / 'provision' / 'envs'


def env_autocompletion():
    return os.listdir(envs_folder)


playbooks = {p.with_suffix('').name: p for p in list((project_folder / 'provision').glob('*.yaml'))}


def playbook_autocompletion():
    return list(playbooks)


@app.command(context_settings=context_settings, help='Create and enter containerized environment for local development')
def run(ctx: typer.Context,
        cmd: str = typer.Option('bash', '--cmd'),
        display: bool = typer.Option(False, '--display'),
        gpus: bool = typer.Option(False, '--gpus'),
        root: bool = typer.Option(False, '--root')):
    cmd_parts = list()
    cmd_parts.append(commands_folder / 'docker_run.sh')
    cmd_parts.append('-it --rm')
    if display:
        os.system('xhost +')
        cmd_parts.append('--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"')
        cmd_parts.append('--env="DISPLAY"')
    if root:
        cmd_parts.append('--user root')
    if gpus:
        cmd_parts.append('--gpus all')
    image_fullname = Box.from_yaml(filename=project_folder.joinpath('settings.yaml')).image_fullname
    cmd_parts.extend(ctx.args)
    cmd_parts.append(image_fullname)
    cmd_parts.append(cmd)
    run_cmd(*cmd_parts)


@app.command(context_settings=context_settings, help='Play ansible playbook in provided environment.')
def play(ctx: typer.Context,
         playbook_name=typer.Argument('base', autocompletion=playbook_autocompletion, ),
         env=typer.Option('development', '--env', '-e', autocompletion=env_autocompletion)):
    cmd_parts = list()
    cmd_parts.append(f'ansible-playbook {playbooks[playbook_name]}')
    cmd_parts.append(f'--inventory {envs_folder / env}')
    run_cmd(*cmd_parts, ctx=ctx)


def version_callback(value: bool):
    if value:
        typer.echo(f"{project_folder.name}: {__version__}")
        raise typer.Exit()


@app.callback()
def main(verbose: int = typer.Option(0, '--verbose', '-v', count=True),
         version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True)
         ):
    if version:
        pass
    """
    This tool enables:

        1. Quick setup of local development environment.

        2. Powerful settings management with 12-factor methodology in mind.

        3. Effortless project deployment to remote servers.

    """
    if verbose:
        typer.echo(f"Verbose level {verbose}")
        state["verbose"] = verbose


if __name__ == "__main__":
    app()
