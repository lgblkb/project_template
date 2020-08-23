import sys
import logging
import subprocess
from subprocess import call

import click

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('lgblkb')


def run_cmd_parts(parts):
    cmd = " ".join(map(str, parts))
    logger.debug("cmd: %s", cmd)
    call(parts)


context_settings = dict(ignore_unknown_options=True, )
vault_parts = ['--vault-password-file', 'provision/.secret', ]


@click.group()
def main():
    pass


# region Main commands:
# region Encrypt/Decrypt:
@main.command(context_settings=context_settings)
@click.option("-i", "--inventory", default="development", show_default=True)
@click.argument('other_args', nargs=-1, type=click.UNPROCESSED)
def encrypt(inventory, other_args):
    encrypt_decrypt('encrypt', inventory, other_args)


@main.command(context_settings=context_settings)
@click.option("-i", "--inventory", default="development", show_default=True)
@click.argument('other_args', nargs=-1, type=click.UNPROCESSED)
def decrypt(inventory, other_args):
    encrypt_decrypt('decrypt', inventory, other_args)


def encrypt_decrypt(action, inventory, other_args):
    parts = ['ansible-vault', action, *vault_parts,
             f'provision/envs/{inventory}/.secrets.yaml',
             *other_args,
             ]
    run_cmd_parts(parts)


# endregion

@main.command(context_settings=context_settings)
@click.argument('playbook')
@click.option("-i", "--inventory", default="development", show_default=True)
@click.option('--vault/--no-vault', default=True, show_default=True)
@click.argument('other_args', nargs=-1, type=click.UNPROCESSED)
def play(playbook, inventory, vault, other_args):
    parts = ['ansible-playbook']
    if vault: parts.extend(vault_parts)
    parts.extend(['--inventory', f'provision/envs/{inventory}'])
    parts.extend([f'provision/{playbook}.yaml', *other_args])
    run_cmd_parts(parts)


# endregion


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def execute2(command):
    subprocess.check_call(command, stdout=sys.stdout, stderr=sys.stderr)


if __name__ == '__main__':
    main()
