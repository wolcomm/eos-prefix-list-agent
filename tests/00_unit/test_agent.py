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
import signal
import time

import pytest

from prefix_list_agent.agent import PrefixListAgent
from prefix_list_agent.exceptions import handle_sigterm, TermException


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
        assert agent.rptk_endpoint == "https://example.com"
        test_value = "https://example.net"
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
        assert agent.refresh_interval == 3600
        test_value = 60
        agent.refresh_interval = test_value
        assert agent.refresh_interval == test_value
        for fail_value in ("x", 5, 100000):
            with pytest.raises(ValueError):
                agent.refresh_interval = fail_value
        assert agent.refresh_interval == test_value

    def test_property_update_delay(self, agent):
        """Test 'update_delay' getter and setter."""
        assert agent.update_delay == 120
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
        assert agent.agent_mgr.agent_option.call_count == 5

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

    def test_success(self, agent, mocker):
        """Test case for 'success' method."""
        for method in ("report", "cleanup", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
        stats = {"foo": "bar"}
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.data = stats
        agent.worker = mock_worker(endpoint=agent.rptk_endpoint,
                                   path=agent.source_dir,
                                   eapi=agent.eapi_mgr)
        agent.success()
        agent.report.assert_called_once_with(**stats)
        agent.cleanup.assert_called_once_with(process=agent.worker)
        agent.sleep.assert_called_once_with()

    @pytest.mark.parametrize("local_err", (None, StandardError("test_error")))
    @pytest.mark.parametrize("worker_process", (True, False))
    @pytest.mark.parametrize("restart", (True, False))
    def test_failure(self, agent, mocker, local_err, worker_process, restart):
        """Test case for 'failure' method."""
        for method in ("err", "restart", "cleanup", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        worker_err = StandardError("worker_err")
        mock_worker.return_value.error = worker_err
        agent.worker = mock_worker(endpoint=agent.rptk_endpoint,
                                   path=agent.source_dir,
                                   eapi=agent.eapi_mgr)
        if worker_process:
            process = agent.worker
        else:
            process = None
        agent.failure(err=local_err, process=process, restart=restart)
        if local_err is None:
            if process is None:
                assert agent.err.call_count == 2
            else:
                agent.err.assert_called_once_with(worker_err)
        else:
            agent.err.assert_called_once_with(local_err)
        if restart:
            agent.restart.assert_called_once_with()
        else:
            agent.cleanup.assert_called_once_with(process=process)
            agent.sleep.assert_called_once_with()

    def test_report(self, agent):
        """Test case for 'report' method."""
        stats = {"foo": 1, "bar": "baz"}
        agent.report(**stats)
        assert agent.agent_mgr.status_set.call_count == len(stats)

    @pytest.mark.parametrize("unwatch_err", ((None,), StandardError()))
    @pytest.mark.parametrize("catch_sigterm", (True, False))
    def test_cleanup(self, agent, worker, mocker, unwatch_err, catch_sigterm):
        """Test case for 'cleanup' method."""
        def run():
            if catch_sigterm:
                signal.signal(signal.SIGTERM, handle_sigterm)
                while True:
                    try:
                        time.sleep(1)
                    except TermException:
                        pass
            else:
                while True:
                    time.sleep(1)
        mocker.patch.object(worker, "run", autospec=True, side_effect=run)
        mocker.patch.object(agent, "unwatch", autospec=True,
                            side_effect=unwatch_err)
        for method in ("err", "notice", "info"):
            mocker.patch.object(agent, method, autospec=True)
        agent.watching.add(worker.p_data)
        agent.watching.add(worker.p_err)
        worker.start()
        agent.cleanup(worker)
        agent.unwatch.assert_any_call(worker.p_data, close=True)
        agent.unwatch.assert_any_call(worker.p_err, close=True)
        assert agent.unwatch.call_count == 2
        if isinstance(unwatch_err, Exception):
            agent.err.assert_called_with(unwatch_err)
            assert agent.err.call_count == 2
        if catch_sigterm:
            agent.notice.assert_called_once_with("Timeout waiting for {}. Sending SIGKILL"  # noqa: E501
                                                 .format(worker.__class__.__name__))  # noqa: E501
        assert 5 <= agent.info.call_count <= 9

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
