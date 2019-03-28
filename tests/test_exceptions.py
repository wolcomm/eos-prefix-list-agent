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
"""Tests for prefix_list_agent.exceptions module."""

from __future__ import print_function
from __future__ import unicode_literals

import signal

import pytest

from prefix_list_agent.exceptions import TermException, handle_sigterm


class TestExceptions(object):
    """Test cases for exceptions module."""

    def test_term(self):
        """Test case for SIGTERM signal handler."""
        with pytest.raises(TermException):
            handle_sigterm(signal.SIGTERM, None)
