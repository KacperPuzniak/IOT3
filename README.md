# Fog vs Cloud Mini Project

This project demonstrates a simple fog/cloud architecture using Docker Compose. It includes:

- two client containers that send payloads to a fog node
- a fog node that processes payloads, logs events, and forwards parts to a cloud node
- a cloud node that stores processed parts in SQLite
- a logging service that records incoming IPs, request sizes, and detects DoS-like behavior

Run the stack with Docker Compose (Windows PowerShell):

```powershell
docker-compose up --build -d
```

To run the DoS mode for client2, set environment variable DOS_MODE=true in the `docker-compose.yml` for service `client2` or run the container with:

```powershell
docker-compose run --rm -e DOS_MODE=true client2
```

To run the client with a specific payload size, set the variable PAYLOAD_SIZE="" in the client file, or run the container with:

```powershell
docker-compose run --rm -e PAYLOAD_SIZE=500 client1
```

or

```powershell
docker-compose run --rm -e PAYLOAD_SIZE=3000 client2
```

This variable can also be set for the DoS mode:

```powershell
docker-compose run --rm -e PAYLOAD_SIZE=3000 -e DOS_MODE=true client2
```

Services:

Watch fog logs

```powershell
docker-compose logs -f fog
```

Watch logger service output

```powershell
docker-compose logs -f logger
```

- fog: http://localhost:5000/ingest
- cloud: http://localhost:5001/process (GET /parts to list stored parts)
- logger: http://localhost:5002/log (POST logs), /logs and /alerts for lists
