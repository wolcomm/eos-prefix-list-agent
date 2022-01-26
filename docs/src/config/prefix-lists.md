# Prefix List Configuration

The EOS Prefix List Agent leverages the standard EOS source based prefix-list
feature, which allows the configuration of `prefix-list` objects whose contents
are to be retrieved from a URL, rather than enumerated in the
`running-configuration`.

To determine which prefix-lists it should attempt to construct using IRR data,
the agent attempts to match the `source` URL of all configured source-based
`prefix-list` objects against a well defined pattern.

To configure a `prefix-list` to be managed by the agent:

``` eos
ip[v6] prefix-list <IRR_OBJECT> source file:<SOURCE_DIR>/<POLICY>/<FILE_NAME>
```

Where:

-   `IRR_OBJECT`

    The IRR object (`aut-num` or `as-set`) to build the prefix-list from.

-   `SOURCE_DIR`

    The configured agent [`source-directory`](agent.md#source-directory-path).

-   `POLICY`

    The resolution policy to use when resolving the IRR object to a
    prefix-list.

    This must be a valid resolution policy available on the [RPTK] web service.

    The available policies can be checked with:

    ``` bash
    $ curl -q ${rptk_endpoint}/policies | jq
    {
      "strict": "Permit only prefixes with explicitly registered 'route' or 'route6' objects",
      "loose": "Permit prefixes shorter than /24 (ipv4) or /48 (ipv6) with a registered covering 'route' or 'route6' object"
    }
    ```

-   `FILE_NAME`

    The file to write the resulting prefix-list data to.

    The actual name is unimportant, but must be unique per resolution policy.

    The recommended convention is `<IRR_OBJECT>-<ipv4|ipv6>.txt`.

[RPTK]: https://github.com/wolcomm/rptk
