# Agent Configuration

The EOS Prefix List Agent is configured via a custom CLI extension providing
the `prefix-list-agent` configuration sub-mode.

The legacy `daemon` CLI syntax should still work, but is unsupported and
untested as of `0.2.0`.

## Synopsis

``` eos
prefix-list-agent
   [no] disabled                #  Enable/disable the agent (default: disabled)
   rptk-endpoint <URL>          #  RPTK Web API endpoint URL (required)
   source-directory <PATH>      #  Filesystem path to write to (default: /tmp/prefix-lists)
   refresh-interval <10-86400>  #  Seconds between update runs (default: 3600)
   update-delay <1-120>         #  Optional delay between prefix-list refreshes (default: none)
```

## Command Reference

### `[no] disabled`

Control whether the agent is enabled or disabled, i.e. should be started by
EOS `ProcMgr`.

The agent is disabled by default. Configure `no disabled` to start it.

Default: `disabled`

### `rptk-endpoint <URL>`

The URL of an instance of the [RPTK] Web API service.

The agent does not communicate directly with an IRR mirror using the `tcp/43`
protocol(s). Instead an instance of [RPTK] is used to resolve IRR object names
to prefix sets.

The option is required in order for the agent to function. If it is not
provided then the agent when an update run begins then an error is logged, and
the agent restarts its `refresh-interval` timer and waits for the next run.

Default: none (required)

### `source-directory <PATH>`

The path on the local filesystem to the directory where the agent should write
the contents of prefix-lists.

The default path is on a `tmpfs` filesystem, meaning that the contents of the
prefix-lists will not persist across reloads. To change this behaviour,
configure a directory path on a filesystem that is backed by a real block
device (e.g. `/mnt/flash` or `/mnt/disk`).

Default: `/tmp/prefix-lists`

### `refresh-interval <10-86400>`

The interval (in seconds) between prefix list contents update runs.

The timer is reset at the *end* of each run, so the interval excludes however
much time is taken to perform the update itself. Similarly, and change in the
configuration will take effect at the end of the next (currently scheduled)
run.

Default: `3600`

### `update-delay <1-120>`

Tell EOS to re-read the prefix-list content sources one-at-a-time, and
introduce a delay (in seconds) between each.

When not configured, all prefix-lists are re-read simultaneously. On affected
EOS versions, bug [578037] can cause the `IsIs` and/or `Ospf` agents to crash
if the prefix-lists being managed are large enough. Using `update-delay` can
dampen the effect and avoid this issue.

Default: `none`

[RPTK]: https://github.com/wolcomm/rptk
[578037]: https://www.arista.com/en/support/software-bug-portal/bugdetail?bug_id=578037
