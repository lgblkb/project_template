source .env
echo
echo "Running in $ENV_NAME mode..."
echo
cmd="docker compose -f docker-compose.yaml"
if [ "$ENV_NAME" == "prod" ]; then
  cmd="$cmd -f docker-compose.prod.yaml"
fi
#echo "$cmd"
eval "$cmd" "$@"
