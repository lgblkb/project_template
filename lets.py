#!/usr/bin/env python
import getpass
import os
import subprocess
from enum import Enum
from pathlib import Path
from typing import List

import dotenv
import typer
from rich.console import Console

console = Console(color_system='auto')
app = typer.Typer()

project_folder = Path(__file__).resolve().parent


# class DotenvMan:
#     def __init__(self, env_path: Path = Path('.env')):
#         self.env_path = env_path
#         self.data = self.get()
#
#     def __getitem__(self, item):
#         return self.data[item]
#
#     def __setitem__(self, key, value):
#         self.data[key] = value
#         dotenv.set_key(self.env_path, key, value, quote_mode='never')
#
#     def get(self):
#         env_data = dotenv.dotenv_values(self.env_path)
#         return env_data
#
#     def write(self):
#         for k, v in self.data.items():
#             dotenv.set_key(self.env_path, k, v, quote_mode='never')
#
#
# dm = DotenvMan()


def run_cmd(cmd: str):
    console.log(cmd, style='magenta')
    os.system(cmd)


context_settings = {"allow_extra_args": True, "ignore_unknown_options": True}


def get_user_group_ids():
    user_id = os.getuid()
    group_id = os.getgid()
    return user_id, group_id


@app.command(context_settings=context_settings)
def build(ctx: typer.Context,
          version: str = typer.Option("latest", '--version', '-v'),
          target='base'):
    dm['PROJECT_NAME'] = project_folder.name
    dm['PROJECT_PATH'] = str(project_folder)
    user_id, group_id = get_user_group_ids()

    cmd_parts = [
        'docker image build',
        f'--build-arg USER_ID={user_id}',
        f'--build-arg GROUP_ID={group_id}',
        f'--build-arg USERNAME={getpass.getuser()}',
        f"--build-arg PROJECT_PATH='{project_folder}'",
        f"--build-arg BASE_IMAGE={dm['BASE_IMAGE']}",
        # f"--build-arg BUILDPLATFORM={dm['BUILDPLATFORM']}",
    ]
    assert target, 'Please specify build target'

    cmd_parts.append(f"--target {target}")
    tag = '-'.join([project_folder.name, target]) + f':{version}'

    dm[f'APP_IMAGE_NAME_{target.upper()}'] = tag
    cmd_parts.append(f'-t {tag}')
    cmd = " ".join(cmd_parts + ctx.args + ['.'])
    run_cmd(cmd)


# @app.command(context_settings=context_settings)
# def run(ctx: typer.Context, command: str = typer.Option('bash', '--command', '--cmd'),
#         display: bool = typer.Option(True)):
#     # cmd = ' '.join([f'docker-compose run -it --rm app'] + ctx.args)
#
#     cmd_parts = ['docker run -it --rm']
#     for v in [dm['PROJECT_PATH'], dm['STORAGE_FOLDER']]:
#         cmd_parts.append(f"-v {v}:{v}")
#     # cmd_parts.append('--device /dev/snd')
#     if display:
#         os.system('xhost +')
#         cmd_parts.append('--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"')
#         cmd_parts.append('--env="DISPLAY"')
#         cmd_parts.append('--env-file ".env"')
#         cmd_parts.append(f'--shm-size=12gb')
#     cmd_parts.extend(ctx.args)
#     cmd_parts.append(f"{dm['APP_IMAGE_NAME_BASE']} {command}")
#     cmd = " ".join(cmd_parts)
#     run_cmd(cmd)

@app.command(context_settings=context_settings)
def run(ctx: typer.Context, command: str = typer.Option('bash', '--command', '--cmd'),
        display: bool = typer.Option(True)):
    # cmd = ' '.join([f'docker-compose run -it --rm app'] + ctx.args)

    cmd_parts = [get_compose_cmd()]
    # for v in [dm['PROJECT_PATH'], dm['STORAGE_FOLDER']]:
    #     cmd_parts.append(f"-v {v}:{v}")
    # cmd_parts.append('--device /dev/snd')
    cmd_parts.append('--env-file ".env"')
    cmd_parts.append('run -i --rm')
    if display:
        os.system('xhost +')
        cmd_parts.append('--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"')
        cmd_parts.append('--env="DISPLAY"')
    cmd_parts.extend(ctx.args)
    cmd_parts.append('app')
    cmd_parts.append(command)
    cmd = " ".join(cmd_parts)
    run_cmd(cmd)


@app.command()
def save_env(file=typer.Option(Path('environment.yaml'))):
    cmd = f'conda env export > {file}'
    run_cmd(cmd)


def resolve_storage_folder():
    if 'STORAGE_FOLDER' in dm.data:
        return dm['STORAGE_FOLDER']


class Resolve:
    def __init__(self, env_key: str):
        self.env_key = env_key

    def __call__(self):
        if self.env_key in dm.data:
            return dm[self.env_key]


class EnvKeys(str, Enum):
    STORAGE_FOLDER = 'STORAGE_FOLDER'
    BASE_IMAGE = 'BASE_IMAGE'
    USER_GROUP = 'USER_GROUP'


@app.command()
def init(
        storage_folder: Path = typer.Option(Resolve(EnvKeys.STORAGE_FOLDER), '--storage-folder', prompt=True),
        base_image: str = typer.Option(Resolve(EnvKeys.BASE_IMAGE), '--base-image', prompt=True),
):
    (storage_folder := storage_folder.resolve()).mkdir(exist_ok=True, parents=True)

    for path in ['.env', '.gitignore', '.dockerignore']:
        Path(path).touch(exist_ok=True)
    dm[EnvKeys.STORAGE_FOLDER] = str(storage_folder)
    dm[EnvKeys.BASE_IMAGE] = base_image
    dm[EnvKeys.USER_GROUP] = ":".join(map(str, get_user_group_ids()))


@app.command()
def exec():
    container_name = dm['PROJECT_NAME']
    cmd = f'docker exec -it {container_name} bash'
    run_cmd(cmd)


def get_compose_cmd():
    docker_compose = 'docker compose'
    if subprocess.run(docker_compose, shell=True, stdout=subprocess.PIPE).returncode:
        docker_compose = 'docker-compose'
    return docker_compose


@app.command(context_settings=context_settings)
def downup(ctx: typer.Context):
    """
    docker compose down + docker compose up with additional user provided args and options.
    """
    docker_compose = get_compose_cmd()
    parts = [
        f'{docker_compose} down -t 3 --remove-orphans &&',
        f'{docker_compose} up',
    ]
    cmd = " ".join(parts + ctx.args)
    run_cmd(cmd)


@app.command()
def generate_proto():
    for proto_file in Path('./protos').rglob('*.proto'):
        parts = [
            'python3 -m grpc_tools.protoc',
            f'--proto_path=.',
            f'--python_out=.',
            f'--grpc_python_out=.',
            str(proto_file),
        ]
        run_cmd(" ".join(parts))


@app.command()
def save_env(filename: Path = typer.Option(Path('env.yaml'), prompt=True)):
    cmd = f'micromamba env export > {filename}'
    run_cmd(cmd)


@app.command()
def install(ctx: typer.Context,
            packages: List[str],
            channel: str = typer.Option('conda-forge', '--channel', '-c'), ):
    cmd = f'micromamba install -c {channel}'
    run_cmd(" ".join([cmd] + ctx.args + packages))


if __name__ == "__main__":
    app()
