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
"""prefix_list_agent Package."""

import logging
import sys

import eossdk

from .agent import PrefixListAgent

logging.getLogger(__name__).addHandler(logging.NullHandler())


def start(sdk: eossdk.Sdk) -> int:
    """Start the agent."""
    try:
        # create an instance of the agent
        _ = PrefixListAgent(sdk)
        # enter the sdk event-loop
        sdk.main_loop(sys.argv)
    except KeyboardInterrupt:
        return 130
    except Exception:
        raise
    return 0
