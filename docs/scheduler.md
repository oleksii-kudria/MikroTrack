# Scheduler

MikroTrack supports two collection modes controlled via environment variables.

## `RUN_MODE`

Allowed values:

- `once` — run one collection cycle and exit
- `loop` — run continuously with pause between cycles

Default: `once`.

## `COLLECTION_INTERVAL`

Used only in `loop` mode.

- Unit: seconds
- Meaning: delay between the end of the previous cycle and the start of the next one
- Example: `COLLECTION_INTERVAL=60`

## Loop vs once

### Once mode

Use when you need:

- one-shot run (manual check)
- execution from CI/CD or cron with external scheduling

Behavior:

1. connect to MikroTik
2. collect DHCP + ARP
3. build unified model
4. print/log result (depending on settings)
5. exit process

### Loop mode

Use when you need:

- always-on collector container
- internal repeat schedule

Behavior:

1. run collection cycle
2. handle/log possible errors
3. sleep for `COLLECTION_INTERVAL`
4. continue next iteration

This mode is resilient for long-running operation and keeps the collector alive.
