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

import StringIO
import urllib2

import pytest

from prefix_list_agent.worker import PrefixListWorker


class TestPrefixListWorker(object):
    """Test cases for the PrefixListWorker object."""

    def test_init(self, worker):
        """Test case for PrefixListWorker initialisation."""
        assert isinstance(worker, PrefixListWorker)

    @pytest.mark.parametrize(("afi", "expect"), (
        ("ipv4", "seq 1 deny 0.0.0.0/0 le 32\n"),
        ("ipv6", "seq 1 deny ::/0 le 128\n"),
        pytest.param("foo", False,
                     marks=pytest.mark.xfail(raises=KeyError))
    ))
    def test_deny_all(self, worker, afi, expect):
        """Test case for 'deny_all' method."""
        line = worker.deny_all(afi)
        assert line == expect

    @pytest.mark.parametrize(("cmd", "allow_empty"), (
        ("test", False),
        ("empty", True),
        pytest.param("empty", False,
                     marks=pytest.mark.xfail(raises=KeyError)),
        pytest.param("fail", False,
                     marks=pytest.mark.xfail(raises=RuntimeError)),
        pytest.param("error", False,
                     marks=pytest.mark.xfail(raises=StandardError))
    ))
    def test_eapi_request(self, worker, cmd, allow_empty):
        """Test case for 'eapi_request' method."""
        result = worker.eapi_request(cmd, "{}_resp".format(cmd), allow_empty)
        if allow_empty:
            assert result == {}
        else:
            assert result["foo"] == "bar"

    @pytest.mark.parametrize("side_effect", (
        (urllib2.addinfourl(url="/testing", code=200, headers=None,
                            fp=StringIO.StringIO('{"foo":"bar"}')),),
        pytest.param(urllib2.URLError(reason="Testing"),
                     marks=pytest.mark.xfail(raises=urllib2.URLError)),
        pytest.param(urllib2.HTTPError(url="/testing", code=500,
                                       msg="Testing", hdrs=None, fp=None),
                     marks=pytest.mark.xfail(raises=urllib2.HTTPError))
    ))
    def test_rptk_request(self, mocker, worker, side_effect):
        """Test case for 'rptk_request' method."""
        mocker.patch.object(urllib2, "urlopen", autospec=True,
                            side_effect=side_effect)
        result = worker.rptk_request("/testing")
        assert result["foo"] == "bar"

    @pytest.mark.parametrize("obj", (
        '{"foo":"bar"}',
        StringIO.StringIO('{"foo":"bar"}'),
        pytest.param("foo",
                     marks=pytest.mark.xfail(raises=ValueError, strict=True)),
        pytest.param(StringIO.StringIO("foo"),
                     marks=pytest.mark.xfail(raises=ValueError, strict=True))
    ))
    def test_json_load(self, worker, obj):
        """Test case for 'json_load' method."""
        result = worker.json_load(obj)
        assert result["foo"] == "bar"
