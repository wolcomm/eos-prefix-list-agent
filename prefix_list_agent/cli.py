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
"""prefix_list_agent cli entry point."""

from __future__ import print_function

import sys

from prefix_list_agent import PrefixListAgent


def start(sdk):
    """Start the agent."""
    try:
        # create a Sysdb mount profile, restarting if necessary
        if PrefixListAgent.set_sysdb_mp(sdk.name()):
            # return a user defined status to indicate
            # that a restart is desired
            return 64
        # create an instance of the agent
        agent = PrefixListAgent(sdk)  # noqa: W0612
        # enter the sdk event-loop
        sdk.main_loop(sys.argv)
    except KeyboardInterrupt:
        return 130
    except Exception:
        raise
    return
