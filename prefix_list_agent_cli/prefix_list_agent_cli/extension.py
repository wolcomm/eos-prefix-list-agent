# Copyright (c) 2019 Workonline Communications (Pty) Ltd. All rights reserved.
#
# The contents of this file are licensed under the MIT License
# (the "License"); you may not use this file except in compliance with the
# License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""PrefixListAgent CLI plugin handlers."""

from typing import Any, Dict, Optional, Text

import CliExtension


class ShowPrefixListAgent(CliExtension.ShowCommandClass):  # type: ignore[misc]
    """Handlers for `show prefix-list-agent` command."""

    def handler(self, ctx):
        # type: (Any) -> Optional[Dict[Text, Any]]
        """Handle `show prefix-list-agent` command."""
        daemon = ctx.getDaemon("PrefixListAgent")
        if daemon is None:
            ctx.addError("Unable to get daemon info")
            return None
        result = {"enabled": daemon.config.isEnabled(),
                  "config": {key: value for key, value
                             in daemon.config.configIter()},
                  "status": {key: value for key, value
                             in daemon.status.statusIter()}}
        return result

    def render(self, data):
        # type: (Dict[Text, Any]) -> None
        """Render `show prefix-list-agent` command output."""
        print(data)


class PrefixListAgentCfgDisabled(CliExtension.CliCommandClass):  # type: ignore[misc]  # noqa: E501
    """Handlers for `[no] disabled` commands."""

    def handler(self, ctx):
        # type: (Any) -> None
        """Handle `disabled` command."""
        ctx.daemon.config.disable()

    def noHandler(self, ctx):  # noqa: N802
        # type: (Any) -> None
        """Handle `no disabled` command."""
        ctx.daemon.config.enable()


class PrefixListAgentCfg(CliExtension.CliCommandClass):  # type: ignore[misc]
    """Base configuration command handler."""

    option_key = None  # type: Text
    arg_key = None  # type: Text

    def handler(self, ctx):
        # type: (Any) -> None
        """Handle configuration command."""
        value = ctx.args[self.arg_key]
        ctx.daemon.config.configSet(self.option_key, value)


class PrefixListAgentCfgNullable(PrefixListAgentCfg):
    """Base nullable configuration command handler."""

    def noHandler(self, ctx):  # noqa: N802
        # type: (Any) -> None
        """Handle `no ...` configuration command."""
        ctx.daemon.config.configDel(self.option_key)


class PrefixListAgentCfgEndpoint(PrefixListAgentCfgNullable):
    """Handlers for `[no] rptk-endpoint <url>` command."""

    option_key = "rptk-endpoint"
    arg_key = "<url>"


class PrefixListAgentCfgSrcDir(PrefixListAgentCfg):
    """Handlers for `source-directory <path>` command."""

    option_key = "source-directory"
    arg_key = "<path>"


class PrefixListAgentCfgInterval(PrefixListAgentCfg):
    """Handlers for `refresh-interval <int>` command."""

    option_key = "refresh-interval"
    arg_key = "<int>"


class PrefixListAgentCfgDelay(PrefixListAgentCfgNullable):
    """Handlers for `[no] update-delay <int>` command."""

    option_key = "update-delay"
    arg_key = "<int>"


def Plugin(ctx):  # noqa: N802
    # type: (Any) -> None
    """Initialise CLI plugin."""
    CliExtension.registerCommand("show_prefix_list_agent", ShowPrefixListAgent)
    CliExtension.registerCommand("cfg_prefix_list_agent_disabled",
                                 PrefixListAgentCfgDisabled)
    CliExtension.registerCommand("cfg_prefix_list_agent_endpoint",
                                 PrefixListAgentCfgEndpoint)
    CliExtension.registerCommand("cfg_prefix_list_agent_source_dir",
                                 PrefixListAgentCfgSrcDir)
    CliExtension.registerCommand("cfg_prefix_list_agent_interval",
                                 PrefixListAgentCfgInterval)
    CliExtension.registerCommand("cfg_prefix_list_agent_delay",
                                 PrefixListAgentCfgDelay)
