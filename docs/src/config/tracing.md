# Tracing Configuration

Agent execution tracing is provided by EOS's tracing infrastructure.

To enable tracing:

``` eos
arista-cli(conf)# trace PrefixListAgent setting <TRACE_NAME>/<TRACE_LEVEL>
```

Where:

-   `TRACE_NAME`

    The name of the component emitting the trace (usually the module name).

    Wildcard matching is supported using the `*` character.

    To enable tracing for all extension components (but not the EOS SDK
    infrastructure) use `PrefixList*`.

-   `TRACE_LEVEL`

    Each trace is emitted at a "level" indicated by an integer in the range
    `0-9`, with lower levels corresponding to higher importance.

    This setting accepts one of:

    - A single level `N`
    - A range of levels `N-M`
    - A wildcard `*`, matching all levels

The trace can be viewed as described [here](../ops#inspecting-trace-logs).
