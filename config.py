from pathlib import Path

from box import Box

settings = Box.from_yaml(filename='settings.yaml').settings


def get_folder(path: str):
    folder = Path(path).joinpath(settings.PROJECT.name)
    folder.mkdir(exist_ok=True)
    return folder


cache_folder = get_folder(settings.PROJECT.dirs.cache_folder)
data_folder = get_folder(settings.PROJECT.dirs.data_folder)
