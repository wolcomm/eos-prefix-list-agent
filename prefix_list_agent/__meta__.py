#!/usr/bin/env python3
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
"""prefix_list_agent package metadata."""

__version__ = "0.2.0a1"
__author__ = "Ben Maddison"
__author_email__ = "benm@workonline.africa"
__licence__ = "MIT"
__copyright__ = "Copyright (c) 2019-2021 Workonline Communications (Pty) Ltd"
__url__ = "https://github.com/wolcomm/eos-prefix-list-agent"
__classifiers__ = [
    "Development Status :: 4 - Beta",
    "Environment :: Other Environment",
    "Intended Audience :: Telecommunications Industry",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Other",
    "Programming Language :: Python :: 3",
    "Topic :: Internet",
    "Topic :: System :: Networking"
]
__entry_points__ = None
__scripts__ = [
    "bin/PrefixListAgent"
]


if __name__ == "__main__":
    print(__version__)
