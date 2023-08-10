#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Jean-Pierre Matsumoto (@jpmat296) <jpmat296@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: elastic_dangling_index_list

short_description: Returns list of dangling indexes.

description:
  - List dangling indexes on all nodes of Elasticsearch cluster.

author: Jean-Pierre Matsumoto (@jpmat296)
version_added: "1.2.0"

extends_documentation_fragment:
  - community.elastic.login_options

'''

EXAMPLES = r'''
- name: List dangling indexes
  community.elastic.elastic_dangling_list:
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

    argument_spec = elastic_common_argument_spec()
    argument_spec.update()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['login_user', 'login_password']],
    )

    if not elastic_found:
        module.fail_json(msg=missing_required_lib('elasticsearch'),
                         exception=E_IMP_ERR)

    try:
        elastic = ElasticHelpers(module)
        client = elastic.connect()

        response = dict(client.dangling_indices.list_dangling_indices())

        module.exit_json(changed=False, msg="List of dangling indices.", **response)
    except Exception as excep:
        module.fail_json(msg='Elastic error: %s' % to_native(excep))


if __name__ == '__main__':
    main()
