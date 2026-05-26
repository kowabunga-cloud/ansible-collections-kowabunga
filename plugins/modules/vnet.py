#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: vnet
short_description: Manage Kowabunga virtual networks
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga virtual network.
options:
  name:
    description:
      - Name for the virtual network.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the virtual network.
    type: str
  vlan:
    description:
      - VLAN ID for the virtual network.
    type: int
  interface:
    description:
      - Physical interface name to use for this virtual network.
      - This attribute cannot be updated.
    required: true
    type: str
  private:
    description:
      - Whether the virtual network is private.
    default: true
    type: bool
  region:
    description:
      - Name (or ID) of the region where the virtual network will be created.
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
- name: Create a virtual network
  kowabunga.cloud.vnet:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vnet-01
    interface: eth0
    region: eu-west-1

- name: Delete a virtual network
  kowabunga.cloud.vnet:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vnet-01
    region: eu-west-1
    state: absent
'''

RETURN = r'''
vnet:
  description: Dictionary describing the virtual network.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: VNet ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: VNet name
      type: str
      sample: "vnet-01"
    description:
      description: VNet description
      type: str
      sample: "Virtual network 01"
    vlan:
      description: VLAN ID
      type: int
      sample: 100
    interface:
      description: Physical interface name
      type: str
      sample: "eth0"
    private:
      description: Whether the network is private
      type: bool
      sample: true
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class VnetModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        vlan=dict(immutable=False, type='int'),
        interface=dict(immutable=True, required=True, type='str'),
        private=dict(immutable=False, default=True, type='bool'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        vnet = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, vnet))

        if state == 'present' and not vnet:
            vnet = self._create()
            self.exit_json(changed=True, vnet=vnet.to_dict(), action="create")
        elif state == 'present' and vnet:
            update, vnet = self._build_update(vnet)
            if update:
                vnet = self._update(vnet)
            self.exit_json(changed=bool(update), vnet=vnet.to_dict(), action="update")
        elif state == 'absent' and vnet:
            self._delete(vnet)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not vnet:
            self.exit_json(changed=False)

    def _read(self):
        return self._find_vnet_by_name(self.params['name'])

    def _create(self):
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        vnet = self.sdk.VNet.from_dict(self.kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_v_net(region.id, vnet)

    def _update(self, vnet):
        return self.sdk.VnetApi(self.client).update_v_net(vnet.id, vnet)

    def _delete(self, vnet):
        return self.sdk.VnetApi(self.client).delete_v_net(vnet.id)


def main():
    module = VnetModule()
    module()


if __name__ == '__main__':
    main()
