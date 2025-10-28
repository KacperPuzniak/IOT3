# Fog and Cloud Mini Project Report

1. Architecture diagram and services

- Clients (2 containers): send JSON payloads to Fog node.
- Fog node (Flask): receives payloads, logs metadata to Logging service, processes payloads locally depending on size and forwards parts to Cloud service.
- Cloud node (Flask): stores received parts in SQLite and returns processed results.
- Logging service (Flask + SQLite): receives log entries (ip, size, ts), stores them, and detects DoS-like behavior.

2. Workload simulation

- Threshold used: 1024 bytes.
- If data <= 1024 bytes: processed locally (reversed) and forwarded as a full part to Cloud.
- If data > 1024 bytes: split into two halves; the first half processed locally, the second half forwarded to Cloud for processing.

3. Logging and security monitoring

- Fog node posts events to `logger` with IP, size, timestamp for every request.
- Logger stores logs and raises an alert when a single IP makes more than 20 requests within a 10-second window. Alerts recorded in `alerts` table.

4. DoS attack

- Client2 has a `DOS_MODE` that rapidly sends many requests. During DoS, the logger will record many entries from the attacking client IP and the alerts endpoint will show the generated alert entries.

5. Preventing MITM attacks

- Use TLS for all inter-service communications, mutual TLS if possible, and certificate pinning for clients. Configure services to use HTTPS and validate certificates.
- Use network segmentation and service authentication (JWT or mTLS), and avoid plaintext traffic.

6. Log entries during DoS and mitigation

- During a DoS attempt, the logs table will show a large number of entries with the same IP and small intervals. The alerts table will record an alert entry once the threshold is exceeded.
- Mitigation strategies: rate-limiting at the fog node, IP blocking, connection throttling, introducing a CAPTCHA for human clients, and using upstream network-based DoS protection.

Key snippets and configuration

- docker-compose.yml (orchestrates services)
- fog/app.py (shows ingest logic, logging and forwarding)
- logger/app.py (shows detection rule)

Screenshots and logs: include after running the stack and reproducing the DoS.
