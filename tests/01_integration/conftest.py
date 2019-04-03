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

from __future__ import print_function

import time

import pytest


@pytest.fixture(scope="module")
def node():
    """Provide a pyeapi node connected to the local unix socket."""
    for retry in range(60):
        try:
            import pyeapi
            conn = pyeapi.connect(transport="socket")
            node = pyeapi.client.Node(conn)
            assert node.version
            break
        except Exception as e:
            time.sleep(3)
            continue
    else:
        raise e
    return node


@pytest.fixture()
def configure(node):
    """Configure the agent as an EOS ProcMgr daemon."""
    agent_config = [
        "trace PrefixListAgent-PrefixListAgent setting PrefixList*/*",
        "daemon PrefixListAgent",
        "exec /root/bin/PrefixListAgent",
        "option rptk_endpoint value http://localhost:8080/",
        "option refresh_interval value 10",
        "no shutdown"
    ]
    node.config(agent_config)
    time.sleep(3)
    yield
    node.config("no daemon PrefixListAgent")
