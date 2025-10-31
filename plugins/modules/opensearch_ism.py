#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Jean-Pierre Matsumoto (@jpmat296)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: opensearch_ism

short_description: Manage Opensearch Index State Management.

description:
  - Manage Opensearch Index State Management.
  - Create, update and delete ISM.

author: Jean-Pierre Matsumoto (@jpmat296)
version_added: "2.0.0"

extends_documentation_fragment:
  - community.elastic.login_options

options:
  state:
    description: The state of the ISM Policy.
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - The ISM Policy name
    type: str
    required: True
  policy:
    description:
      - The ISM Policy Document.
    type: dict
    default: {}
'''

EXAMPLES = r'''
- name: Create an ISM Policy
  community.elastic.opensearch_ism:
    name: mypolicy
    policy:
      description: daily rollover then delete
      default_state: hot
      states:
      - name: hot
        actions:
        - rollover:
            min_index_age: 1d
        transitions:
        - state_name: delete
          conditions:
            min_index_age: 7d

- name: Delete an ISM Policy
  community.elastic.opensearch_ism:
    name: mypolicy
    state: absent
'''

RETURN = r'''
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


from ansible_collections.community.elastic.plugins.module_utils.elastic_common import (
    missing_required_lib,
    elastic_found,
    E_IMP_ERR,
    elastic_common_argument_spec,
    ElasticHelpers,
    NotFoundError,
    __version__
)

# import ism helpers from module_utils
from ansible_collections.community.elastic.plugins.module_utils.ism_utils import (
    ism_is_different,
)


def get_policy(client, name):
    '''
    Gets the policy document specified by name. Full Opensearch response is returned.
    '''
    try:
        # with open("/Users/jpmat/test.log", "a") as f:
        #     print("before policy_doc", file=f)
        resp = client.transport.perform_request(
          "GET",
          f"/_plugins/_ism/policies/{name}"
        )
        # with open("/Users/jpmat/test.log", "a") as f:
        #     print("policy_doc resp", resp, file=f)
    except Exception as e:
        # with open("/Users/jpmat/test.log", "a") as f:
        #     print("Exception", e, file=f)
        resp = None
    except NotFoundError:
        resp = None
    return resp


def put_policy(client, name, body, current_policy=None):
    '''
    Creates / Updates the policy specified by name using the body provided
    '''
    params = {}
    if current_policy is not None:
        params['if_seq_no'] = current_policy['_seq_no']
        params['if_primary_term'] = current_policy['_primary_term']
    policy_doc = client.transport.perform_request(
        "PUT",
        f"/_plugins/_ism/policies/{name}",
        body=body,
        params=params,
    )['policy']
    return policy_doc


def delete_policy(client, name):
    '''
    Deletes the policy specified by name
    '''
    try:
      resp = client.transport.perform_request(
          "DELETE",
          f"/_plugins/_ism/policies/{name}"
      )
    except NotFoundError:
        resp = None
    return resp


# ================
# Module execution
#


def main():

    state_choices = [
        "present",
        "absent",
    ]

    argument_spec = elastic_common_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        state=dict(type='str', choices=state_choices, default='present'),
        policy=dict(type='dict', default={}),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['login_user', 'login_password']],
    )

    if not elastic_found:
        module.fail_json(msg=missing_required_lib('elasticsearch'),
                         exception=E_IMP_ERR)

    name = module.params['name']
    state = module.params['state']
    policy = module.params['policy']

    try:
        elastic = ElasticHelpers(module)
        client = elastic.connect()

        policy_resp = get_policy(client, name)

        if state == 'present':
            request_body = {"policy": policy}
            if policy_resp is not None:
                if ism_is_different(policy_resp['policy'], policy):
                    if module.check_mode:
                        response = {"acknowledged": True}
                    else:
                        response = dict(put_policy(client, name, request_body, current_policy=policy_resp))
                    module.exit_json(changed=True, msg="The ISM Policy '{0}' was updated.".format(name), **response)
                else:
                    module.exit_json(changed=False, msg="The ISM Policy '{0}' is already configured as specified.".format(name))
            else:
                if module.check_mode:
                    response = {"acknowledged": True}
                else:
                    response = dict(put_policy(client, name, request_body))
                module.exit_json(changed=True, msg="The ISM Policy '{0}' was created.".format(name), **response)
        elif state == 'absent':
            if policy_resp is not None:
                if module.check_mode:
                    response = {"acknowledged": True}
                else:
                    response = dict(delete_policy(client, name))
                module.exit_json(changed=True, msg="The ISM Policy '{0}' was deleted.".format(name), **response)
            else:
                module.exit_json(changed=False, msg="The ISM Policy '{0}' does not exist.".format(name))
    except Exception as excep:
        module.fail_json(msg='Opensearch error: %s' % to_native(excep))


if __name__ == '__main__':
    main()
