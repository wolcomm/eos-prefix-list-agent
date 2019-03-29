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
"""Tests for prefix_list_agent.agent module."""

from __future__ import print_function

import datetime

import pytest

from prefix_list_agent.agent import PrefixListAgent


class TestPrefixListAgent(object):
    """Test cases for PrefixListAgent object."""

    def test_set_sysdb_mp(self, sdk):
        """Test case for 'set_sysdb_mp' classmethod."""
        # Should return True on the first call
        assert PrefixListAgent.set_sysdb_mp(sdk.name())
        # Should return False on subsequent calls
        for i in range(3):
            assert not PrefixListAgent.set_sysdb_mp(sdk.name())

    def test_init(self, agent):
        """Test case for PrefixListAgent initialisation."""
        assert isinstance(agent, PrefixListAgent)

    def test_property_rptk_endpoint(self, agent):
        """Test 'rptk_endpoint' getter and setter."""
        assert agent.rptk_endpoint == "https://irr.wolcomm.net"
        test_value = "https://example.com"
        agent.rptk_endpoint = test_value
        assert agent.rptk_endpoint == test_value

    def test_property_source_dir(self, agent):
        """Test 'source_dir' getter and setter."""
        assert agent.source_dir == "/tmp/prefix-lists"
        test_value = "/foo/bar"
        agent.source_dir = test_value
        assert agent.source_dir == test_value

    def test_property_refresh_interval(self, agent):
        """Test 'refresh_interval' getter and setter."""
        assert agent.refresh_interval == 10
        test_value = 60
        agent.refresh_interval = test_value
        assert agent.refresh_interval == test_value
        for fail_value in ("x", 5, 100000):
            with pytest.raises(ValueError):
                agent.refresh_interval = fail_value
        assert agent.refresh_interval == test_value

    def test_property_status(self, agent):
        """Test 'status' getter and setter."""
        assert agent.status is None
        test_value = "test"
        agent.status = test_value
        assert agent.status == test_value

    def test_property_result(self, agent):
        """Test 'result' getter and setter."""
        assert agent.result is None
        test_value = "test"
        agent.result = test_value
        assert agent.result == test_value

    def test_property_timestamps(self, agent):
        """Test 'last_start' and 'last_end' getters and setters."""
        for prop in ("last_start", "last_end"):
            assert getattr(agent, prop) is None
            test_value = datetime.datetime.now()
            setattr(agent, prop, test_value)
            assert getattr(agent, prop) == test_value
            with pytest.raises(TypeError):
                setattr(agent, prop, "foo")
            assert getattr(agent, prop) == test_value

    def test_configure(self, agent):
        """Test 'configure' method."""
        agent.configure()
        agent.agent_mgr.agent_option_iter.assert_called_once()
        assert agent.agent_mgr.agent_option.call_count == 4
