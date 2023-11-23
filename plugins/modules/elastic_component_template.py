#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Jean-Pierre Matsumoto <jpmat296@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elastic_component_template

short_description: Manage Elasticsearch component templates.

description:
  - Manage Elasticsearch component templates.

author: Jean-Pierre Matsumoto (@jpmat296)
version_added: "0.0.2"

extends_documentation_fragment:
  - community.elastic.login_options

options:
  name:
    description:
      - Name of component template.
    type: str
    required: yes
  src:
    description:
      - Path to JSON file containing the component template
      - value is required when C(state) is C(present)
    type: str
  state:
    description:
      - The desired state of the component template.
    type: str
    choices:
      - present
      - absent
    default: present
'''

EXAMPLES = r'''
- name: Create new component template
  community.elastic.elastic_component_template:
    name: 02_shards
    src: files/02_shards.json

- name: Delete a component template
  community.elastic.elastic_component_template:
    name: 02_shards
    state: absent
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


def get_component_template(module, client, name):
    '''
    Uses the get component template api to return information about the given
    component template name
    '''
    try:
        response = dict(client.cluster.get_component_template(name=name))
    except NotFoundError as excep:
        response = None
    except Exception as excep:
        module.fail_json(msg=str(excep))
    return response


def put_component_template(module, client, name):
    '''
    Creates or updates a component template using a JSON file as component template content.
    '''
    keys = [
        "src"
    ]

    with open(module.params['src']) as json_file:
        data = json.load(json_file)

    try:
        response = dict(client.cluster.put_component_template(name=name, body=data))
        if not isinstance(response, dict):  # Valid response should be a dict
            module.fail_json(msg="Invalid response received: {0}.".format(str(response)))
    except Exception as excep:
        module.fail_json(msg=str(excep))
    return response


def component_template_is_different(current_ct, module):
    '''
    Check if component template is different
    '''
    with open(module.params['src']) as json_file:
        disk_ct = json.load(json_file)
    str1 = json.dumps(current_ct, sort_keys=True)
    str2 = json.dumps(disk_ct, sort_keys=True)
    return str1 != str2


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
        name=dict(type='str', required=True),
        src=dict(type='str'),
        state=dict(type='str', choices=state_choices, default='present')
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

        ct = get_component_template(module, client, name)
        response = None

        if ct is None:
            if state == "present":
                if module.check_mode is False:
                    response = put_component_template(module, client, name)
                module.exit_json(changed=True, msg="The component template {0} was successfully created: {1}".format(name, str(response)))
            elif state == "absent":
                module.exit_json(changed=False, msg="The component template {0} does not exist.".format(name))
        else:
            if state == "present":
                if component_template_is_different(ct['component_templates'][0]['component_template'], module):
                    if module.check_mode is False:
                        response = put_component_template(module, client, name)
                    module.exit_json(changed=True, msg="The component template {0} was successfully updated: {1} {2}".format(name, str(response), str(ct)))
                else:
                    module.exit_json(changed=False, msg="The component template {0} already exists as configured.".format(name))
            elif state == "absent":
                if module.check_mode is False:
                    response = client.cluster.delete_component_template(name=name)
                    module.exit_json(changed=True, msg="The component template {0} was deleted.".format(name))
                else:
                    module.exit_json(changed=True, msg="The component template {0} was deleted.".format(name))
    except Exception as excep:
        module.fail_json(msg='Elastic error: %s' % to_native(excep))


if __name__ == '__main__':
    main()