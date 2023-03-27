FROM mambaorg/micromamba:1.4-bullseye-slim
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml env.yaml
ENV ENV_NAME=the_env
RUN micromamba create --name $ENV_NAME --verbose --yes --file env.yaml && \
    micromamba clean --all --yes

#ARG MAMBA_DOCKERFILE_ACTIVATE=1