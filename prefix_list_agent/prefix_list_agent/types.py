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
"""prefix_list_agent typing helpers."""

import typing

ConfigVal = typing.TypeVar("ConfigVal")

StatusVal = typing.TypeVar("StatusVal")

Policies = typing.Dict[str, str]

Configured = typing.Dict[
    str,
    typing.DefaultDict[
        str,
        typing.Dict[str, str],
    ],
]

Objects = typing.Set[str]

Stats = typing.Dict[str, int]

RptkPrefixEntry = typing.Dict[  # prefix
    str,
    typing.Union[str, bool, int],
]

RptkPrefixEntries = typing.List[RptkPrefixEntry]

RptkPrefixes = typing.Dict[
    str,  # object
    typing.Dict[
        str,  # afi
        RptkPrefixEntries,
    ],
]

RptkResult = typing.Union[Policies, RptkPrefixes]

Data = typing.Dict[
    str,  # policy
    RptkPrefixes,
]

EapiResponse = typing.Any
