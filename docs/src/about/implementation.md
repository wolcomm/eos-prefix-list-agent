# Implementation

Arista EOS provides the ability to have the contents of `prefix-list`s and
`as-path access-list`s retrieved dynamically from an arbitrary URL.

This feature allows the presence of the policy object and the source of its
contents defined in the `running-configuration`, whilst omitting the contents.

The [EOS SDK] provides the ability to run third party extension code under
the EOS process manager, in order that the extension can be configured via the
EOS `running-configuration`, and can register callbacks against events
occurring in the main event loop.

The agent is configured to periodically inspect the current
`running-configuration` for `prefix-list` objects with a `source` that matches
a well defined pattern.

For each such object, the agent will execute the necessary queries to write the
entries in the `prefix-list` to the file system, and instruct EOS to reload
their contents.

The agent does not query an IRR database server directly, but relies on the
availability of an instance of [RPTK] to provide an easy-to-consume JSON based
API.

[EOS SDK]: https://github.com/aristanetworks/EosSdk
[RPTK]: https://github.com/wolcomm/rptk
