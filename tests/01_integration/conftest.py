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


def pytest_addoption(parser):
    """Add custom pytest CLI options."""
    parser.addoption("--extension-pkg", action="store")
    parser.addoption("--exec-path", action="store")


@pytest.fixture(scope="session")
def package(request):
    """Get extension package name from CLI args."""
    return request.config.getoption("extension_pkg", default=None)


@pytest.fixture(scope="session")
def exec_path(request):
    """Get exec path from CLI args."""
    return request.config.getoption("exec_path", default="/root/bin")


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
def install_extension(node, package):
    """Install EOS SDK based extension from RPM/SWIX."""
    if package is not None:
        commands = [
            f"copy flash:{package} extension:",
            f"extension {package}",
        ]
        node.run_commands(commands)
        time.sleep(3)
    yield


@pytest.fixture(scope="module")
def configure_daemon(node, install_extension, exec_path):
    """Configure the agent as an EOS ProcMgr daemon."""
    agent_config = [
        "trace PrefixListAgent-PrefixListAgent setting PrefixList*/*",
        "daemon PrefixListAgent",
        f"exec {exec_path}/PrefixListAgent",
        "option rptk_endpoint value http://127.0.0.1:8000/",
        "option refresh_interval value 10",
        "option update_delay value 1",
        "no shutdown",
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
