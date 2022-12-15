DOCKER_BUILDKIT=1 docker compose build
docker compose down -t 1 && docker compose up --remove-orphans -d