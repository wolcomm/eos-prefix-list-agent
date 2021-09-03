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

from __future__ import print_function

import json

import mock
import pytest

import eossdk

from _multiprocessing import Connection

from prefix_list_agent.agent import PrefixListAgent
from prefix_list_agent.worker import PrefixListWorker


class DummySdk(object):
    """Dummy class to stub-out eossdk interactions in test cases."""

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
        mgr = mock.create_autospec(eossdk.AgentMgr)

        test_options = {"rptk_endpoint": "https://example.com",
                        "source_dir": "/foo/bar",
                        "refresh_interval": 60,
                        # "update_delay": None,
                        "bad_option": None}

        def agent_option_iter():
            return test_options.keys()
        mgr.agent_option_iter.side_effect = agent_option_iter

        def agent_option(key):
            return test_options[key]
        mgr.agent_option.side_effect = agent_option

        return mgr

    def get_timeout_mgr(self):
        """Stub for 'get_timeout_mgr' method."""
        mgr = mock.create_autospec(eossdk.TimeoutMgr)
        return mgr

    def get_eapi_mgr(self):
        """Stub for 'get_eapi_mgr' method."""
        mgr = mock.create_autospec(eossdk.EapiMgr)

        def run_show_cmd(cmd):
            if cmd == "error":
                raise StandardError
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
                    "AS-QUX": {"ipPrefixListSource": "file:/tmp/prefix-lists/qux/as-qux"}  # noqa: E501
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


@pytest.fixture()
def agent(sdk, mocker):
    """Provide a PrefixListAgent instance with mocked Mgrs."""
    for cls in PrefixListAgent.mro():
        if cls.__module__ == "eossdk":
            mocker.patch("eossdk.{}".format(cls.__name__), autospec=True)
    agent = PrefixListAgent(sdk)
    agent.rptk_endpoint = "https://example.com"
    return agent


@pytest.fixture()
def worker(agent):
    """Provide a PrefixListWorker instance from a mocked agent."""
    worker = PrefixListWorker(endpoint=agent.rptk_endpoint,
                              path=agent.source_dir,
                              eapi=agent.eapi_mgr)
    return worker


@pytest.fixture()
def connection(mocker):
    """Provide a mocked Connection instance."""
    conn = mock.create_autospec(Connection)
    return conn
