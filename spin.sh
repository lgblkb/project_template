DOCKER_BUILDKIT=1 docker compose build
docker compose down --remove-orphans && docker compose "$@"