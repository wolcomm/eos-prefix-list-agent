# Operations

## Inspecting Agent Status

### `show prefix-list-agent`

Display the operational state and configuration of the agent.

### `show daemon PrefixListAgent`

> This command is not provided by the extension, and may change or be removed
> without notice in future versions.

Display the internal operational state of the EOS SDK daemon process.

This command may be used to view details that are not visible via the `show
prefix-list-agent` command, such as uptime and PID.

## Inspecting `prefix-list` contents

### `show ip[v6] prefix-list <IRR_OBJECT> <summary|detail>`

The contents of source-based prefix-lists are not shown in the output of the
unqualified `show ip[v6] prefix-list` command.

Instead, use either `summary` or `detail` as follows:

-   `summary`

    Show the number of entries and the last update time of the `prefix-list`

-   `detail`

    Show the full contents of the `prefix-list`

An error of the form `Failed to import from source: file:<PATH>` indicates that
the source file could not be read, possibly because the agent has not yet
processed a newly added `prefix-list`, or due to some other problem.

## Inspecting trace logs

### `show agent PrefixListAgent logs`

Inspect the contents of the agent trace log file if [agent tracing has been
configured](../config/tracing.md).

Alternatively, the trace files can be found in `/var/log/agent/`.
