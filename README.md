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

## Installation

### From RPM (recommended)

Install the agent as an EOS extension:
```
ar#copy https://github.com/wolcomm/eos-prefix-list-agent/releases/download/0.1.0a8/prefix_list_agent-0.1.0a8-1.noarch.rpm extension:
ar#extension prefix_list_agent-0.1.0a8-1.noarch.rpm
ar#sh extensions
Name                                      Version/Release    Status    Extension
----------------------------------------- ------------------ --------- ---------
prefix_list_agent-0.1.0a8-1.noarch.rpm    0.1.0a8/1          A, I      1


A: available | NA: not available | I: installed | NI: not installed | F: forced
```

Persist the extension to be installed on boot:
```
ar#copy installed-extensions boot-extensions
Copy completed successfully.
ar#sh boot-extensions
prefix_list_agent-0.1.0a8-1.noarch.rpm
```

### Using `pip`

This method is not recommended unless you know what you are doing.
Without additional configuration, the installation will not persist across
reloads.

Drop to the shell:
```
ar#bash
```

Install from PyPI:
```bash
$ sudo pip install prefix-list-agent
```

## Agent Configuration

### Daemon

Configure the agent as an EOS "daemon":
```
ar#conf t
ar(config)#daemon PrefixListAgent
ar(config-daemon-PrefixListAgent)#exec /usr/bin/PrefixListAgent
```

### Tracing

Enable tracing using the EOS agent tracing infrastructure, e.g.:
```
ar(config)#trace PrefixListAgent-PrefixListAgent setting PrefixList*/0-6
```

### Set Configuration Options

Set configuration options using the command:
```
ar(config-daemon-PrefixListAgent)#option <option-name> value <option-value>
```

Available configuration options are:
* `rptk_endpoint` (default: `None`, *required*):

  The RPTK web service endpoint to connect to when retrieving prefix-list data.

* `source_dir` (default: `/tmp/prefix-lists`):

  The local directory to write prefix-list files to.

* `refresh_interval` (default: `3600`):

  The interval between prefix-list updates.

### Start the Agent

```
ar(config-daemon-PrefixListAgent)#no shutdown
```

## Prefix-List Configuration

The PrefixListAgent will check the running configuration for source-based
prefix-lists matching the form:
```
ip[v6] prefix-list ${irr_object} source file:${source_dir}/${policy}/${file_name}
```
Where:

* `${irr_object}`: The IRR object (`aut-num` or `as-set`) to build the
  prefix-list from.
* `${source_dir}`: The configured `source_dir`, as above.
* `${policy}`: The resolution policy to use when resolving the IRR object to a
  prefix-list. Must be a valid policy available on the RPTK web service. You can
  check the available policies with:
```bash
$ curl -q ${rptk_endpoint}/policies | jq
```
* `${file_name}`: The file to write the resulting prefix-list data to. This
  name should be unique per resolution policy.

After the next update, you should be able to see the entries with:
```
ar#show ip[v6] prefix-list ${irr_object} detail
```
