# Installation

## EOS Compatibility

Versions from `0.2.0` are compatible with EOS versions `4.26.0F` and above.

To run on an older EOS version (`4.22.0F` and above), select a release from
`0.1.x`.

> Note: the remainder of this documentation is written for the current version.
> Usage details for older versions can be found in the [README] of the GitHub
> repository (at the appropriate tagged commit).

## Download

Packages are available for download from [GitHub Releases].

Versions prior to `0.2.0` were provided as RPM packages. From `0.2.0` onwards
Arista's SWIX packaging format is used.

Ensure that you change the below URLs and file names accordingly.

The installation procedure is the same in either case.

## Extension installation

1.  Copy the SWIX package onto the device.

    ``` eos
    arista-cli# copy https://github.com/wolcomm/eos-prefix-list-agent/releases/download/0.2.0/eos-prefix-list-agent-0.2.0.swix extensions:
    ```

2.  Install the package.

    > Note that the EOS `ConfigAgent` will restart, terminating any existing CLI
    > sessions. You will have to reconnect to the device after this step.

    ``` eos
    arista-cli# extension eos-prefix-list-agent-0.2.0.swix
    ```

3.  (Optional) Persist installation across reloads.

    > If you skip this step, the agent will not be installed after a device
    > reload.

    ``` eos
    arista-cli# copy installed-extensions boot-extensions
    ```

[README]: https://github.com/wolcomm/eos-prefix-list-agent/blob/release/0.1/README.md
[GitHub Releases]: https://github.com/wolcomm/eos-prefix-list-agent/releases
