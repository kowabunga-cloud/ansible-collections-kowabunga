#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: adapter
short_description: Manage Kowabunga network adapters
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga network adapter.
options:
  name:
    description:
      - Name for the network adapter.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the network adapter.
    type: str
  mac:
    description:
      - MAC address for the adapter (auto-generated if not specified).
    type: str
  reserved:
    description:
      - Whether the adapter is reserved.
    default: false
    type: bool
  subnet:
    description:
      - Name (or ID) of the subnet where the adapter will be created.
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
- name: Create a network adapter
  kowabunga.cloud.adapter:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: adapter-01
    subnet: subnet-01

- name: Delete a network adapter
  kowabunga.cloud.adapter:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: adapter-01
    subnet: subnet-01
    state: absent
'''

RETURN = r'''
adapter:
  description: Dictionary describing the network adapter.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Adapter ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Adapter name
      type: str
      sample: "adapter-01"
    description:
      description: Adapter description
      type: str
      sample: "Network adapter 01"
    mac:
      description: MAC address
      type: str
      sample: "02:00:00:00:00:01"
    addresses:
      description: List of assigned IP addresses
      type: list
      sample: ["192.168.1.10"]
    reserved:
      description: Whether the adapter is reserved
      type: bool
      sample: false
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class AdapterModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        mac=dict(immutable=False, type='str'),
        reserved=dict(immutable=False, default=False, type='bool'),
        subnet=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'adapter'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        adapter = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, adapter))

        if state == 'present' and not adapter:
            adapter = self._create()
            self.exit_json(changed=True, adapter=adapter.to_dict(), action="create")
        elif state == 'present' and adapter:
            update, adapter = self._build_update(adapter)
            if update:
                adapter = self._update(adapter)
            self.exit_json(changed=bool(update), adapter=adapter.to_dict(), action="update")
        elif state == 'absent' and adapter:
            self._delete(adapter)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not adapter:
            self.exit_json(changed=False)

    def _create(self):
        subnet = self._find_resource_by_name('subnet', self.params['subnet'])
        if not subnet:
            self.fail_json(msg=f"Subnet '{self.params['subnet']}' not found")
        adapter = self.sdk.Adapter.from_dict(self.kwargs)
        api = self.sdk.SubnetApi(self.client)
        return api.create_adapter(subnet.id, adapter)

    def _update(self, adapter):
        return self.sdk.AdapterApi(self.client).update_adapter(adapter.id, adapter)

    def _delete(self, adapter):
        return self.sdk.AdapterApi(self.client).delete_adapter(adapter.id)


def main():
    module = AdapterModule()
    module()


if __name__ == '__main__':
    main()
