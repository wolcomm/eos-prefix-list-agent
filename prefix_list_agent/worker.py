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

from __future__ import print_function

import collections
import json
import multiprocessing
import os
import re
import signal
import sys
import time
import urllib2

from prefix_list_agent.base import PrefixListBase
from prefix_list_agent.exceptions import handle_sigterm, TermException


class PrefixListWorker(multiprocessing.Process, PrefixListBase):
    """Worker to fetch and process IRR data."""

    def __init__(self, endpoint, path, eapi, update_delay, *args, **kwargs):
        """Initialise an PrefixListWorker instance."""
        super(PrefixListWorker, self).__init__(*args, **kwargs)
        PrefixListBase.__init__(self)
        self.endpoint = endpoint
        self.path = path
        self.eapi = eapi
        self.update_delay = update_delay
        self.path_re = re.compile(r"^file:{}/(?P<policy>\w+)/(?P<file>[-.:\w]+)$"  # noqa: E501
                                  .format(self.path.rstrip("/")))
        self._p_err, self._c_err = multiprocessing.Pipe(duplex=False)
        self._p_data, self._c_data = multiprocessing.Pipe(duplex=False)

    @property
    def p_err(self):
        """Get 'p_err' property."""
        return self._p_err

    @property
    def c_err(self):
        """Get 'c_err' property."""
        return self._c_err

    @property
    def p_data(self):
        """Get 'p_data' property."""
        return self._p_data

    @property
    def c_data(self):
        """Get 'c_data' property."""
        return self._c_data

    def run(self):
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

    def get_configured(self, policies):
        """Get the prefix-lists in running-config."""
        configured = {p: collections.defaultdict(dict) for p in policies}
        self.info("Searching for prefix-lists with source matching {}"
                  .format(self.path_re.pattern))
        for afi, cmd in (("ipv4", "show ip prefix-list"),
                         ("ipv6", "show ipv6 prefix-list")):
            data = self.eapi_request(cmd, result_node="ipPrefixLists")
            self.debug("Got response: {}".format(data))
            for name, config in data.items():
                try:
                    source = config["ipPrefixListSource"]
                except KeyError:
                    continue
                self.debug("Testing {}, source {}".format(name, source))
                m = self.path_re.match(source)
                if m:
                    self.debug("Source matched")
                    (policy, file) = m.groups()
                    if policy in policies:
                        configured[policy][name][afi] = file
                    else:
                        self.warning("Ignoring unknown policy {}"
                                     .format(policy))
                else:
                    self.debug("No match")
        return configured

    def refresh_all(self, written_objs):
        """Refresh prefix-lists."""
        self.info("Refreshing source-based prefix-lists")
        for afi in ("ip", "ipv6"):
            if self.update_delay is None:
                cmd = "refresh {} prefix-list".format(afi)
                messages = self.eapi_request(cmd, result_node="messages",
                                             allow_empty=True)
                for msg in messages:
                    for submsg in msg.replace("\nNum", " -").rstrip().split("\n"): # noqa: E501
                        self.info(submsg)
            else:
                for prefix_list in written_objs:
                    cmd = "refresh {} prefix-list {}".format(afi, prefix_list)
                    messages = self.eapi_request(cmd, result_node="messages",
                                                 allow_empty=True)
                    for msg in messages:
                        for submsg in msg.replace("\nNum", " -").rstrip().split("\n"): # noqa: E501
                            self.info(submsg)
                    time.sleep(self.update_delay)
        self.notice("Prefix-lists refreshed successfully")

    def get_policies(self):
        """Get the list of valid policy names from RPTK."""
        url_path = "/policies"
        self.info("Trying to get policy data from {}".format(url_path))
        policies = self.rptk_request(url_path)
        self.debug("Got policies: {}".format(policies.keys()))
        return policies

    def get_data(self, configured):
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

    def get_data_bulk(self, policy, objs):
        """Get IRR data in bulk."""
        url_path = "/json/query?policy={}&".format(policy) + \
                   "&".join(["objects={}".format(obj) for obj in objs])
        self.info("Trying to get prefix data from {}".format(url_path))
        result = self.rptk_request(url_path)
        self.debug("Got prefix data")
        return result

    def get_data_obj(self, policy, obj):
        """Get IRR data for a single object."""
        url_path = "/json/{}/{}".format(obj, policy)
        self.info("Trying to get prefix data from {}".format(url_path))
        result = self.rptk_request(url_path)
        self.debug("Got prefix data")
        return result

    # TODO: include list of written prefix-lists, to give to 'refresh_all()'
    def write_results(self, configured, data):
        """Write prefix-list data to files."""
        stats = {"succeeded": 0, "failed": 0}
        written_objs = list()
        for policy, objs in configured.items():
            self.info("Writing files for policy {}".format(policy))
            if not objs:
                self.info("No objects with policy: {}".format(policy))
                continue
            policy_dir = os.path.join(self.path, policy)
            if not os.path.isdir(policy_dir):
                self.info("Creating directory {}".format(policy_dir))
                os.makedirs(policy_dir)
            for obj, config in objs.items():
                self.info("Trying to write files for {}/{}"
                          .format(obj, policy))
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
                    written_objs.append(obj)
                else:
                    self.warning("No prefix data for {}/{}"
                                 .format(obj, policy))
                    stats["failed"] += len(config)
        return stats, written_objs

    def write_prefix_list(self, path, entries, afi):
        """Write prefix-list to file."""
        self.info("Trying to write {}".format(path))
        try:
            with open(path, "w") as f:
                for i, p in enumerate(entries):
                    f.write(self.prefix_list_line(i, p))
        except Exception as e:
            self.err("Failed to write {}: {}".format(path, e))
            raise e

    def prefix_list_line(self, index, entry):
        """Generate a line in a prefix-list."""
        line = "seq {} permit {}".format(index + 1, entry["prefix"])
        if not entry["exact"]:
            if "greater-equal" in entry:
                line += " ge {}".format(entry["greater-equal"])
            if "less-equal" in entry:
                line += " le {}".format(entry["less-equal"])
        line += "\n"
        return line

    def eapi_request(self, cmd, result_node, allow_empty=False):
        """Get call an enable-mode eAPI command."""
        self.debug("Calling eAPI command {}".format(cmd))
        try:
            resp = self.eapi.run_show_cmd(cmd)
        except Exception as e:
            self.err("eAPI request failed: {}".format(e))
            raise e
        if resp.success():
            data = self.json_load(resp.responses()[0])
        else:
            e = RuntimeError("eAPI request failed: {} ({})"
                             .format(resp.error_message(),
                                     resp.error_code()))
            self.err(e)
            raise e
        try:
            result = data[result_node]
        except KeyError as e:
            if allow_empty:
                result = {}
            else:
                self.err("Failed to get result data: {}".format(e))
                raise e
        self.debug("eAPI request successful")
        return result

    def rptk_request(self, url_path):
        """Perform a query against the RPTK endpoint."""
        url = "{}/{}".format(self.endpoint.rstrip("/"),
                             url_path.lstrip("/"))
        self.debug("Querying RPTK endpoint at {}".format(url))
        try:
            resp = urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            self.err("Request failed: {} {}".format(e.code, e.reason))
            raise e
        except urllib2.URLError as e:
            self.err("Request failed: {}".format(e))
            raise e
        self.debug("Request successful: {}".format(resp.getcode()))
        result = self.json_load(resp)
        return result

    def json_load(self, obj):
        """Deserialise JSON from a string or file-like object."""
        def fail(e):
            self.err("Failed to deserialise response: {}".format(e))
            raise e

        self.debug("Deserialising JSON response")
        try:
            self.debug("Trying 'json.load' method")
            result = json.load(obj)
        except AttributeError:
            self.debug("Object has no 'read' method")
            self.debug("Trying 'json.loads' method")
            try:
                result = json.loads(obj)
            except Exception as e:
                fail(e)
        except Exception as e:
            fail(e)
        self.debug("Successfully deserialised JSON")
        return result

    @property
    def data(self):
        """Get data from the worker."""
        if self.p_data.poll():
            return self.p_data.recv()

    @property
    def error(self):
        """Get exception raised by worker."""
        if self.p_err.poll():
            return self.p_err.recv()
