#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: template
short_description: Manage Kowabunga VM templates
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga VM template.
options:
  name:
    description:
      - Name for the template.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the template.
    type: str
  os:
    description:
      - Operating system type for the template.
    default: linux
    choices: [linux, windows]
    type: str
  source:
    description:
      - URL or path to the template source image.
      - This attribute cannot be updated.
    required: true
    type: str
  pool:
    description:
      - Name (or ID) of the storage pool where the template will be stored.
    required: true
    type: str
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
    type: str
extends_documentation_fragment:
  - kowabunga.cloud.kowabunga
'''

EXAMPLES = r'''
- name: Create a VM template
  kowabunga.cloud.template:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: ubuntu-24.04
    source: https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
    pool: pool-01

- name: Delete a VM template
  kowabunga.cloud.template:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: ubuntu-24.04
    pool: pool-01
    state: absent
'''

RETURN = r'''
template:
  description: Dictionary describing the template.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Template ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Template name
      type: str
      sample: "ubuntu-24.04"
    description:
      description: Template description
      type: str
      sample: "Ubuntu 24.04 LTS"
    os:
      description: Operating system type
      type: str
      sample: "linux"
    source:
      description: Template source URL/path
      type: str
      sample: "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class TemplateModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        os=dict(immutable=False, default='linux', type='str', choices=['linux', 'windows']),
        source=dict(immutable=True, required=True, type='str'),
        pool=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'template'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        template = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, template))

        if state == 'present' and not template:
            template = self._create()
            self.exit_json(changed=True, template=template.to_dict(), action="create")
        elif state == 'present' and template:
            update, template = self._build_update(template)
            if update:
                template = self._update(template)
            self.exit_json(changed=bool(update), template=template.to_dict(), action="update")
        elif state == 'absent' and template:
            self._delete(template)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not template:
            self.exit_json(changed=False)

    def _create(self):
        pool = self._find_pool_by_name(self.params['pool'])
        if not pool:
            self.fail_json(msg=f"Storage pool '{self.params['pool']}' not found")
        template = self.sdk.Template.from_dict(self.kwargs)
        api = self.sdk.PoolApi(self.client)
        return api.create_template(pool.id, template)

    def _update(self, template):
        return self.sdk.TemplateApi(self.client).update_template(template.id, template)

    def _delete(self, template):
        return self.sdk.TemplateApi(self.client).delete_template(template.id)


def main():
    module = TemplateModule()
    module()


if __name__ == '__main__':
    main()
