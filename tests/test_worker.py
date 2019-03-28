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
"""Tests for prefix_list_agent.worker module."""

from __future__ import print_function
from __future__ import unicode_literals

from prefix_list_agent.worker import PrefixListWorker


class TestPrefixListWorker(object):
    """Test cases for the PrefixListWorker object."""

    def test_init(self, worker):
        """Test case for PrefixListWorker initialisation."""
        assert isinstance(worker, PrefixListWorker)
