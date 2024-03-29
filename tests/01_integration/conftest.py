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
"""Fixtures for PrefixListAgent integration tests."""

import time

import pytest

from rptk_stub import RptkStubProcess


@pytest.fixture(scope="module")
def node():
    """Provide a pyeapi node connected to the local unix socket."""
    err = None
    for _ in range(60):
        try:
            import pyeapi
            conn = pyeapi.connect(transport="socket")
            node = pyeapi.client.Node(conn)
            assert node.version
            break
        except Exception as e:
            err = e
            time.sleep(3)
            continue
    else:
        raise err
    return node


@pytest.fixture(scope="module")
def configure_daemon(node):
    """Configure the agent as an EOS ProcMgr daemon."""
    agent_config = [
        "trace PrefixListAgent setting PrefixList*/*",
        "prefix-list-agent",
        "rptk-endpoint http://127.0.0.1:8000/",
        "refresh-interval 10",
        "update-delay 1",
        "no disabled",
    ]
    node.config(agent_config)
    time.sleep(3)
    yield


@pytest.fixture(scope="module")
def rptk_stub():
    """Launch a stub version of an rptk web application."""
    process = RptkStubProcess()
    process.start()
    yield
    process.terminate()
    process.join()
