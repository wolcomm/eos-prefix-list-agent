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

import pytest


NAME = "PrefixListAgent"


@pytest.mark.usefixtures(u"configure")
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
