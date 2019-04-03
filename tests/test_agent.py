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

    @pytest.mark.parametrize(("key", "value"), (
        ("rptk_endpoint", "https://x.com"),
        ("source_dir", "/foo/bar"),
        ("refresh_interval", 60),
        ("bad_option", None)
    ))
    def test_set(self, agent, mocker, key, value):
        """Test case for 'set' method."""
        mocker.patch.object(agent, "warning", autospec=True)
        agent.set(key, value)
        if key in agent.agent_options:
            assert getattr(agent, key) == value
        else:
            agent.warning.assert_called_once_with("Ignoring unknown option '{}'"  # noqa: E501
                                                  .format(key))

    def test_start(self, agent, mocker):
        """Test case for 'start' method."""
        methods = ("configure", "init", "run")
        for method in methods:
            mocker.patch.object(agent, method, autospec=True)
        agent.start()
        for method in methods:
            getattr(agent, method).assert_called_once_with()

    @pytest.mark.parametrize("side_effect", ((None,), StandardError()))
    @pytest.mark.parametrize("rptk_endpoint", ("https://example.com", None))
    def test_run(self, agent, worker, mocker, side_effect, rptk_endpoint):
        """Test case for 'run' method."""
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.start.side_effect = side_effect
        for method in ("watch", "failure", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
        agent.rptk_endpoint = rptk_endpoint
        agent.run()
        if agent.rptk_endpoint is None:
            agent.sleep.assert_called_once_with()
        else:
            assert agent.watch.call_count == 2
            agent.worker.start.assert_called_once_with()
            if issubclass(type(side_effect), Exception):
                assert agent.failure.call_count == 1

    def test_watch(self, agent, mocker, connection):
        """Test case for 'watch' method."""
        mocker.patch.object(agent, "watch_readable")
        agent.watch(connection, "test")
        agent.watch_readable.assert_called_once_with(connection.fileno(), True)
        assert connection in agent.watching

    @pytest.mark.parametrize("close", (True, False))
    def test_unwatch(self, agent, mocker, connection, close):
        """Test case for 'unwatch' method."""
        mocker.patch.object(agent, "watch_readable")
        agent.watching.add(connection)
        agent.unwatch(connection, close=close)
        agent.watch_readable.assert_called_once_with(connection.fileno(),
                                                     False)
        if close:
            connection.close.assert_called_once_with()

    def test_sleep(self, agent, mocker):
        """Test case for 'sleep' method."""
        mocker.patch("eossdk.now", autospec=True, return_value=0)
        mocker.patch.object(agent, "timeout_time_is")
        agent.sleep()
        agent.timeout_time_is.assert_called_once_with(agent.refresh_interval)

    @pytest.mark.parametrize("side_effect", ((None,), StandardError))
    def test_shutdown(self, agent, mocker, side_effect):
        """Test case for 'shutdown' method."""
        mocker.patch.object(agent, "cleanup", autospec=True,
                            side_effect=side_effect)
        agent.shutdown()
        agent.cleanup.assert_called_once_with(process=agent.worker)
        agent.agent_mgr.agent_shutdown_complete_is.assert_called_once_with(True)  # noqa: E501

    @pytest.mark.parametrize("side_effect", ((None,), StandardError))
    def test_restart(self, agent, mocker, side_effect):
        """Test case for 'restart' method."""
        mocker.patch.object(agent, "cleanup", autospec=True,
                            side_effect=side_effect)
        mocker.patch.object(agent, "start", autospec=True)
        agent.restart()
        agent.cleanup.assert_called_once_with(process=agent.worker)
        agent.start.assert_called_once_with()

    def test_on_initialized(self, agent, mocker):
        """Test case for 'on_initialized' method."""
        mocker.patch.object(agent, "start", autospec=True)
        agent.on_initialized()
        agent.start.assert_called_once_with()

    def test_on_agent_option(self, agent, mocker):
        """Test case for 'on_agent_option' method."""
        mocker.patch.object(agent, "set", autospec=True)
        agent.on_agent_option("foo", "bar")
        agent.set.assert_called_once_with("foo", "bar")

    @pytest.mark.parametrize("enabled", (True, False))
    def test_on_agent_enabled(self, agent, mocker, enabled):
        """Test case for 'on_agent_enabled' method."""
        mocker.patch.object(agent, "notice", autospec=True)
        mocker.patch.object(agent, "shutdown", autospec=True)
        agent.on_agent_enabled(enabled)
        assert agent.notice.call_count == 1
        if not enabled:
            agent.shutdown.assert_called_once_with()

    def test_on_timeout(self, agent, mocker):
        """Test case for 'on_timeout' method."""
        mocker.patch.object(agent, "run", autospec=True)
        agent.on_timeout()
        agent.run.assert_called_once_with()

    @pytest.mark.parametrize("fd", (1, 2, 3))
    def test_on_readable(self, agent, mocker, fd):
        """Test case for 'on_readable' method."""
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.p_data.fileno.return_value = 1
        mock_worker.return_value.p_err.fileno.return_value = 2
        for method in ("success", "failure", "warning"):
            mocker.patch.object(agent, method, autospec=True)
        agent.worker = mock_worker(endpoint=agent.rptk_endpoint,
                                   path=agent.source_dir,
                                   eapi=agent.eapi_mgr)
        agent.on_readable(fd)
        if fd == 1:
            agent.success.assert_called_once_with()
        elif fd == 2:
            agent.failure.assert_called_once_with(process=agent.worker)
        else:
            agent.warning.assert_called_once_with("Unknown file descriptor: ignoring")  # noqa: E501
