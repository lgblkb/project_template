# `./lets.py`

**Usage**:

```console
$ ./lets.py [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --verbose`: [default: 0]
* `--version`
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `build`: Build project's docker image
* `play`: Play ansible playbook in provided...
* `run`: Create and enter containerized environment...

## `./lets.py build`

Build project's docker image

**Usage**:

```console
$ ./lets.py build [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `./lets.py play`

Play ansible playbook in provided environment.

**Usage**:

```console
$ ./lets.py play [OPTIONS] [PLAYBOOK_NAME]
```

**Arguments**:

* `[PLAYBOOK_NAME]`: [default: base]

**Options**:

* `-e, --env TEXT`: [default: development]
* `--help`: Show this message and exit.

## `./lets.py run`

Create and enter containerized environment for local development

**Usage**:

```console
$ ./lets.py run [OPTIONS]
```

**Options**:

* `--cmd TEXT`: [default: bash]
* `--display`: [default: False]
* `--gpus`: [default: False]
* `--root`: [default: False]
* `--help`: Show this message and exit.
