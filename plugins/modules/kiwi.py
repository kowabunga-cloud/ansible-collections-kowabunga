#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kiwi
short_description: Manage Kowabunga inner WAN interface nodes
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kiwi inner WAN interface node.
options:
  name:
    description:
      - Name for the kiwi node.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the kiwi node.
    type: str
  agents:
    description:
      - List of agent names (or IDs) managing this kiwi node.
    type: list
  region:
    description:
      - Name (or ID) of the region where the kiwi will be created.
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
- name: Create a kiwi node
  kowabunga.cloud.kiwi:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: kiwi-01
    agents:
      - my-agent
    region: eu-west-1

- name: Delete a kiwi node
  kowabunga.cloud.kiwi:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: kiwi-01
    region: eu-west-1
    state: absent
'''

RETURN = r'''
kiwi:
  description: Dictionary describing the kiwi node.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Kiwi ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Kiwi name
      type: str
      sample: "kiwi-01"
    description:
      description: Kiwi description
      type: str
      sample: "Kiwi node 01"
    agents:
      description: List of agent IDs
      type: list
      sample: ["6850281677f2462b6919dbe6"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KiwiModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        agents=dict(immutable=False, type='list'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'kiwi'
    resource_arg_maps = ['agents']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        kiwi = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, kiwi))

        if state == 'present' and not kiwi:
            kiwi = self._create()
            self.exit_json(changed=True, kiwi=kiwi.to_dict(), action="create")
        elif state == 'present' and kiwi:
            update, kiwi = self._build_update(kiwi)
            if update:
                kiwi = self._update(kiwi)
            self.exit_json(changed=bool(update), kiwi=kiwi.to_dict(), action="update")
        elif state == 'absent' and kiwi:
            self._delete(kiwi)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not kiwi:
            self.exit_json(changed=False)

    def _find_agents(self):
        if not self.params.get('agents'):
            return []
        return self._find_resources_by_name('agent', 'agents')

    def _create(self):
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        kiwi = self.sdk.Kiwi.from_dict(self.kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_kiwi(region.id, kiwi)

    def _update(self, kiwi):
        return self.sdk.KiwiApi(self.client).update_kiwi(kiwi.id, kiwi)

    def _delete(self, kiwi):
        return self.sdk.KiwiApi(self.client).delete_kiwi(kiwi.id)


def main():
    module = KiwiModule()
    module()


if __name__ == '__main__':
    main()
