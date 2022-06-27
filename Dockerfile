ARG CUDA_VERSION_TAG
FROM nvidia/cuda:${CUDA_VERSION_TAG}-devel-ubuntu20.04
FROM python:3.10.5-buster

MAINTAINER Dias Bakhtiyarov dbakhtiyarov@nu.edu.kz

RUN apt-get update -yqq && apt-get upgrade -y

ARG ENV_NAME
ARG USERNAME
ARG USER_ID
ARG GROUP_ID
ARG PROJECT_PATH

ENV HOME=/home/${USERNAME}\
    ENV_NAME=${ENV_NAME} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Almaty \
    PATH=/home/${USERNAME}/.local/bin:$PATH \
    POETRY_VIRTUALENVS_CREATE=false


RUN apt-get update -yqq && apt-get install -y \
    software-properties-common \
    curl wget file tree unzip \
    gcc


RUN mkdir -p ${PROJECT_PATH} &&\
    groupadd -g ${GROUP_ID} ${USERNAME} &&\
    useradd --create-home --shell /bin/bash ${USERNAME}  \
    --gid ${GROUP_ID} --uid ${USER_ID} --home-dir ${HOME} &&\
    install --directory --mode=0755 --owner=${USERNAME} --group=${USERNAME} ${HOME} &&\
    chown --changes --silent --no-dereference --recursive \
    ${USER_ID}:${GROUP_ID} \
    ${HOME}
#RUN apt-get update -yqq && apt-get install -y \
#    git
USER ${USERNAME}


RUN curl -sSL https://install.python-poetry.org | python3 -
COPY poetry.lock pyproject.toml ./

RUN poetry install
#RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113 &&\
#    pip install dgl-cu113 dglgo -f https://data.dgl.ai/wheels/repo.html

#RUN pip install pytorch-lightning
WORKDIR ${PROJECT_PATH}

