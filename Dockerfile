#FROM phusion/baseimage:focal-1.0.0alpha1-amd64 as base
FROM nvidia/cuda:11.0-runtime-ubuntu20.04 as base
#FROM nvcr.io/nvidia/cuda:11.1-devel-ubuntu20.04 as base
MAINTAINER Dias Bakhtiyarov, dbakhtiyarov@nu.edu.kz

ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Almaty \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    VIRTUAL_ENV=/opt/venv

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    nano git\
    build-essential \
    python3.8-dev \
    software-properties-common \
    gdal-bin libgdal-dev \
    swig potrace \
    wget unzip file curl \
    libpq-dev libspatialindex-dev \
    libsm6 libxext6 libxrender-dev ffmpeg libgl1-mesa-dev \
    libeccodes0 \
    python3-pip python3-venv &&\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    python3 -m venv $VIRTUAL_ENV &&\
    pip3 install --no-cache-dir -U pip wheel setuptools numpy &&\
    pip3 install --no-cache-dir -U poetry taskipy &&\
    pip3 install --global-option=build_ext \
                --global-option="-I/usr/include/gdal" \
                GDAL==$(gdal-config --version) &&\
    curl https://rclone.org/install.sh | bash &&\
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

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

COPY requirements_base.txt .
RUN pip3 install --no-cache-dir -r requirements_base.txt
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

USER ${USERNAME}

FROM base as production
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

