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

import re
import time

import pytest


NAME = "PrefixListAgent"


@pytest.mark.usefixtures("rptk_stub", "configure_daemon")  # noqa: R701
class TestPrefixListAgentDaemon(object):
    """Integration test cases for PrefixListAgent."""

    def test_running(self, node):
        """Test that the agent is running."""
        resp = node.enable(f"show daemon {NAME}")
        status = resp[0]["result"]["daemons"]
        assert NAME in status
        assert status[NAME]["isSdkAgent"]
        assert status[NAME]["enabled"]
        assert status[NAME]["running"]

    def test_prefix_lists(self, node):  # noqa: R701
        """Test prefix-list creation."""
        objects = {
            "AS-FOO": {
                "ipv4": [
                    {"prefix": "192.0.2.0/24", "exact": True},
                ],
                "ipv6": [
                    {"prefix": "2001:db8::/32", "exact": False,
                     "greater-equal": 40, "less-equal": 48},
                ],
            },
            "AS-BAR": {
                "ipv4": [
                    {"prefix": "198.51.100.0/24", "exact": True},
                    {"prefix": "203.0.113.0/24", "exact": True},
                ],
                "ipv6": [],
            },
        }
        time.sleep(15)
        responses = node.enable([f"show {config_af} prefix-list"
                                 for config_af in ("ip", "ipv6")])
        entry_pattern = r"^\s+seq \d+ permit (?P<p>[\w.:/]+)( ge (?P<ge>\d+))?( le (?P<le>\d+))?$"  # noqa: E501
        entry_regexp = re.compile(entry_pattern)
        for obj, data in objects.items():
            for resp in responses:
                assert obj in resp["result"]["ipPrefixLists"]
            for config_af, afi in (("ip", "ipv4"), ("ipv6", "ipv6")):
                resp = node.enable(f"show {config_af} prefix-list {obj} detail",  # noqa: E501
                                   encoding="text")
                output = resp[0]["result"]["output"]
                entries = [m.groupdict() for m in
                           [entry_regexp.match(line)
                            for line in output.splitlines()]
                           if m is not None]
                assert len(entries) == len(data[afi])
                for item in data[afi]:
                    assert item["prefix"] in [e["p"] for e in entries]
                    if not item["exact"]:
                        assert item["less-equal"] in [int(e["le"])
                                                      for e in entries]
                        assert item["greater-equal"] in [int(e["ge"])
                                                         for e in entries]
        status_resp = node.enable(f"show daemon {NAME}")
        status = status_resp[0]["result"]["daemons"]
        assert NAME in status
        assert status[NAME]["data"]["result"] == "ok"
        assert int(status[NAME]["data"]["failed"]) == 0
        assert int(status[NAME]["data"]["succeeded"]) == 4

    def test_show_cli(self, node):
        """Test 'show prefix-list-agent' command."""
        response = node.enable("show prefix-list-agent")
        data = response[0]["result"]
        assert data["enabled"] is True
        assert data["status"]["result"] == "ok"
        assert int(data["status"]["succeeded"]) == 4
        assert int(data["status"]["failed"]) == 0
