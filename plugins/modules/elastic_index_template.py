#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Rhys Campbell (@rhysmeister) <rhys.james.campbell@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elastic_index_template

short_description: Manage Elasticsearch index templates.

description:
  - Manage Elasticsearch index templates.
  - Only composable index templates introduced in Elasticsearch 7.8 are supported.

author: Jean-Pierre Matsumoto (@jpmat296)
version_added: "1.2.0"

extends_documentation_fragment:
  - community.elastic.login_options

options:
  state:
    description: The state of the index template.
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - The name of the index template
    type: str
    required: True
  src:
    description:
      - Path to a json file containing index template body.
    type: str

'''

EXAMPLES = r'''
- name: Create an index template named template_1
  community.elastic.elastic_index_template:
    name: template_1
    src: index_template/template_1.json
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import json

from ansible_collections.community.elastic.plugins.module_utils.elastic_common import (
    missing_required_lib,
    elastic_found,
    E_IMP_ERR,
    elastic_common_argument_spec,
    ElasticHelpers,
    NotFoundError
)


def index_template_from_file(src):
    with open(src) as f:
        return json.loads(f.read())


def get_index_template(module, client, name):
    '''
    Uses the get _index_template api to return information about the given template
    '''
    try:
        response = dict(client.indices.get_index_template(name=name))
    except NotFoundError as excep:
        response = None
    except Exception as excep:
        module.fail_json(msg=str(excep))
    return response


def put_index_template(module, client, name):
    '''
    Creates or updates an index template
    '''
    try:
        body = index_template_from_file(module.params['src'])
        response = dict(client.indices.put_index_template(name=name, body=body))
        if not isinstance(response, dict):  # Valid response should be a dict
            module.fail_json(msg="Invalid response received: {0}.".format(str(response)))
    except Exception as excep:
        module.fail_json(msg=str(excep))
    return response


def index_template_is_different(index_template, module):
    '''
    Check if there are any differences in the index template
    '''
    body = index_template_from_file(module.params['src'])
    dict1 = json.dumps(body, sort_keys=True)
    dict2 = json.dumps(index_template, sort_keys=True)
    if dict1 is not None and dict1 != dict2:
        return True


# ================
# Module execution
#

def main():

    state_choices = [
        "present",
        "absent"
    ]

    argument_spec = elastic_common_argument_spec()
    argument_spec.update(
        state=dict(type='str', choices=state_choices, default='present'),
        name=dict(type='str', required=True),
        src=dict(type='str', required=False),
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

    try:
        elastic = ElasticHelpers(module)
        client = elastic.connect()

        before = get_index_template(module, client, name)
        if before is not None:
            before = before['index_templates'][0]['index_template']
        response = None

        if before is None:
            if state == "present":
                if module.check_mode is False:
                    response = put_index_template(module, client, name)
                exit_json = {
                    "changed": True,
                    "msg": "The index_template {0} was successfully created: {1}".format(name, str(response)),
                    "diff": {"after": index_template_from_file(module.params['src'])} if module._diff else None,
                }
                module.exit_json(**exit_json)
            elif state == "absent":
                module.exit_json(changed=False, msg="The index_template {0} does not exist.".format(name))
        else:
            if state == "present":
                if index_template_is_different(before, module):
                    if module.check_mode is False:
                        response = put_index_template(module, client, name)
                    exit_json = {
                        "changed": True,
                        "msg": "The index_template {0} was successfully updated: {1}".format(name, str(response)),
                        "diff": {"before": before, "after": index_template_from_file(module.params['src'])} if module._diff else None,
                    }
                    module.exit_json(**exit_json)
                else:
                    module.exit_json(changed=False, msg="The index_template {0} already exists as configured.".format(name))
            elif state == "absent":
                if module.check_mode is False:
                    response = client.indices.delete_index_template(name=name)  # TODO Check ack key?
                    module.exit_json(changed=True, msg="The index_template {0} was deleted.".format(name))
                else:
                    module.exit_json(changed=True, msg="The index_template {0} was deleted.".format(name))
    except Exception as excep:
        module.fail_json(msg='Elastic error: %s' % to_native(excep))


if __name__ == '__main__':
    main()
