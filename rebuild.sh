DOCKER_BUILDKIT=1 docker compose build
docker compose down -t 1 --remove-orphans && docker compose "$@"