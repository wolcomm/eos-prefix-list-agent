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
"""prefix_list_agent Package."""

from __future__ import print_function
from __future__ import unicode_literals

import logging

import prefix_list_agent.__meta__  # noqa

from prefix_list_agent.agent import PrefixListAgent
from prefix_list_agent.cli import start

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [PrefixListAgent.__name__, start.__name__]
