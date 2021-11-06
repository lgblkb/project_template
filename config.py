from pathlib import Path

from box import Box

settings = Box.from_yaml(filename='settings.yaml').settings

cache_folder = Path(settings.PROJECT.dirs.cache_folder)
data_folder = Path(settings.PROJECT.dirs.data_folder)
