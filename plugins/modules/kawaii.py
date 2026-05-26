#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kawaii
short_description: Manage Kowabunga network gateway instances
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kawaii network gateway.
options:
  name:
    description:
      - Name for the kawaii gateway.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the kawaii gateway.
    type: str
  project:
    description:
      - Name (or ID) of the project where the kawaii will be created.
    required: true
    type: str
  region:
    description:
      - Name (or ID) of the region where the kawaii will be created.
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
- name: Create a kawaii gateway
  kowabunga.cloud.kawaii:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: gw-01
    project: my-project
    region: eu-west-1

- name: Delete a kawaii gateway
  kowabunga.cloud.kawaii:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: gw-01
    project: my-project
    region: eu-west-1
    state: absent
'''

RETURN = r'''
kawaii:
  description: Dictionary describing the kawaii gateway.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Kawaii ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Kawaii name
      type: str
      sample: "gw-01"
    description:
      description: Kawaii description
      type: str
      sample: "Gateway 01"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KawaiiModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        project=dict(required=True, type='str'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'kawaii'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        kawaii = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, kawaii))

        if state == 'present' and not kawaii:
            kawaii = self._create()
            self.exit_json(changed=True, kawaii=kawaii.to_dict(), action="create")
        elif state == 'present' and kawaii:
            update, kawaii = self._build_update(kawaii)
            if update:
                kawaii = self._update(kawaii)
            self.exit_json(changed=bool(update), kawaii=kawaii.to_dict(), action="update")
        elif state == 'absent' and kawaii:
            self._delete(kawaii)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not kawaii:
            self.exit_json(changed=False)

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        kawaii = self.sdk.Kawaii.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_region_kawaii(project.id, region.id, kawaii)

    def _update(self, kawaii):
        return self.sdk.KawaiiApi(self.client).update_kawaii(kawaii.id, kawaii)

    def _delete(self, kawaii):
        return self.sdk.KawaiiApi(self.client).delete_kawaii(kawaii.id)


def main():
    module = KawaiiModule()
    module()


if __name__ == '__main__':
    main()
