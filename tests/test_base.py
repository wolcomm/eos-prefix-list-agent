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
from __future__ import unicode_literals

import pytest

from prefix_list_agent.base import PrefixListBase


class TestPrefixListAgent(object):
    """Test cases for PrefixListBase object."""

    def test_init(self, sdk, mocker):
        """Test case for PrefixListAgent initialisation."""
        mocker.patch("eossdk.Tracer", autospec=True)
        base = PrefixListBase()
        assert isinstance(base, PrefixListBase)

    @pytest.mark.parametrize("level", ("emerg", "alert", "crit", "err",
                                       "warning", "notice", "info", "debug"))
    def test_tracing(self, mocker, level):
        """Test calls to tracer."""
        mocker.patch("eossdk.Tracer", autospec=True)
        base = PrefixListBase()
        method = getattr(base, level)
        method("message")
        assert base.tracer.trace.call_count == 1
