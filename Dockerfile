# Use phusion/baseimage as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/baseimage-docker/blob/master/Changelog.md for
# a list of version numbers.
FROM phusion/baseimage:focal-1.1.0 as base
#FROM nvidia/cuda:11.2.0-runtime-ubuntu20.04 as base
#FROM nvcr.io/nvidia/cuda:11.1-devel-ubuntu20.04 as base
MAINTAINER Dias Bakhtiyarov, dbakhtiyarov@nu.edu.kz
# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Almaty \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    PATH=/opt/pdm/bin:$PATH
#    VIRTUAL_ENV=/opt/venv
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ...put your own build instructions here...

RUN apt-get update -y && apt-get upgrade -y

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    nano git tree wget unzip file curl\
    build-essential \
    software-properties-common \
    gdal-bin libgdal-dev \
    swig potrace \
    libpq-dev libspatialindex-dev \
    libsm6 libxext6 libxrender-dev ffmpeg libgl1-mesa-dev \
    libeccodes0 &&\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y && \
    add-apt-repository ppa:deadsnakes/ppa -y &&\
    apt-get install -y\
    python3.10-dev \
    python3.10-venv \
    python3.10-distutils \
    python3.10-gdbm \
    python3.10-tk &&\
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 &&\
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1


#    python3 -m venv $VIRTUAL_ENV &&\
RUN pip install --no-cache-dir -U pip wheel setuptools numpy cython typer[all] &&\
    curl https://rclone.org/install.sh | bash&&\
    curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 - -p /opt/pdm &&\
    pdm --pep582 bash>> ~/.bash_profile &&\
    pdm completion bash > /etc/bash_completion.d/pdm.bash-completion

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM base as builder

ARG USER_ID
ARG GROUP_ID
ARG USERNAME
ARG PROJECT_DIR

RUN groupadd -g ${GROUP_ID} ${USERNAME} &&\
    useradd -l -u ${USER_ID} -g ${USERNAME} ${USERNAME} &&\
    install -d -m 0755 -o ${USERNAME} -g ${USERNAME} /home/${USERNAME} &&\
    chown --changes --silent --no-dereference --recursive \
     ${USER_ID}:${GROUP_ID} \
        /home/${USERNAME}

USER ${USERNAME}
WORKDIR ${PROJECT_DIR}

