#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kaktus
short_description: Manage Kowabunga hyperconverged bare-metal nodes
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kaktus hyperconverged bare-metal node.
options:
  name:
    description:
      - Name for the kaktus node.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the kaktus node.
    type: str
  overcommit_cpu_ratio:
    description:
      - CPU overcommit ratio.
    default: 3
    type: int
  overcommit_memory_ratio:
    description:
      - Memory overcommit ratio.
    default: 2
    type: int
  agents:
    description:
      - List of agent names (or IDs) managing this node.
    required: true
    type: list
  zone:
    description:
      - Name (or ID) of the availability zone where the kaktus will be created.
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
- name: Create a kaktus node
  kowabunga.cloud.kaktus:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: kaktus-01
    agents:
      - my-agent
    zone: eu-west-1a

- name: Delete a kaktus node
  kowabunga.cloud.kaktus:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: kaktus-01
    zone: eu-west-1a
    state: absent
'''

RETURN = r'''
kaktus:
  description: Dictionary describing the kaktus node.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Kaktus ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Kaktus name
      type: str
      sample: "kaktus-01"
    description:
      description: Kaktus description
      type: str
      sample: "Kaktus node 01"
    overcommit_cpu_ratio:
      description: CPU overcommit ratio
      type: int
      sample: 3
    overcommit_memory_ratio:
      description: Memory overcommit ratio
      type: int
      sample: 2
    agents:
      description: List of agent IDs
      type: list
      sample: ["6850281677f2462b6919dbe6"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KaktusModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        overcommit_cpu_ratio=dict(immutable=False, default=3, type='int'),
        overcommit_memory_ratio=dict(immutable=False, default=2, type='int'),
        agents=dict(immutable=False, required=True, type='list'),
        zone=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'kaktus'
    resource_arg_maps = ['agents']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        kaktus = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, kaktus))

        if state == 'present' and not kaktus:
            kaktus = self._create()
            self.exit_json(changed=True, kaktus=kaktus.to_dict(), action="create")
        elif state == 'present' and kaktus:
            update, kaktus = self._build_update(kaktus)
            if update:
                kaktus = self._update(kaktus)
            self.exit_json(changed=bool(update), kaktus=kaktus.to_dict(), action="update")
        elif state == 'absent' and kaktus:
            self._delete(kaktus)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not kaktus:
            self.exit_json(changed=False)

    def _create(self):
        zone = self._find_resource_by_name('zone', self.params['zone'])
        if not zone:
            self.fail_json(msg=f"Zone '{self.params['zone']}' not found")
        kaktus = self.sdk.Kaktus.from_dict(self.kwargs)
        api = self.sdk.ZoneApi(self.client)
        return api.create_kaktus(zone.id, kaktus)

    def _update(self, kaktus):
        return self.sdk.KaktusApi(self.client).update_kaktus(kaktus.id, kaktus)

    def _delete(self, kaktus):
        return self.sdk.KaktusApi(self.client).delete_kaktus(kaktus.id)


def main():
    module = KaktusModule()
    module()


if __name__ == '__main__':
    main()
