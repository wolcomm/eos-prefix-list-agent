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

import json
import multiprocessing
import sys

import flask

import gunicorn.app.base


class RptkStub(gunicorn.app.base.BaseApplication):
    """Integrated web server."""

    app = flask.Flask(__name__)
    formats = {"json": {"description": "JSON object"}}
    policies = {"test": "A dummy test policy"}
    objects = {
        "AS-FOO": {
            "ipv4": [
                {"prefix": "192.0.2.0/24", "exact": True}
            ],
            "ipv6": [
                {"prefix": "2001:db8::/32", "exact": False,
                 "greater-equal": 40, "less-equal": 48}
            ]
        },
        "AS-BAR": {
            "ipv4": [
                {"prefix": "198.51.100.0/24", "exact": True},
                {"prefix": "203.0.113.0/24", "exact": True}
            ],
            "ipv6": []
        }
    }

    def __init__(self, **kwargs):
        """Initialise the uwsgi app."""
        self.opts = kwargs
        super(RptkStub, self).__init__()

    def load(self):
        """Load the uwsgi app."""
        return self.app

    def load_config(self):
        """Set config options."""
        for key, value in self.opts.items():
            try:
                self.cfg.set(key.lower(), value)
            except Exception as e:
                print(e)

    def run(self, *args, **kwargs):
        """Run the server."""
        @self.app.route("/formats")
        def formats():
            return json.dumps(self.formats)

        @self.app.route("/policies")
        def policies():
            return json.dumps(self.policies)

        @self.app.route("/query")
        @self.app.route("/<string:format>/query")
        @self.app.route("/<string:format>/<string:obj>")
        @self.app.route("/<string:format>/<string:obj>/<string:policy>")
        def prefix_list(format=None, obj=None, policy=None):
            objs = flask.request.args.getlist("objects")
            if obj:
                objs.append(obj)
            objs = set(objs)
            result = {o: self.objects[o] for o in objs}
            return json.dumps(result)

        super(RptkStub, self).run(*args, **kwargs)


class RptkStubProcess(multiprocessing.Process):
    """Multiprocessing runner."""

    def run(self):
        """Run the stub server."""
        sys.argv = [sys.executable]
        server = RptkStub(loglevel="warning")
        server.run()


def main():
    """Launch a stub version of an rptk web application."""
    server = RptkStub()
    return server.run()


if __name__ == "__main__":
    sys.exit(main())
