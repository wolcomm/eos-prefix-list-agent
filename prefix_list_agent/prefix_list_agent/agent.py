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
"""prefix_list_agent agent implementation."""

import datetime
import multiprocessing.connection
import os
import signal
import typing

import eossdk

from .base import PrefixListBase
from .exceptions import ConfigValueError
from .types import ConfigVal, StatusVal
from .worker import PrefixListWorker


class PrefixListAgent(PrefixListBase,
                      eossdk.AgentHandler,  # type: ignore[misc]
                      eossdk.TimeoutHandler,  # type: ignore[misc]
                      eossdk.FdHandler):  # type: ignore[misc]
    """An EOS SDK based agent that creates prefix-list policy objects."""

    def __init__(self, sdk: eossdk.Sdk):
        """Initialise the agent instance."""
        # Set up tracing
        PrefixListBase.__init__(self)
        # get sdk managers
        self.agent_mgr = sdk.get_agent_mgr()
        self.timeout_mgr = sdk.get_timeout_mgr()
        self.eapi_mgr = sdk.get_eapi_mgr()
        # init sdk handlers
        eossdk.AgentHandler.__init__(self, self.agent_mgr)
        eossdk.TimeoutHandler.__init__(self, self.timeout_mgr)
        eossdk.FdHandler.__init__(self)
        # set worker process to None
        self._worker: typing.Optional[PrefixListWorker] = None
        self.watching: typing.Set[multiprocessing.connection.Connection] = set()  # noqa: E501

    def option(self,
               typ: typing.Callable[[str], ConfigVal],
               key: str,
               default: ConfigVal) -> ConfigVal:
        """Get configuration option value."""
        if not self.agent_mgr.agent_option_exists(key):
            return default
        return typ(self.agent_mgr.agent_option(key))

    # TODO: 'rptk-endpoint' should not be optional
    @property
    def rptk_endpoint(self) -> typing.Optional[str]:
        """Get 'rptk-endpoint' option."""
        return self.option(str, "rptk-endpoint", None)

    @property
    def source_dir(self) -> str:
        """Get 'source-directory' option."""
        return self.option(str, "source-directory", "/tmp/prefix-lists")  # noqa: S108, E501

    @property
    def refresh_interval(self) -> int:
        """Get 'refresh-interval' option."""
        def validate(s: str) -> int:
            i = int(s)
            if i not in range(10, 86401):
                raise ConfigValueError("refresh-interval must be in range 10 - 86400")  # noqa: E501
            return i
        return self.option(validate, "refresh-interval", 3600)

    @property
    def update_delay(self) -> typing.Optional[int]:
        """Get 'update-delay' option."""
        def validate(s: str) -> int:
            i = int(s)
            if i not in range(1, 121):
                raise ConfigValueError("update-delay must be in range 1 - 120")
            return i
        return self.option(validate, "update-delay", None)

    def status_get(self,
                   typ: typing.Callable[[str], StatusVal],
                   key: str) -> StatusVal:
        """Get agent state key-value-pair."""
        return typ(self.agent_mgr.status(key))

    # TODO: check max key/val lengths (512 char/10KB)
    def status_set(self, key: str, val: typing.Optional[StatusVal]) -> None:
        """Set agent state key-value-pair."""
        if val is None:
            self.debug(f"deleting state key {key}")
            self.agent_mgr.status_del(key)
        else:
            self.debug(f"setting state '{key}' = '{val}'")
            self.agent_mgr.status_set(key, val)

    @property
    def status(self) -> typing.Optional[str]:
        """Get 'status' property."""
        return self.status_get(lambda s: s or None, "status")

    @status.setter
    def status(self, s: str) -> None:
        """Set 'status' property."""
        self.status_set("status", s)
        self.info(f"Status: {s}")

    @property
    def result(self) -> typing.Optional[str]:
        """Get 'result' property."""
        return self.status_get(lambda s: s or None, "result")

    @result.setter
    def result(self, r: str) -> None:
        """Set 'result' property."""
        self.status_set("result", r)
        self.notice(f"Result: {r}")

    @staticmethod
    def timestamp(ts: str) -> typing.Optional[datetime.datetime]:
        """Parse an ISO timestamp."""
        if not ts:
            return None
        return datetime.datetime.fromisoformat(ts)

    @property
    def last_start(self) -> typing.Optional[datetime.datetime]:
        """Set the 'last-start' timestamp."""
        return self.status_get(self.timestamp, "last-start")

    @last_start.setter
    def last_start(self, ts: datetime.datetime) -> None:
        """Set the 'last-start' timestamp."""
        if not isinstance(ts, datetime.datetime):
            raise TypeError(f"expected 'datetime' object, got {ts}")
        self.status_set("last-start", ts.isoformat())
        self.info(f"Last start: {ts}")

    @property
    def last_end(self) -> typing.Optional[datetime.datetime]:
        """Set the 'last-end' timestamp."""
        return self.status_get(self.timestamp, "last-end")

    @last_end.setter
    def last_end(self, ts: datetime.datetime) -> None:
        """Set the 'last-end' timestamp."""
        if not isinstance(ts, datetime.datetime):
            raise TypeError(f"expected 'datetime' object, got {ts}")
        self.status_set("last-end", ts.isoformat())
        self.info(f"Last end: {ts}")

    @property
    def worker(self) -> PrefixListWorker:
        """Get active worker process."""
        if self._worker is None:
            raise RuntimeError("attempted to access uninitialized worker.")
        return self._worker

    def start(self) -> None:
        """Start up the agent."""
        self.status = "init"
        self.init()
        self.run()

    def init(self) -> None:  # pragma: no cover
        """Perform one-time start actions."""
        pass

    def init_worker(self) -> None:
        """Create a worker instance."""
        self.info("Initialising worker")
        assert self.rptk_endpoint is not None  # noqa: S101
        self._worker = PrefixListWorker(rptk_endpoint=self.rptk_endpoint,
                                        source_dir=self.source_dir,
                                        update_delay=self.update_delay,
                                        eapi=self.eapi_mgr)

    def run(self) -> None:
        """Spawn worker process."""
        self.status = "running"
        if self.rptk_endpoint is not None:
            try:
                self.last_start = datetime.datetime.now()
                self.init_worker()
                self.watch(self.worker.p_data, "result")
                self.watch(self.worker.p_err, "error")
                self.info("Starting worker")
                self.worker.start()
                self.info(f"Worker started: pid {self.worker.pid}")
            except Exception as e:
                self.err(f"Starting worker failed: {e}")
                self.failure(err=e)
        else:
            self.warning("'rptk-endpoint' is not set")
            self.sleep()

    def watch(self,
              conn: multiprocessing.connection.Connection,
              typ: str) -> None:
        """Watch a Connection for new data."""
        self.info(f"Trying to watch for {typ} data on {conn}")
        fileno = conn.fileno()
        self.watch_readable(fileno, True)
        self.watching.add(conn)
        self.info(f"Watching {conn} for {typ} data")

    def unwatch(self,
                conn: multiprocessing.connection.Connection,
                close: bool = False) -> None:
        """Stop watching a Connection for new data."""
        self.info(f"Trying to remove watch on {conn}")
        fileno = conn.fileno()
        self.watch_readable(fileno, False)
        if conn in self.watching:
            self.watching.remove(conn)
            self.info(f"Stopped watching {conn}")
        else:
            self.warning(f"Connection {conn} not watched")
        if close:
            self.info(f"Closing connection {conn}")
            conn.close()

    def success(self) -> None:
        """Report statistics and restart refresh_interval timer."""
        self.status = "finalising"
        self.info("Receiving results from worker")
        stats = self.worker.data
        if stats is not None:
            self.report(**stats)
        self.result = "ok"
        self.last_end = datetime.datetime.now()
        self.cleanup(process=self.worker)
        self.sleep()

    def failure(self,
                err: typing.Optional[Exception] = None,
                process: typing.Optional[PrefixListWorker] = None,
                restart: bool = False) -> None:
        """Handle worker exception."""
        self.status = "error"
        if err is None:
            assert process is not None  # noqa: S101
            err = process.error
        self.err(err)
        self.result = "failed"
        self.last_end = datetime.datetime.now()
        if restart:
            self.restart()
        else:
            self.cleanup(process=process)
            self.sleep()

    def report(self, **stats: int) -> None:
        """Report statistics to the agent manager."""
        for name, value in stats.items():
            self.info(f"{name}: {value}")
            self.agent_mgr.status_set(name, str(value))

    def cleanup(self,  # noqa: R701
                process: typing.Optional[PrefixListWorker]) -> None:
        """Kill the process if it is still running."""
        self.status = "cleanup"
        process_name = process.__class__.__name__
        self.info(f"Cleaning up {process_name} process")
        if process is not None:
            self.info(f"Closing connections from {process_name}")
            for conn in [c for c in
                         [getattr(process, k) for k in dir(process)
                          if not k.startswith("_")]
                         if isinstance(c, multiprocessing.connection.Connection)  # noqa: E501
                         and c in self.watching]:
                try:
                    self.unwatch(conn, close=True)
                except Exception as e:
                    self.err(e)
            for retry in range(3):
                if process.is_alive():
                    if retry:
                        self.info(f"Sending {process_name} SIGTERM")
                        process.terminate()
                    timeout = retry * 5 + 1
                    self.info(f"Waiting {timeout} seconds for {process_name} "
                              f"(pid: {process.pid}) to join")
                    process.join(timeout)
            if process.is_alive() and process.pid is not None:
                self.notice(f"Timeout waiting for {process_name}. "
                            "Sending SIGKILL")
                os.kill(process.pid, signal.SIGKILL)
        self.info("Cleanup complete")

    def sleep(self) -> None:
        """Go to sleep for 'refresh_interval' seconds."""
        self.status = "sleeping"
        self.timeout_time_is(eossdk.now() + self.refresh_interval)

    def shutdown(self) -> None:
        """Shutdown the agent gracefully."""
        self.notice("Shutting down")
        try:
            self.cleanup(process=self.worker)
        except Exception as e:
            self.err(e)
        self.status = "shutdown"
        self.agent_mgr.agent_shutdown_complete_is(True)

    def restart(self) -> None:
        """Restart the agent."""
        self.notice("Restarting")
        self.status = "restarting"
        try:
            self.cleanup(process=self.worker)
        except Exception as e:
            self.err(e)
        self.start()

    def on_initialized(self) -> None:
        """Start the agent after initialisation."""
        self.start()

    def on_agent_enabled(self, enabled: bool) -> None:
        """Handle a change in the admin state of the agent."""
        if enabled:
            self.notice("Agent enabled")
        else:
            self.notice("Agent disabled")
            self.shutdown()

    def on_timeout(self) -> None:
        """Handle a 'refresh_interval' timeout."""
        self.run()

    def on_readable(self, fd: int) -> None:
        """Handle a watched file descriptor becoming readable."""
        self.info(f"Watched file descriptor {fd} is readable")
        if fd == self.worker.p_data.fileno():
            self.info("Data channel is ready")
            return self.success()
        elif fd == self.worker.p_err.fileno():
            self.info("Exception received from worker")
            return self.failure(process=self.worker)
        else:
            self.warning("Unknown file descriptor: ignoring")
