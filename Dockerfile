FROM mambaorg/micromamba:1-bullseye-slim
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml conda-lock.yml
ENV ENV_NAME=the_env
RUN --mount=type=cache,target=/home/$MAMBA_USER/.mamba/pkgs \
    micromamba create --name $ENV_NAME --verbose --yes --file conda-lock.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /project