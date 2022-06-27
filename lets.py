#!/usr/bin/env python3
import getpass
import os
import subprocess
from enum import Enum
from pathlib import Path

import dotenv
import typer
from loguru import logger

app = typer.Typer()

project_folder = Path(__file__).resolve().parent


class DotenvMan:
    def __init__(self, env_path: Path = Path('.env')):
        self.env_path = env_path
        self.data = self.get()

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value
        dotenv.set_key(self.env_path, key, value)

    def get(self):
        env_data = dotenv.dotenv_values(self.env_path)
        return env_data

    def write(self):
        for k, v in self.data.items():
            dotenv.set_key(self.env_path, k, v)


dm = DotenvMan()


def run_cmd(cmd: str):
    logger.debug("cmd: {}", cmd)
    os.system(cmd)


@app.command()
def build(tag: str = typer.Option(f"{project_folder.name}:latest", '--tag', '-t'), env_name: str = 'development'):
    poetry_version = subprocess.run('poetry --version'.split(' '),
                                    capture_output=True, text=True).stdout.split(' ')[-1]
    dm['PROJECT_NAME'] = project_folder.name
    dm['APP_IMAGE_NAME'] = tag
    dm['PROJECT_PATH'] = str(project_folder)
    cmd = f'docker image build ' \
          f'-t {tag} ' \
          f'--build-arg CUDA_VERSION_TAG={dm[EnvKeys.CUDA_VERSION_TAG]} ' \
          f'--build-arg USER_ID={os.getuid()} ' \
          f'--build-arg GROUP_ID={os.getgid()} ' \
          f'--build-arg USERNAME={getpass.getuser()} ' \
          f"--build-arg PROJECT_PATH='{project_folder}' " \
          f'--build-arg ENV_NAME={env_name} ' \
          f"--build-arg POETRY_VERSION='{poetry_version}' ."
    run_cmd(cmd)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(ctx: typer.Context, command: str = typer.Option('bash', '--command', '--cmd'),
        display: bool = typer.Option(True)):
    # cmd = ' '.join([f'docker-compose run -it --rm app'] + ctx.args)

    cmd_parts = ['docker run -it --rm']
    for v in [dm['PROJECT_PATH'], dm['STORAGE_FOLDER']]:
        cmd_parts.append(f"-v {v}:{v}")
    # cmd_parts.append('--device /dev/snd')
    if display:
        os.system('xhost +')
        cmd_parts.append('--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"')
        cmd_parts.append('--env="DISPLAY"')
    cmd_parts.extend(ctx.args)
    cmd_parts.append(f"{dm['APP_IMAGE_NAME']} {command}")
    cmd = " ".join(cmd_parts)
    run_cmd(cmd)


@app.command()
def save_env(file=typer.Option(Path('environment.yaml'))):
    cmd = f'conda env export > {file}'
    run_cmd(cmd)


@app.command()
def run_jupyter():
    cmd = 'docker-compose up jupyter_server && docker-compose rm -fsv'
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


def resolve_cuda_version():
    if 'CUDA_VERSION_TAG' in dm.data:
        return dm['CUDA_VERSION_TAG']


class EnvKeys(str, Enum):
    STORAGE_FOLDER = 'STORAGE_FOLDER'
    CUDA_VERSION_TAG = 'CUDA_VERSION_TAG'


@app.command()
def init(storage_folder: Path = typer.Option(Resolve(EnvKeys.STORAGE_FOLDER), '--storage-folder', prompt=True),
         cuda_version: str = typer.Option(Resolve(EnvKeys.CUDA_VERSION_TAG), '--cuda-version', prompt=True)):
    (storage_folder := storage_folder.resolve()).mkdir(exist_ok=True, parents=True)

    for path in ['.env', '.gitignore', '.dockerignore']:
        Path(path).touch(exist_ok=True)

    dm[EnvKeys.STORAGE_FOLDER] = str(storage_folder)
    dm[EnvKeys.CUDA_VERSION_TAG] = cuda_version.strip()


if __name__ == "__main__":
    app()
