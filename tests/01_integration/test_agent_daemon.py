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
"""Integration tests for PrefixListAgent."""

from __future__ import print_function

import time

import pytest


NAME = "PrefixListAgent"


@pytest.mark.usefixtures("configure_daemon", "rptk_stub")
class TestPrefixListAgentDaemon(object):
    """Integration test cases for PrefixListAgent."""

    def test_running(self, node):
        """Test that the agent is running."""
        resp = node.enable("show daemon {}".format(NAME))
        status = resp[0]["result"]["daemons"]
        assert NAME in status
        assert status[NAME]["isSdkAgent"]
        assert status[NAME]["enabled"]
        assert status[NAME]["running"]

    # @pytest.mark.usefixtures("configure_prefix_lists")
    def test_prefix_lists(self, node):
        """Test prefix-list creation."""
        time.sleep(15)
        resp = node.enable(["show ip prefix-list", "show ipv6 prefix-list"])
        print(resp)
        resp = node.enable("show daemon {}".format(NAME))
        print(resp)
