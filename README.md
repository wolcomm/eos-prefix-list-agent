<!--description: An EOS agent to dynamically update IRR based prefix-lists -->
[![PyPI](https://img.shields.io/pypi/v/prefix-list-agent.svg)](https://pypi.python.org/pypi/prefix-list-agent)
[![Build Status](https://travis-ci.com/wolcomm/eos-prefix-list-agent.svg?branch=master)](https://travis-ci.com/wolcomm/eos-prefix-list-agent)
[![codecov](https://codecov.io/gh/wolcomm/eos-prefix-list-agent/branch/master/graph/badge.svg)](https://codecov.io/gh/wolcomm/eos-prefix-list-agent)

# Prefix-list Agent for Arista EOS

Periodically retrieve data from the IRR and build prefix-list objects on EOS.

## Overview

The `PrefixListAgent` is an EOS SDK based agent that runs under `ProcMrg` on an
Arista EOS based device or VM.

The agent maintains up-to-date prefix-list policy objects for use in EOS
routing policy configurations, based on data in the IRR.

The agent will periodically check the running configuration of the device to
gather a list of prefix-lists that it is responsible for maintaining. It will
then retrieve the required data from the IRR via an RPTK web service, and
update the prefix-lists without calling the EOS config parser.
