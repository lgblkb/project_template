FROM ubuntu:20.04
MAINTAINER Dias Bakhtiyarov, dbakhtiyarov@nu.edu.kz

ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Almaty \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    VIRTUAL_ENV=/opt/venv \
    SEN2COR_VERSION=2.5.5 \
    SEN2COR_LONG_VERSION=02.05.05 \
    SEN2COR_INSTALLER="Sen2Cor.run" \
    BASEDIR=/sen2cor_old

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    python3.8-dev \
    software-properties-common \
    gdal-bin libgdal-dev \
    swig potrace \
    wget unzip file curl \
    libpq-dev libspatialindex-dev \
    libsm6 libxext6 libxrender-dev ffmpeg libgl1-mesa-dev\
    python3-pip python3-venv &&\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone &&\
    pip3 install poetry taskipy tomlkit dynaconf &&\
    python3 -m venv $VIRTUAL_ENV

RUN pip3 install -U pip wheel setuptools numpy &&\
    pip3 install --global-option=build_ext \
                --global-option="-I/usr/include/gdal" \
                GDAL==$(gdal-config --version)
ENV SEN2COR_DOWNLOAD_URL="http://step.esa.int/thirdparties/sen2cor/${SEN2COR_VERSION}/Sen2Cor-${SEN2COR_LONG_VERSION}-Linux64.run" \
    SEN2COR_PATH_OLD=$BASEDIR/bin/L2A_Process

RUN curl -o ${SEN2COR_INSTALLER} -sSL ${SEN2COR_DOWNLOAD_URL} && \
    bash ${SEN2COR_INSTALLER} --target ${BASEDIR} && \
    rm ${SEN2COR_INSTALLER} && \
    sed -i 's:<Cirrus_Correction>FALSE</Cirrus_Correction>:<Cirrus_Correction>TRUE</Cirrus_Correction>:g' $BASEDIR/$SEN2COR/lib/python2.7/site-packages/sen2cor/cfg/L2A_GIPP.xml

ENV SEN2COR_VERSION=2.8.0 \
    SEN2COR_LONG_VERSION=02.08.00 \
    SEN2COR_DOWNLOAD_HASH=0b61f903d96f24f073390330f1cf9bf958ee62eb8ece8f5c6419718c9ae2b21e \
    SEN2COR_INSTALLER="Sen2Cor.run" \
    BASEDIR=/sen2cor_new

ENV SEN2COR_DOWNLOAD_URL="http://step.esa.int/thirdparties/sen2cor/${SEN2COR_VERSION}/Sen2Cor-${SEN2COR_LONG_VERSION}-Linux64.run" \
    SEN2COR_PATH_NEW=$BASEDIR/bin/L2A_Process

RUN curl -o ${SEN2COR_INSTALLER} -sSL ${SEN2COR_DOWNLOAD_URL} && \
    echo "$SEN2COR_DOWNLOAD_HASH $SEN2COR_INSTALLER" | sha256sum -c - && \
    bash ${SEN2COR_INSTALLER} --target ${BASEDIR} && \
    rm ${SEN2COR_INSTALLER} && \
    sed -i 's:<Cirrus_Correction>FALSE</Cirrus_Correction>:<Cirrus_Correction>TRUE</Cirrus_Correction>:g' $BASEDIR/$SEN2COR/lib/python2.7/site-packages/sen2cor/cfg/L2A_GIPP.xml

#ARG USER_ID
#ARG GROUP_ID
#ARG USERNAME
#ARG PROJECT_DIR
#
#RUN groupadd -g ${GROUP_ID} ${USERNAME} &&\
#    useradd -l -u ${USER_ID} -g ${USERNAME} ${USERNAME} &&\
#    install -d -m 0755 -o ${USERNAME} -g ${USERNAME} /home/${USERNAME} &&\
#    chown --changes --silent --no-dereference --recursive \
#     ${USER_ID}:${GROUP_ID} \
#        /home/${USERNAME} &&\
#    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements_base.txt .
RUN pip3 install --no-cache-dir -r requirements_base.txt
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ansible sshpass && pip3 install ansible && ansible-galaxy install lgblkb.lgblkb_deployer

WORKDIR /app
#USER ${USERNAME}