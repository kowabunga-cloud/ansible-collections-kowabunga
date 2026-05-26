#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: subnet
short_description: Manage Kowabunga subnets
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga subnet.
options:
  name:
    description:
      - Name for the subnet.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the subnet.
    type: str
  cidr:
    description:
      - CIDR block for the subnet (e.g. 192.168.1.0/24).
      - This attribute cannot be updated.
    required: true
    type: str
  gateway:
    description:
      - Default gateway IP address for the subnet.
    required: true
    type: str
  dns:
    description:
      - DNS server IP address for the subnet.
    type: str
  extra_routes:
    description:
      - List of extra static routes (CIDR notation).
    type: list
  application:
    description:
      - Subnet application type.
    default: user
    choices: [ceph, user]
    type: str
  vnet:
    description:
      - Name (or ID) of the virtual network where the subnet will be created.
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
- name: Create a subnet
  kowabunga.cloud.subnet:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: subnet-01
    cidr: 192.168.1.0/24
    gateway: 192.168.1.1
    vnet: vnet-01

- name: Delete a subnet
  kowabunga.cloud.subnet:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: subnet-01
    vnet: vnet-01
    state: absent
'''

RETURN = r'''
subnet:
  description: Dictionary describing the subnet.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Subnet ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Subnet name
      type: str
      sample: "subnet-01"
    description:
      description: Subnet description
      type: str
      sample: "Subnet 01"
    cidr:
      description: CIDR block
      type: str
      sample: "192.168.1.0/24"
    gateway:
      description: Default gateway
      type: str
      sample: "192.168.1.1"
    dns:
      description: DNS server
      type: str
      sample: "8.8.8.8"
    application:
      description: Application type
      type: str
      sample: "user"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class SubnetModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        cidr=dict(immutable=True, required=True, type='str'),
        gateway=dict(immutable=False, required=True, type='str'),
        dns=dict(immutable=False, type='str'),
        extra_routes=dict(immutable=False, type='list'),
        application=dict(immutable=False, default='user', type='str', choices=['ceph', 'user']),
        vnet=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'subnet'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        subnet = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, subnet))

        if state == 'present' and not subnet:
            subnet = self._create()
            self.exit_json(changed=True, subnet=subnet.to_dict(), action="create")
        elif state == 'present' and subnet:
            update, subnet = self._build_update(subnet)
            if update:
                subnet = self._update(subnet)
            self.exit_json(changed=bool(update), subnet=subnet.to_dict(), action="update")
        elif state == 'absent' and subnet:
            self._delete(subnet)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not subnet:
            self.exit_json(changed=False)

    def _create(self):
        vnet = self._find_vnet_by_name(self.params['vnet'])
        if not vnet:
            self.fail_json(msg=f"VNet '{self.params['vnet']}' not found")
        subnet = self.sdk.Subnet.from_dict(self.kwargs)
        api = self.sdk.VnetApi(self.client)
        return api.create_subnet(vnet.id, subnet)

    def _update(self, subnet):
        return self.sdk.SubnetApi(self.client).update_subnet(subnet.id, subnet)

    def _delete(self, subnet):
        return self.sdk.SubnetApi(self.client).delete_subnet(subnet.id)


def main():
    module = SubnetModule()
    module()


if __name__ == '__main__':
    main()
