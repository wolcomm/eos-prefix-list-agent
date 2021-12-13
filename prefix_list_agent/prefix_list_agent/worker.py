# Copyright (c) 2019 Ben Maddison. All rights reserved.
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
"""prefix_list_agent worker functions."""

import collections
import json
import multiprocessing
import multiprocessing.connection
import os
import re
import signal
import sys
import time
import typing
import urllib.error
import urllib.request

import eossdk

from .base import PrefixListBase
from .exceptions import TermException, handle_sigterm
from .types import (Configured, Data, EapiResponse, Objects, Policies,
                    RptkPrefixEntries, RptkPrefixEntry, RptkPrefixes,
                    RptkResult, Stats)

PATH_RE = r"^file:{}/(?P<policy>\w+)/(?P<file>[-.:\w]+)$"


class PrefixListWorker(multiprocessing.Process, PrefixListBase):
    """Worker to fetch and process IRR data."""

    def __init__(self,
                 endpoint: str,
                 path: str,
                 eapi: eossdk.EapiMgr,
                 update_delay: typing.Optional[int],
                 *args: typing.Any,
                 **kwargs: typing.Any) -> None:
        """Initialise an PrefixListWorker instance."""
        super(PrefixListWorker, self).__init__(*args, **kwargs)
        PrefixListBase.__init__(self)
        self.endpoint = endpoint
        self.path = path
        self.eapi = eapi
        self.update_delay = update_delay
        self.path_re = re.compile(PATH_RE.format(self.path.rstrip("/")))
        self._p_err, self._c_err = multiprocessing.Pipe(duplex=False)
        self._p_data, self._c_data = multiprocessing.Pipe(duplex=False)

    @property
    def p_err(self) -> multiprocessing.connection.Connection:
        """Get 'p_err' connection."""
        return self._p_err

    @property
    def c_err(self) -> multiprocessing.connection.Connection:
        """Get 'c_err' connection."""
        return self._c_err

    @property
    def p_data(self) -> multiprocessing.connection.Connection:
        """Get 'p_data' connection."""
        return self._p_data

    @property
    def c_data(self) -> multiprocessing.connection.Connection:
        """Get 'c_data' connection."""
        return self._c_data

    def run(self) -> None:
        """Run the worker process."""
        self.info("Worker started")
        signal.signal(signal.SIGTERM, handle_sigterm)
        try:
            policies = self.get_policies()
            configured = self.get_configured(policies)
            data = self.get_data(configured)
            stats, written_objs = self.write_results(configured, data)
            self.refresh_all(written_objs)
            self.c_data.send(stats)
        except TermException:
            self.notice("Got SIGTERM signal: exiting.")
            if os.getpid() == self.pid:
                sys.exit(127 + signal.SIGTERM)
        except Exception as e:
            self.err(e)
            try:
                self.c_err.send(e)
            except TypeError:  # pragma: no cover
                self.c_err.send(Exception(str(e)))
        finally:
            self.c_err.close()
            self.c_data.close()

    def get_configured(self, policies: Policies) -> Configured:
        """Get the prefix-lists in running-config."""
        configured: Configured = {p: collections.defaultdict(dict)
                                  for p in policies}
        self.info("Searching for prefix-lists with "
                  f"source matching {self.path_re.pattern}")
        for afi, cmd in (("ipv4", "show ip prefix-list"),
                         ("ipv6", "show ipv6 prefix-list")):
            data = self.eapi_request(cmd, result_node="ipPrefixLists")
            self.debug(f"Got response: {data}")
            for name, config in data.items():
                try:
                    source = config["ipPrefixListSource"]
                except KeyError:
                    continue
                self.debug(f"Testing {name}, source {source}")
                m = self.path_re.match(source)
                if m:
                    self.debug("Source matched")
                    (policy, file) = m.groups()
                    if policy in policies:
                        configured[policy][name][afi] = file
                    else:
                        self.warning(f"Ignoring unknown policy {policy}")
                else:
                    self.debug("No match")
        return configured

    def refresh_prefix_list(self,
                            afi: str,
                            prefix_list: typing.Optional[str] = None) -> None:
        """Refresh all prefix-lists or a single named prefix-list."""
        cmd = f"refresh {afi} prefix-list"
        if prefix_list is not None:
            cmd += f" {prefix_list}"
        messages = self.eapi_request(cmd, result_node="messages",
                                     allow_empty=True)
        for msg in messages:
            for submsg in msg.replace("\nNum", " -").rstrip().split("\n"):
                self.info(submsg)

    def refresh_all(self, written_objs: typing.Iterable[str]) -> None:
        """Refresh prefix-lists."""
        self.info("Refreshing source-based prefix-lists")
        for afi in ("ip", "ipv6"):
            if self.update_delay is None:
                self.refresh_prefix_list(afi)
            else:
                for prefix_list in written_objs:
                    self.refresh_prefix_list(afi, prefix_list)
                    time.sleep(self.update_delay)
        self.notice("Prefix-lists refreshed successfully")

    def get_policies(self) -> Policies:
        """Get the list of valid policy names from RPTK."""
        url_path = "/policies"
        self.info(f"Trying to get policy data from {url_path}")
        policies = self.rptk_request(url_path)
        self.debug(f"Got policies: {policies.keys()}")
        return typing.cast(Policies, policies)

    def get_data(self, configured: Configured) -> Data:
        """Get IRR data for the configured prefix-list objects."""
        data = dict()
        self.info("Querying for IRR data")
        for policy, objs in configured.items():
            if not objs:
                continue
            self.info("Trying bulk query")
            try:
                result = self.get_data_bulk(policy, objs)
                data.update({policy: result})
                continue
            except Exception as e:
                self.err(e)
            self.info("Failing back to indiviual queries")
            data[policy] = dict()
            for obj in objs:
                try:
                    result = self.get_data_obj(policy, obj)
                except Exception as e:
                    self.err(e)
                    continue
                data[policy].update(result)
        return data

    def get_data_bulk(self,
                      policy: str,
                      objs: typing.Iterable[str]) -> RptkPrefixes:
        """Get IRR data in bulk."""
        url_path = f"/json/query?policy={policy}&" + \
                   "&".join([f"objects={obj}" for obj in objs])
        self.info(f"Trying to get prefix data from {url_path}")
        result = self.rptk_request(url_path)
        self.debug("Got prefix data")
        return typing.cast(RptkPrefixes, result)

    def get_data_obj(self, policy: str, obj: str) -> RptkPrefixes:
        """Get IRR data for a single object."""
        url_path = f"/json/{obj}/{policy}"
        self.info(f"Trying to get prefix data from {url_path}")
        result = self.rptk_request(url_path)
        self.debug("Got prefix data")
        return typing.cast(RptkPrefixes, result)

    def write_results(self,
                      configured: Configured,
                      data: Data) -> typing.Tuple[Stats, Objects]:
        """Write prefix-list data to files."""
        stats = {"succeeded": 0, "failed": 0}
        written_objs = set()
        for policy, objs in configured.items():
            self.info(f"Writing files for policy {policy}")
            if not objs:
                self.info(f"No objects with policy: {policy}")
                continue
            policy_dir = os.path.join(self.path, policy)
            if not os.path.isdir(policy_dir):
                self.info(f"Creating directory {policy_dir}")
                os.makedirs(policy_dir)
            for obj, config in objs.items():
                self.info(f"Trying to write files for {obj}/{policy}")
                if obj in data[policy]:
                    for afi, file in config.items():
                        path = os.path.join(policy_dir, file)
                        entries = data[policy][obj][afi]
                        try:
                            self.write_prefix_list(path, entries, afi)
                        except Exception:  # pragma: no cover
                            stats["failed"] += 1
                            continue
                        stats["succeeded"] += 1
                        written_objs.add(obj)
                else:
                    self.warning(f"No prefix data for {obj}/{policy}")
                    stats["failed"] += len(config)
        return stats, written_objs

    def write_prefix_list(self,
                          path: str,
                          entries: RptkPrefixEntries,
                          afi: str) -> None:
        """Write prefix-list to file."""
        self.info(f"Trying to write {path}")
        try:
            with open(path, "w") as f:
                for i, p in enumerate(entries):
                    f.write(self.prefix_list_line(i, p))
        except Exception as e:
            self.err(f"Failed to write {path}: {e}")
            raise e

    def prefix_list_line(self, index: int, entry: RptkPrefixEntry) -> str:
        """Generate a line in a prefix-list."""
        line = "seq {} permit {}".format(index + 1, entry["prefix"])
        if not entry["exact"]:
            if "greater-equal" in entry:
                line += " ge {}".format(entry["greater-equal"])
            if "less-equal" in entry:
                line += " le {}".format(entry["less-equal"])
        line += "\n"
        return line

    def eapi_request(self,
                     cmd: str,
                     result_node: str,
                     allow_empty: bool = False) -> EapiResponse:
        """Get call an enable-mode eAPI command."""
        self.debug(f"Calling eAPI command {cmd}")
        try:
            resp = self.eapi.run_show_cmd(cmd)
        except Exception as e:
            self.err(f"eAPI request failed: {e}")
            raise e
        if resp.success():
            data = self.json_load(resp.responses()[0])
        else:
            err = RuntimeError(f"eAPI request failed: {resp.error_message()} "
                               f"({resp.error_code()})")
            self.err(err)
            raise err
        try:
            result = data[result_node]
        except KeyError as e:
            if allow_empty:
                result = {}
            else:
                self.err(f"Failed to get result data: {e}")
                raise e
        self.debug("eAPI request successful")
        return result

    def rptk_request(self, url_path: str) -> RptkResult:
        """Perform a query against the RPTK endpoint."""
        url = "{}/{}".format(self.endpoint.rstrip("/"),
                             url_path.lstrip("/"))
        self.debug(f"Querying RPTK endpoint at {url}")
        try:
            # TODO: construct url properly
            resp = urllib.request.urlopen(url)  # noqa: S310
        except urllib.error.HTTPError as e:
            self.err(f"Request failed: {e.code} {e.reason}")
            raise e
        except urllib.error.URLError as e:
            self.err(f"Request failed: {e}")
            raise e
        self.debug(f"Request successful: {resp.getcode()}")
        result = self.json_load(resp)
        return typing.cast(RptkResult, result)

    def json_load(self,
                  obj: typing.Union[str, typing.TextIO]) -> typing.Any:
        """Deserialise JSON from a string or file-like object."""
        def fail(e: Exception) -> None:
            self.err(f"Failed to deserialise response: {e}")
            raise e

        self.debug("Deserialising JSON response")
        try:
            self.debug("Trying 'json.load' method")
            result = json.load(typing.cast(typing.TextIO, obj))
        except AttributeError:
            self.debug("Object has no 'read' method")
            self.debug("Trying 'json.loads' method")
            try:
                result = json.loads(typing.cast(str, obj))
            except Exception as e:
                fail(e)
        except Exception as e:
            fail(e)
        self.debug("Successfully deserialised JSON")
        return result

    @property
    def data(self) -> typing.Optional[Stats]:
        """Get data from the worker."""
        if self.p_data.poll():
            return typing.cast(Stats, self.p_data.recv())
        return None

    @property
    def error(self) -> typing.Optional[Exception]:
        """Get exception raised by worker."""
        if self.p_err.poll():
            return typing.cast(Exception, self.p_err.recv())
        return None
