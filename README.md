# EOS Prefix List Agent

*Automated IRR-based prefix-lists for Arista EOS.*

[![CI/CD](https://github.com/wolcomm/eos-prefix-list-agent/actions/workflows/cicd.yml/badge.svg?event=push)](https://github.com/wolcomm/eos-prefix-list-agent/actions/workflows/cicd.yml)
[![codecov](https://codecov.io/gh/wolcomm/eos-prefix-list-agent/branch/master/graph/badge.svg)](https://codecov.io/gh/wolcomm/eos-prefix-list-agent)

## Overview

The EOS Prefix List Agent is an EOS SDK based agent that runs under `ProcMrg`
on an Arista EOS based device, VM or container.

The agent maintains up-to-date prefix-list policy objects for use in EOS
routing policy configurations, based on data in the IRR.

The agent will periodically check the running configuration of the device to
gather a list of prefix-lists that it is responsible for maintaining. It will
then retrieve the required data from the IRR via an [RPTK] web service, and
update the prefix-lists without calling the EOS config parser.

## Documentation

Installation, configuration and operational documentation is available
[here][docs].

## Contributing

External contributions of all forms are welcomed and appreciated.

Potential contributors are requested to open an issue for discussion prior to
spending time on an implementation.

## Developing

Due to the on-going transition from Python `2.7` to `3` within EOS, this
project contains different Python packages, targeting different interpreter
versions. We hope that this unfortunate complexity will go away in time.

Additionally, the build process and test suite depend on the availability of
an Arista cEOS-lab container image. We cannot currently provide this within the
repository for licensing reasons.

As a result, external contributors are advised to reach out to
[oss@workonline.africa] or via an issue for assistance setting up a working local
development environment.

We apologise for the additional work!

## PyPI Package

Previous versions were provided as Python packages via [PyPI].

Due to changes in the design of the project this installation method is no
longer viable, and new versions are no longer published.

**Users should install via the published SWIX packages, not via `pip`.**

[RPTK]: https://github.com/wolcomm/rptk
[docs]: https://wolcomm.github.io/eos-prefix-list-agent
[PyPI]: https://pypi.python.org/pypi/prefix-list-agent
[oss@workonline.africa]: mailto:oss@workonline.africa
