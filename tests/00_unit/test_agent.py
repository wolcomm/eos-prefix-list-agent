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

import datetime
import signal
import time

from prefix_list_agent.agent import PrefixListAgent
from prefix_list_agent.exceptions import (ConfigValueError, TermException,
                                          handle_sigterm)

import pytest


class TestPrefixListAgent(object):
    """Test cases for PrefixListAgent object."""

    def test_init(self, agent):
        """Test case for PrefixListAgent initialisation."""
        assert isinstance(agent, PrefixListAgent)

    # def test_property_rptk_endpoint(self, agent):
    #     """Test 'rptk_endpoint' getter and setter."""
    #     assert agent.rptk_endpoint == "https://example.com"
    #     test_value = "https://example.net"
    #     agent.rptk_endpoint = test_value
    #     assert agent.rptk_endpoint == test_value

    # def test_property_source_dir(self, agent):
    #     """Test 'source_dir' getter and setter."""
    #     assert agent.source_dir == "/tmp/prefix-lists"  # noqa: S108
    #     test_value = "/foo/bar"
    #     agent.source_dir = test_value
    #     assert agent.source_dir == test_value

    @pytest.mark.parametrize(("agent", "value"),
                             (({}, 3600),
                              ({"refresh-interval": 60}, 60),
                              pytest.param({"refresh-interval": 86500}, None,
                                  marks=pytest.mark.xfail(raises=ConfigValueError))),  # noqa: E501
                             indirect=("agent",))
    def test_property_refresh_interval(self, agent, value):
        """Test 'refresh_interval' getter."""
        assert agent.refresh_interval == value

    @pytest.mark.parametrize(("agent", "value"),
                             (({}, None),
                              ({"update-delay": 10}, 10),
                              pytest.param({"update-delay": 0}, None,
                                  marks=pytest.mark.xfail(raises=ConfigValueError))),  # noqa: E501
                             indirect=("agent",))
    def test_property_update_delay(self, agent, value):
        """Test 'update_delay' getter."""
        assert agent.update_delay == value

    def test_property_status(self, agent):
        """Test 'status' getter and setter."""
        assert agent.status is None
        test_value = "test"
        agent.status = test_value
        assert agent.status == test_value
        agent.status = None
        assert agent.status is None

    def test_property_result(self, agent):
        """Test 'result' getter and setter."""
        assert agent.result is None
        test_value = "test"
        agent.result = test_value
        assert agent.result == test_value
        agent.result = None
        assert agent.result is None

    @pytest.mark.parametrize("prop", ("last_start", "last_end"))
    def test_property_timestamps(self, agent, prop):
        """Test 'last_start' and 'last_end' getters and setters."""
        assert getattr(agent, prop) is None
        test_value = datetime.datetime.now()
        setattr(agent, prop, test_value)
        assert getattr(agent, prop) == test_value
        with pytest.raises(TypeError):
            setattr(agent, prop, "foo")
        assert getattr(agent, prop) == test_value

    def test_init_worker(self, agent):
        """Test case for `init_worker` method."""
        agent.init_worker()
        assert agent.rptk_endpoint == agent.worker.rptk_endpoint
        assert agent.source_dir == agent.worker.source_dir
        assert agent.update_delay == agent.worker.update_delay

    def test_start(self, agent, mocker):
        """Test case for 'start' method."""
        methods = ("init", "run")
        for method in methods:
            mocker.patch.object(agent, method, autospec=True)
        agent.start()
        for method in methods:
            getattr(agent, method).assert_called_once_with()

    @pytest.mark.parametrize("side_effect", ((None,), RuntimeError()))
    @pytest.mark.parametrize("agent",
                             ({}, {"rptk-endpoint": "https://example.com"}),
                             indirect=True)
    def test_run(self, agent, mocker, side_effect):
        """Test case for 'run' method."""
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.start.side_effect = side_effect
        for method in ("watch", "failure", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
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

    @pytest.mark.parametrize("watching", (True, False))
    @pytest.mark.parametrize("close", (True, False))
    def test_unwatch(self, agent, mocker, connection, watching, close):
        """Test case for 'unwatch' method."""
        mocker.patch.object(agent, "watch_readable")
        mocker.patch.object(agent, "warning")
        if watching:
            agent.watching.add(connection)
        agent.unwatch(connection, close=close)
        agent.watch_readable.assert_called_once_with(connection.fileno(),
                                                     False)
        if not watching:
            agent.warning.assert_called_once()
        if close:
            connection.close.assert_called_once_with()

    @pytest.mark.parametrize("stats", ({"foo": "bar"}, None))
    def test_success(self, agent, mocker, stats):
        """Test case for 'success' method."""
        for method in ("report", "cleanup", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.data = stats
        agent._worker = mock_worker(rptk_endpoint=agent.rptk_endpoint,
                                    source_dir=agent.source_dir,
                                    update_delay=agent.update_delay,
                                    eapi=agent.eapi_mgr)
        agent.success()
        if stats is not None:
            agent.report.assert_called_once_with(**stats)
        agent.cleanup.assert_called_once_with(process=agent.worker)
        agent.sleep.assert_called_once_with()

    @pytest.mark.parametrize("local_err", (None, RuntimeError("test_error")))
    @pytest.mark.parametrize("worker_err", (None, RuntimeError("worker_err")))
    @pytest.mark.parametrize("worker_process", (True, False))
    @pytest.mark.parametrize("restart", (True, False))
    def test_failure(self, agent, mocker, local_err, worker_err,
                     worker_process, restart):
        """Test case for 'failure' method."""
        for method in ("err", "restart", "cleanup", "sleep"):
            mocker.patch.object(agent, method, autospec=True)
        mock_worker = mocker.patch("prefix_list_agent.agent.PrefixListWorker",
                                   autospec=True)
        mock_worker.return_value.error = worker_err
        agent._worker = mock_worker(rptk_endpoint=agent.rptk_endpoint,
                                    source_dir=agent.source_dir,
                                    update_delay=agent.update_delay,
                                    eapi=agent.eapi_mgr)
        if worker_process:
            process = agent.worker
        else:
            process = None
            if local_err is None:
                pytest.xfail()
        agent.failure(err=local_err, process=process, restart=restart)
        if local_err is None:
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

    @pytest.mark.parametrize("unwatch_err", ((None,), RuntimeError()))
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

    def test_cleanup_noop(self, agent, mocker):
        """Test case for noop-'cleanup'."""
        for method in ("err", "notice", "info"):
            mocker.patch.object(agent, method, autospec=True)
        agent.cleanup(None)
        assert agent.info.call_count == 3

    def test_sleep(self, agent, mocker):
        """Test case for 'sleep' method."""
        mocker.patch("eossdk.now", autospec=True, return_value=0)
        mocker.patch.object(agent, "timeout_time_is")
        agent.sleep()
        agent.timeout_time_is.assert_called_once_with(agent.refresh_interval)

    @pytest.mark.parametrize("side_effect", ((None,), RuntimeError))
    @pytest.mark.parametrize("init_worker", (True, False))
    def test_shutdown(self, agent, mocker, side_effect, init_worker):
        """Test case for 'shutdown' method."""
        mocker.patch.object(agent, "cleanup", autospec=True,
                            side_effect=side_effect)
        if init_worker:
            agent.init_worker()
        agent.shutdown()
        if init_worker:
            agent.cleanup.assert_called_once()
        agent.agent_mgr.agent_shutdown_complete_is.assert_called_once_with(True)  # noqa: E501

    @pytest.mark.parametrize("side_effect", ((None,), RuntimeError))
    @pytest.mark.parametrize("init_worker", (True, False))
    def test_restart(self, agent, mocker, side_effect, init_worker):
        """Test case for 'restart' method."""
        mocker.patch.object(agent, "cleanup", autospec=True,
                            side_effect=side_effect)
        mocker.patch.object(agent, "start", autospec=True)
        if init_worker:
            agent.init_worker()
        agent.restart()
        if init_worker:
            agent.cleanup.assert_called_once()
        agent.start.assert_called_once_with()

    def test_on_initialized(self, agent, mocker):
        """Test case for 'on_initialized' method."""
        mocker.patch.object(agent, "start", autospec=True)
        agent.on_initialized()
        agent.start.assert_called_once_with()

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
        agent._worker = mock_worker(rptk_endpoint=agent.rptk_endpoint,
                                    source_dir=agent.source_dir,
                                    update_delay=agent.update_delay,
                                    eapi=agent.eapi_mgr)
        agent.on_readable(fd)
        if fd == 1:
            agent.success.assert_called_once_with()
        elif fd == 2:
            agent.failure.assert_called_once_with(process=agent.worker)
        else:
            agent.warning.assert_called_once_with("Unknown file descriptor: ignoring")  # noqa: E501
