import os
from pathlib import Path

import typer

project_folder = Path(__file__).parents[2].absolute()
commands_folder = project_folder / 'provision' / 'commands'


def run_cmd(*cmd_parts, ctx: typer.Context = None):
    cmd_parts = list(cmd_parts)
    if ctx is not None:
        cmd_parts.extend(ctx.args)
    cmd = " ".join(map(str, cmd_parts))
    typer.secho(cmd, fg=typer.colors.GREEN, bold=True)
    return os.system(cmd)
