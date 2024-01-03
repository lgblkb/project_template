FROM mambaorg/micromamba:latest

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml env.yaml
RUN micromamba install --name base --verbose --yes --file env.yaml && \
    micromamba clean --all --yes

#ARG MAMBA_DOCKERFILE_ACTIVATE=1
#USER root
#RUN apt-get update -yqq && apt-get install -y libssl-dev cmake
#USER $MAMBA_USER