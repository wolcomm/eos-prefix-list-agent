# Installation

## EOS Compatibility

The following table sets out the EOS versions compatible with each minor
release, along with its current maintenance status:

| Agent version | EOS versions            | Support            |
|---------------|-------------------------|--------------------|
| `0.1.x`       | `>= 4.22.0F, < 4.26.0F` | none               |
| `0.2.x`       | `>= 4.26.0F, < 4.28.0F` | none               |
| `1.0.x`       | `>= 4.26.0F, < 4.28.0F` | bug/security fixes |
| `1.1.x`       | `>= 4.28.0F`            | active             |

> Note: the remainder of this documentation is written for versions from
> `0.2.0` onwards.
>
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
