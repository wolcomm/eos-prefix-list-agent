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
"""Fixtures for prefix_list_agent test cases."""

import json
import multiprocessing.connection
import unittest.mock

import eossdk

from prefix_list_agent.agent import PrefixListAgent

import pytest


class DummySdk(object):
    """Dummy class to stub-out eossdk interactions in test cases."""

    def __init__(self, **options):
        """Initialise dummy sdk stub."""
        self.options = options
        self.state = dict()

    def name(self):
        """Stub for 'name' method."""
        return "PrefixListAgent"

    def main_loop(self, arg=None):
        """Stub for 'main_loop' method."""
        if arg is not None and issubclass(arg, BaseException):
            raise arg
        return

    def get_agent_mgr(self):
        """Stub for 'get_agent_mgr' method."""
        mgr = unittest.mock.create_autospec(eossdk.AgentMgr)

        def agent_option_exists(key):
            return key in self.options and self.options[key] is not None
        mgr.agent_option_exists.side_effect = agent_option_exists

        def agent_option(key):
            return self.options[key]
        mgr.agent_option.side_effect = agent_option

        def status(key):
            return self.state.get(key)
        mgr.status.side_effect = status

        def status_del(key):
            try:
                del self.state[key]
            except KeyError:
                pass
        mgr.status_del.side_effect = status_del

        def status_set(key, val):
            self.state[key] = val
        mgr.status_set.side_effect = status_set

        return mgr

    def get_timeout_mgr(self):
        """Stub for 'get_timeout_mgr' method."""
        mgr = unittest.mock.create_autospec(eossdk.TimeoutMgr)
        return mgr

    def get_eapi_mgr(self):
        """Stub for 'get_eapi_mgr' method."""
        mgr = unittest.mock.create_autospec(eossdk.EapiMgr)

        def run_show_cmd(cmd):
            if cmd == "error":
                raise RuntimeError
            elif cmd == "fail":
                return eossdk.EapiResponse(False, 255, "synthetic_failure", [])
            elif cmd == "empty":
                result = json.dumps({})
            elif cmd.startswith("refresh"):
                result = json.dumps({"messages": ["Dummy message"]})
            elif cmd.startswith("show"):
                result = json.dumps({"ipPrefixLists": {
                    "AS-FOO": {"ipPrefixListSource": "file:/tmp/prefix-lists/strict/as-foo"},  # noqa: E501
                    "AS-BAR": {},
                    "AS-BAZ": {"ipPrefixListSource": "file:/baz/as-baz"},
                    "AS-QUX": {"ipPrefixListSource": "file:/tmp/prefix-lists/qux/as-qux"},  # noqa: E501
                }})
            else:
                result = json.dumps({"{}_resp".format(cmd): {"foo": "bar"}})
            return eossdk.EapiResponse(True, 0, "", [result])
        mgr.run_show_cmd.side_effect = run_show_cmd

        return mgr


@pytest.fixture(scope="session")
def sdk():
    """Provide an instance of DummySdk to test cases."""
    return DummySdk()


@pytest.fixture(params=({"rptk-endpoint": "https://example.com"},))
def agent(request, mocker):
    """Provide a PrefixListAgent instance with mocked Mgrs."""
    for cls in PrefixListAgent.mro():
        if cls.__module__ == "eossdk":
            mocker.patch("eossdk.{}".format(cls.__name__), autospec=True)
    # opts = getattr(request, "param", {})
    opts = request.param
    sdk = DummySdk(**opts)
    agent = PrefixListAgent(sdk)
    return agent


@pytest.fixture()
def worker(agent):
    """Provide a PrefixListWorker instance from a mocked agent."""
    agent.init_worker()
    return agent.worker


@pytest.fixture()
def connection(mocker):
    """Provide a mocked Connection instance."""
    conn = unittest.mock.create_autospec(multiprocessing.connection.Connection)  # noqa: E501
    return conn
