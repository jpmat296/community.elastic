#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Jean-Pierre Matsumoto (@jpmat296)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy
import traceback

dictdiffer_found = False
dict_diff = None
DICTDIFF_IMP_ERR = None

try:
    from dictdiffer import diff as dict_diff
    dictdiffer_found = True
except ImportError:
    DICTDIFF_IMP_ERR = traceback.format_exc()
    dictdiffer_found = False

policy_runtime_fields = [
    'policy_id',
    'last_updated_time',
    'schema_version',
    'error_notification',
]

policy_action_defaults = {
    'retry': {
        'count': 3,
        'backoff': 'exponential',
        'delay': '1m'
    }
}

policy_action_rollover_defaults = {
    'copy_alias': False
}


def deep_remove_fields(data, fields_to_remove):
    """
    Recursively removes specified keys from a dictionary and its nested structures.
    """
    if isinstance(data, dict):
        for key in list(data.keys()):
            if key in fields_to_remove:
                del data[key]
            else:
                deep_remove_fields(data[key], fields_to_remove)
    elif isinstance(data, list):
        for item in data:
            deep_remove_fields(item, fields_to_remove)


def ism_is_different(current_policy, target_policy):
    """
    Compare two ISM policies.

    Parameters:
    - current_policy: ISM policy dict currently configured in OpenSearch
    - target_policy: policy dict as defined by the user
    """
    current = copy.deepcopy(current_policy)
    target = copy.deepcopy(target_policy)

    deep_remove_fields(current, policy_runtime_fields)

    for state in target.get('states', []):
        for action_index, action in enumerate(state.get('actions', [])):
            state['actions'][action_index] = policy_action_defaults | action

    try:
        rollover = target['states'][0]['actions'][0].get('rollover')
        if rollover is not None:
            target['states'][0]['actions'][0]['rollover'] = policy_action_rollover_defaults | rollover
    except Exception:
        # ignore if structure not as expected
        pass

    result = list(dict_diff(current, target))
    return len(result) > 0