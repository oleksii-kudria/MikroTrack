# Troubleshooting

## connection refused

Symptoms:

- cannot connect to `MIKROTIK_HOST:MIKROTIK_PORT`
- socket error with "connection refused"

Checks:

- MikroTik service `api-ssl` is enabled
- port is correct (default `8729`)
- firewall allows inbound connection from collector host
- IP allow-list on MikroTik service includes collector address

## ssl error

Symptoms:

- TLS handshake failure
- certificate verify failed

Checks:

- `MIKROTIK_USE_SSL=true`
- MikroTik has certificate assigned to `api-ssl`
- if using self-signed certificate, set `MIKROTIK_SSL_VERIFY=false` or trust CA properly
- router date/time are correct (important for certificate validation)

## authentication failed

Symptoms:

- login rejected
- authentication error in logs

Checks:

- `MIKROTIK_USERNAME` and `MIKROTIK_PASSWORD` are correct
- account is not disabled
- user has enough policy rights (`read`, `api`)

## not allowed (9)

Symptoms:

- RouterOS API returns `not allowed (9)`

Root cause:

- user lacks permissions for requested path/command

Fix:

- verify group policies include at least `read,api`
- avoid using over-restricted custom group
- test command access directly in RouterOS terminal
