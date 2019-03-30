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

import json
import StringIO
import urllib2

import pytest

from prefix_list_agent.exceptions import TermException
from prefix_list_agent.worker import PrefixListWorker


class TestPrefixListWorker(object):
    """Test cases for the PrefixListWorker object."""

    def test_init(self, worker):
        """Test case for PrefixListWorker initialisation."""
        assert isinstance(worker, PrefixListWorker)

    @pytest.mark.parametrize(("case", "side_effect"), (
        ("success", ({"foo": "bar"},)),
        ("sigterm", TermException),
        ("error", StandardError),
    ))
    def test_run(self, worker, mocker, case, side_effect):
        """Test case for 'run' method."""
        for method in ("get_policies", "get_configured", "get_data",
                       "refresh_all", "notice"):
            mocker.patch.object(worker, method)
        mocker.patch.object(worker, "write_results", side_effect=side_effect)
        worker.run()
        if case == "success":
            assert worker.data == {"foo": "bar"}
        elif case == "sigterm":
            worker.notice.assert_called_once_with("Got SIGTERM signal: exiting.")  # noqa: E501
        elif case == "error":
            assert type(worker.error) is StandardError
        else:
            raise ValueError(case)

    def test_get_configured(self, worker):
        """Test case for 'test_get_configured' method."""
        configured = worker.get_configured(["strict"])
        expect = {"strict": {"AS-FOO": {"ipv4": "as-foo",
                                        "ipv6": "as-foo"}}}
        assert worker.eapi.run_show_cmd.call_count == 2
        assert configured == expect

    def test_refresh_all(self, worker):
        """Test case for 'refrech_all' method."""
        worker.refresh_all()
        assert worker.eapi.run_show_cmd.call_count == 2

    def test_get_policies(self, worker, mocker):
        """Test case for 'get_policies' method."""
        resp_data = {"strict": "strict descr", "loose": "loose descr"}
        resp_fp = StringIO.StringIO(json.dumps(resp_data))
        return_value = urllib2.addinfourl(url="/testing", code=200,
                                          headers=None, fp=resp_fp)
        mocker.patch.object(urllib2, "urlopen", autospec=True,
                            return_value=return_value)
        policies = worker.get_policies()
        assert policies == resp_data

    def test_get_data(self, worker, mocker):
        """Test case for 'get_data' method."""
        configured = {"strict": {"AS-FOO": {"ipv4": "as-foo-4",
                                            "ipv6": "as-foo-6"},
                                 "AS-BAR": {"ipv4": "as-bar-4",
                                            "ipv6": "as-bar-6"}},
                      "loose":  {"AS-BAZ": {"ipv4": "as-baz-4",
                                            "ipv6": "as-baz-6"},
                                 "AS-QUX": {"ipv4": "as-qux-4",
                                            "ipv6": "as-qux-6"}},
                      "empty":  {}}
        data = {"strict": {"AS-FOO": {"ipv4": [], "ipv6": []},
                           "AS-BAR": {"ipv4": [], "ipv6": []}},
                "loose":  {"AS-BAZ": {"ipv4": [], "ipv6": []}}}
        mocker.patch.object(worker, "get_data_bulk", autospec=True,
                            side_effect=(data["strict"], StandardError))
        mocker.patch.object(worker, "get_data_obj", autospec=True,
                            side_effect=(data["loose"], StandardError))
        result = worker.get_data(configured)
        assert result == data
        assert worker.get_data_bulk.call_count == 2
        assert worker.get_data_obj.call_count == 2

    def test_get_data_bulk(self, worker, mocker):
        """Test case for 'get_data_obj' method."""
        policy = "strict"
        objs = ["AS-FOO", "AS-BAR"]
        resp_data = {obj: {"ipv4": [], "ipv6": []} for obj in objs}
        resp_fp = StringIO.StringIO(json.dumps(resp_data))
        return_value = urllib2.addinfourl(url="/testing", code=200,
                                          headers=None, fp=resp_fp)
        mocker.patch.object(urllib2, "urlopen", autospec=True,
                            return_value=return_value)
        result = worker.get_data_bulk(policy, objs)
        assert result == resp_data

    def test_get_data_obj(self, worker, mocker):
        """Test case for 'get_data_obj' method."""
        policy = "strict"
        obj = "AS-FOO"
        resp_data = {obj: {"ipv4": [], "ipv6": []}}
        resp_fp = StringIO.StringIO(json.dumps(resp_data))
        return_value = urllib2.addinfourl(url="/testing", code=200,
                                          headers=None, fp=resp_fp)
        mocker.patch.object(urllib2, "urlopen", autospec=True,
                            return_value=return_value)
        result = worker.get_data_obj(policy, obj)
        assert result == resp_data

    @pytest.mark.parametrize(("configured", "data"), (
        ({"strict": {"AS-FOO": {"ipv4": "as-foo-4", "ipv6": "as-foo-6"},
                     "AS-BAR": {"ipv4": "as-bar-4", "ipv6": "as-bar-6"}},
          "empty": {}},
         {"strict": {"AS-FOO": {"ipv4": [{"prefix": "192.0.2.0/24",
                                          "exact": True}],
                                "ipv6": [{"prefix": "2001:db8::/32",
                                          "exact": True}]}}}),
    ))
    def test_write_results(self, worker, mocker, configured, data):
        """Test case for 'write_results' method."""
        mocker.patch("__builtin__.open", mocker.mock_open())
        stats = worker.write_results(configured, data)
        assert stats["succeeded"] == 2
        assert stats["failed"] == 2

    @pytest.mark.parametrize(("entries", "side_effect"), (
        ([], None),
        ([{"prefix": "2001:db8:b00::/48", "exact": True},
         {"prefix": "2001:db8:f00::/48", "exact": True}], None),
        pytest.param([], IOError, marks=pytest.mark.xfail(raises=IOError))
    ))
    def test_write_prefix_list(self, worker, mocker, entries, side_effect):
        """Test case for 'write_prefix_list' method."""
        m = mocker.patch("__builtin__.open", mocker.mock_open())
        m.side_effect = side_effect
        path = "/tmp/foo"
        worker.write_prefix_list(path, entries, "ipv6")
        m.assert_called_once_with(path, "w")
        assert m().write.call_count == max(len(entries), 1)

    @pytest.mark.parametrize(("entry", "expect"), (
        ({"prefix": "10.0.0.0/8", "exact": True}, "seq 1 permit 10.0.0.0/8\n"),
        ({"prefix": "2001:db8::/32", "exact": False,
          "greater-equal": 48, "less-equal": 64},
         "seq 1 permit 2001:db8::/32 ge 48 le 64\n")
    ))
    def test_prefix_list_line(self, worker, entry, expect):
        """Test case for 'prefix_list_line' method."""
        line = worker.prefix_list_line(0, entry)
        assert line == expect

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

    def test_property_data(self, worker):
        """Test case for 'data' property."""
        assert worker.data is None
        send_data = {"foo": "bar"}
        worker.c_data.send(send_data)
        recv_data = worker.data
        assert recv_data == send_data

    def test_property_error(self, worker):
        """Test case for 'error' property."""
        assert worker.error is None
        send_error = Exception()
        worker.c_err.send(send_error)
        recv_error = worker.error
        assert (type(recv_error) is type(send_error) and
                recv_error.args == send_error.args)
