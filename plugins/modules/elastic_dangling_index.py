#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Jean-Pierre Matsumoto (@jpmat296) <jpmat296@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elastic_dangling_index

short_description: Manage Elasticsearch dangling indexes.

description:
  - Manage one Elasticsearch dangling indexes.
  - Import the dangling index or delete it.
  - check_mode is supported.

author: Jean-Pierre Matsumoto (@jpmat296)
version_added: "1.2.0"

extends_documentation_fragment:
  - community.elastic.login_options

options:
  uuid:
    description:
      - Dangling index uuid
    type: str
    required: True
  state:
    description: The state of the dangling index.
    type: str
    choices:
      - imported
      - absent
    default: imported
'''

EXAMPLES = r'''
- name: Import dangling index
  community.elastic.elastic_dangling_index:
    uuid: H3mqTUpCRse8xQyuCv_1Tw
    state: imported

- name: Delete dangling index
  community.elastic.elastic_dangling_index:
    uuid: "owfNsfALSJmkywXL9SxL-A"
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
    ElasticHelpers
)


# ================
# Module execution
#

def main():

    state_choices = [
        "imported",
        "absent"
    ]

    argument_spec = elastic_common_argument_spec()
    argument_spec.update(
        uuid=dict(type='str', required=True),
        state=dict(type='str', choices=state_choices, default='imported'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['login_user', 'login_password']],
    )

    if not elastic_found:
        module.fail_json(msg=missing_required_lib('elasticsearch'),
                         exception=E_IMP_ERR)

    uuid = module.params['uuid']
    state = module.params['state']

    try:
        elastic = ElasticHelpers(module)
        client = elastic.connect()

        current_dangling = [i['index_uuid'] for i in client.dangling_indices.list_dangling_indices()['dangling_indices']]

        if state == 'imported':
            if uuid not in current_dangling:
                module.exit_json(changed=False, msg="The index with uuid '{0}' not found. It has probably been already imported.".format(uuid))
            else:
                if module.check_mode:
                    response = {"acknowledged": True}
                else:
                    response = client.dangling_indices.import_dangling_index(index_uuid=uuid, accept_data_loss=True)
                module.exit_json(changed=True, msg="The index with uuid '{0}' was imported.".format(uuid), **response)
        elif state == 'absent':
            if uuid not in current_dangling:
                module.exit_json(changed=False, msg="The index with uuid '{0}' not found. It has probably been already deleted.".format(uuid))
            else:
                if module.check_mode:
                    response = {"acknowledged": True}
                else:
                    response = client.dangling_indices.delete_dangling_index(index_uuid=uuid, accept_data_loss=True)
                module.exit_json(changed=True, msg="The index with uuid '{0}' was deleted from dangling indices.".format(uuid), **response)
    except Exception as excep:
        module.fail_json(msg='Elastic error: %s' % to_native(excep))


if __name__ == '__main__':
    main()
