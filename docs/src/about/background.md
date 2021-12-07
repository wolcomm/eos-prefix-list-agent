# Background

Internet operators maintain BGP filters at the borders of their networks to
control the propagation of routing information between autonomous systems (ASs).

Such filters are essential to prevent policy violations and outages that occur
when configuration mistakes or intentional hijacks happen.

Unfortunately, construction of correct filters requires special knowledge of
the routing intentions of other operators, with whom there may exist no
operational relationship. Furthermore, the burden of providing and consuming
the necessary data, at Internet scale, without automated processes is
impractical.

The [Internet Routing Registry (IRR)][IRR] system is a distributed and loosely
co-ordinated set of databases in which operators publish data about their
routing intentions, which can then be used to construct filter configurations
by others.

The most common way in which IRR data is used for constructing filters is to
make a "prefix set" representing the prefixes originated in BGP by a
neighboring AS and their customer ASs.

## Off-line filter generation

In [RPSL], the language of the IRR, a set of ASs is represented by an `as-set`
object, and a BGP route by `route` (IPv4) or `route6` (IPv6) objects.

To construct a set of prefixes from an `as-set`, one first queries an IRR
database mirror for the ASNs that are members of the set, and then, for each
member, performs further queries for the `route` and `route6` objects that have
an `origin:` attribute equal to that ASN.

Several open source tools are available to perform this procedure, some of
which are capable of outputting the resulting set directly in the configuration
language of a specific router vendor.

Most commonly this process is performed periodically, and the results are
either deployed directly to the target device, or integrated along with other
configuration snippets into a configuration generation and deployment pipeline.

This methodology has several drawbacks, particularly in an environment where
whole configurations are generated and deployed as a single unit:

-   **Configuration size**: Prefix filters can easily grow to hundreds of
    thousands of entries. Generating and deploying filters as part of a device
    configuration slows down the whole deployment pipeline, and makes unrelated
    configuration changes unnecessarily burdensome.
-   **Timing dependence**: Prefix filters and other configuration elements must
    generated and deployed together. Most device configuration ought to change
    on an irregular schedule, according to the changing intentions of the
    operator. Prefix filters, conversely, are generally updated on a fixed
    regular schedule. Coupling these schedules together increases configuration
    churn and scope for failures.
-   **Rollback dependence**: If an operator wishes to roll back to a previous
    configuration, this will also roll back the *contents* of any prefix
    filters. This is unlikely to be desirable in general.

## Policy-plane separation

Network devices are typically conceive of has having three inter-dependent
"planes", each concerned with a function of the device:

-   The *management plane* provides the means for device management functions
    such login and authentication, configuration database management, and
    statistics collection.
-   The *control plane* provides a host networking stack, on which routing
    protocols and other network services run.
-   The *data plane* provides the packet forwarding functions for network
    traffic traversing the device.

Addressing the above shortcomings of prefix filter maintenance requires a
decoupling of the *presence* of a filter from its *contents*.

Whether a filter for a particular neighbor AS should be present, how and when
it should be updated, and how it should be referenced in other policy
constructs are all concerns of the local device operator, and belong in the
device configuration, i.e. the *management plane*.

The *contents* of a particular IRR-based prefix filter, however, is not
(primarily) determined by the intentions of the local operator, but by the data
that has been published in a remote database by some third party.

This data is a natural part of neither the management nor control planes. Its
existence is determined by the former, and its contents impacts the operation
of the later. However it is best managed independently of either, on a separate
logical *"policy plane"*.

[IRR]: http://www.irr.net/
[RPSL]: http://www.irr.net/docs/rpsl.html
