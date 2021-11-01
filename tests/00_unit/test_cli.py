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
"""Tests for prefix_list_agent.cli module."""

import sys

import pytest

from prefix_list_agent.agent import PrefixListAgent
from prefix_list_agent.cli import start


class TestCli(object):
    """Test cases for cli module."""

    @staticmethod
    def module_patch(mocker, mod, cls):
        """Patch all superclasses in a given module."""
        for super_cls in cls.mro():
            if super_cls.__module__ == mod:
                mocker.patch("{}.{}".format(mod, super_cls.__name__),
                             autospec=True)

    @pytest.mark.parametrize(("arg", "ret"),
                             ((None, 0), (KeyboardInterrupt, 130),
                              (RuntimeError, RuntimeError)))
    @pytest.mark.parametrize("sysdb_mp_written", (True, False))
    def test_start(self, sdk, mocker, arg, ret, sysdb_mp_written):
        """Test case for cli entrypoint."""
        self.module_patch(mocker, "eossdk", PrefixListAgent)
        mocker.patch.object(PrefixListAgent, "set_sysdb_mp",
                            return_value=sysdb_mp_written)
        sys.argv = arg
        if sysdb_mp_written:
            assert start(sdk) == 64
        else:
            if isinstance(ret, int):
                assert start(sdk) == ret
            else:
                with pytest.raises(ret):
                    start(sdk)
