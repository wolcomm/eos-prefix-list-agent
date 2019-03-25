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
"""prefix_list_agent base class."""

from __future__ import print_function

import eossdk


class PrefixListBase(object):
    """Base class that implements tracing."""

    def __init__(self):
        """Initialise a PrefixListBase instance."""
        self.tracer = eossdk.Tracer(self.__class__.__name__)

    def _trace(self, msg, level=0):
        """Write tracing output."""
        self.tracer.trace(level, str(msg))

    def emerg(self, msg):
        """Write trace output at 'emergency' (0) level."""
        self._trace(msg, level=0)

    def alert(self, msg):
        """Write trace output at 'alert' (1) level."""
        self._trace(msg, level=1)

    def crit(self, msg):
        """Write trace output at 'critical' (2) level."""
        self._trace(msg, level=2)

    def err(self, msg):
        """Write trace output at 'error' (3) level."""
        self._trace(msg, level=3)

    def warning(self, msg):
        """Write trace output at 'warning' (4) level."""
        self._trace(msg, level=4)

    def notice(self, msg):
        """Write trace output at 'notice' (5) level."""
        self._trace(msg, level=5)

    def info(self, msg):
        """Write trace output at 'informational' (6) level."""
        self._trace(msg, level=6)

    def debug(self, msg):
        """Write trace output at 'debug' (7) level."""
        self._trace(msg, level=7)
