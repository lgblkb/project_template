import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from pandas.errors import ParserWarning
from pydantic import Field, field_validator, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class HostPort(BaseModel):
    host: str
    port: int


class UserPass(BaseModel):
    username: str
    password: str


class DB(HostPort, UserPass):
    name: str

    def get_url(self, engine_name: str = 'asyncpg'):
        return ('postgresql+{engine_name}://'
                '{username}:{password}@'
                '{host}:{port}/{name}').format(
            **self.model_dump(),
            engine_name=engine_name,
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name('.env'),
        env_file_encoding='utf-8',
        extra='ignore',
        env_nested_delimiter='_',
    )
    project_folder: Path = Field(alias='PROJECT_DIR')
    storage_folder: Path = Field(alias='STORAGE_DIR')

    # noinspection PyMethodParameters
    @field_validator('project_folder', 'storage_folder')
    def check_folder(cls, v):
        assert v.exists()
        return v


settings = Settings()

pd.set_option('max_colwidth', 40)
# pd.set_option("display.max_rows", None)
pd.set_option('display.width', None)
warnings.filterwarnings("ignore", category=ParserWarning)
np.set_printoptions(threshold=np.inf, linewidth=np.inf)

logger.remove()
logger.add(sys.stdout, colorize=True, format="{level.icon}|<level>{message}</level>")
