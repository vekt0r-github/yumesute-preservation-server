# CapRover deployment (fork)

This is an experimental single-instance adaptation. Do not expose the backend or the private setup page publicly. The server's mitmproxy CA is unrelated to CapRover's Let's Encrypt certificates. **Never map ports 80 or 443** from this app.

## Storage

Create these persistent directories on the **game app** before preparing data:

| Container path | Host path |
|---|---|
| `/app/data` | `/mnt/yumesute_preservation_server/yumesute_data` |
| `/app/vendor` | `/mnt/yumesute_preservation_server/yumesute_vendor` |
| `/app/private` | `/mnt/yumesute_preservation_server/yumesute_private` |

`vendor` includes the installed server and media; `private` includes media, local save information, WireGuard private keys, and the trusted CA. Keep these mounts intact through redeploys. Back up secrets and account files before migration.

Use **another CapRover app** for `postgres:17.6`, with `/var/lib/postgresql/data` mounted to `/var/lib/yumesute/postgres` (fast system disk). Choose database/user `yumesute` and a strong database password. Do not publish PostgreSQL to the internet. Ensure the game service can resolve/reach the PostgreSQL service name over the CapRover overlay network (typically `srv-captain--YOUR-POSTGRES-APP`).

## Game app configuration

Deploy the repository via CapRover's GitHub deployment using the `caprover-deployment` branch. The `captain-definition` builds the included Dockerfile.

Environment variables:

- `YUMESUTE_DB_HOST`: resolvable PostgreSQL service hostname on the CapRover network
- `YUMESUTE_DB_PORT`: `5432` (default)
- `YUMESUTE_DB_NAME`: `yumesute` (default)
- `YUMESUTE_DB_USER`: `yumesute` (default)
- `YUMESUTE_DB_PASSWORD`: exact PostgreSQL password
- `YUMESUTE_PUBLIC_HOST`: public IPv4 address or DNS name reachable by the game device
- `YUMESUTE_BIND_HOST`: `0.0.0.0` (default)

Publish only the required ports: `51822/udp` for WireGuard and, if you need certificate download directly, `8766/tcp`. Check the published protocol with `docker service inspect`. Do not publish `8125`: the proxy forwards requests to backend loopback within the container. Do not enable a public CapRover HTTP proxy to `8125`.

**Important:** Docker Swarm ingress UDP plus a WireGuard-based mitmproxy setup is not yet verified end-to-end; check the device handshake and game traffic before treating this as production-ready. The game server is intended for trusted personal devices, not public multi-user hosting.

## First installation

1. Migrate any existing `/app/private` data and `vendor` into the host mounts **before** replacing an old container. Never remove an existing PostgreSQL volume without a backup. Stop writers when copying data.
2. Deploy the app once to create the container and ensure its volume mounts exist. It is expected to fail startup if not prepared.
3. Make sure `/app/data` contains `master-original.db`, `master-manifest.json`, and the collected assets from the project's data preparation procedure. The app does not automatically download the ~45 GB of data.
4. In a shell with the same application mounts and environment variables, run `python caprover.py prepare`. This clones the pinned upstream server into `/app/vendor`, installs media, and configures the **external** PostgreSQL address. **Do not run prepare over an installation containing an account unless you have inspected it and backed it up.**
5. Restart/redeploy the game app. The container starts with `python caprover.py start`. Normal upstream startup creates a fresh starter account only if none exists and the database is ready.
6. Run `python caprover.py doctor` inside the app container to verify preparation and database state.
7. Retrieve `/app/private/iPad.conf` and the setup instructions privately; the QR code and profile contain tunnel credentials. Download `http://YOUR_PUBLIC_HOST:8766/cert.cer` only from a trusted device and verify the CA fingerprint before trusting the certificate.

The upstream `server.py setup` command can download content, while `caprover.py prepare` deliberately requires already-downloaded data. To obtain missing files, use the documented upstream download workflow with the persistent `/app/data` directory, then run prepare.

To make changes on the game container while it is stopped/crash-looping, use a temporary container with the **same mounts and environment**, or use CapRover's instance console if one remains available.

## Existing installations

The entrypoint updates **only** the database section of existing `vendor/server-of-dreams/config.yml` using the CapRover environment variables; it keeps other configuration fields intact. PostgreSQL data itself remains in the separate database service. A copied database directory is **not** equivalent to an SQL backup; for migration, use `pg_dump` and `pg_restore` or stop the old PostgreSQL service before copying a compatible data directory.

This fork changes the WireGuard **bind host** separately from the **public advertised endpoint**. `0.0.0.0` is used inside the container while the WireGuard profile advertises `YUMESUTE_PUBLIC_HOST`.

### Known limitations

- Do not scale the game service past one replica.
- Endpoint routing through Swarm ingress is not confirmed on every hosting provider.
- Setup files reference some LAN-local guidance inherited from upstream.
- Backend logs remain ephemeral under `/app/logs` unless separately persisted.
- The server must be able to fetch the pinned `server-of-dreams` Git repository on first preparation.
