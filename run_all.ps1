# Build and start all services
docker-compose up --build -d

Write-Output "Services started. You can view logs with:`n docker-compose logs -f"

Write-Output "To trigger clients (client1 runs a few requests then exits). To run client2 in DoS mode, set DOS_MODE=true in docker-compose.yml or run:"
Write-Output "docker run --rm -e FOG_URL=http://fog:5000/ingest -e CLIENT_ID=client2 -e PAYLOAD_SIZE=2048 -e DOS_MODE=true $(docker-compose build --no-cache client2 > $null; docker-compose images | Select-String client2)"
