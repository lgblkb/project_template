from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import Field, BaseSettings, validator


class Config:
    env_file = Path(__file__).parent / '.env'
    env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    project_folder: Path = Field(..., env='PROJECT_DIR')
    storage_folder: Path = Field(..., env='STORAGE_DIR')

    Config = Config

    # noinspection PyMethodParameters
    @validator('project_folder', 'storage_folder')
    def resolve_path(cls, v):
        path = Path(v).resolve()
        assert path.exists()
        return path


settings = Settings(

)

pd.set_option('max_colwidth', 40)
# pd.set_option("display.max_rows", None)
pd.set_option('display.width', None)

np.set_printoptions(threshold=np.inf, linewidth=np.inf)
