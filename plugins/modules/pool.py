#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: pool
short_description: Manage Kowabunga storage pools
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga storage pool.
options:
  name:
    description:
      - Name for the storage pool.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the storage pool.
    type: str
  pool:
    description:
      - Name of the underlying Ceph storage pool.
      - This attribute cannot be updated.
    required: true
    type: str
  ceph_address:
    description:
      - Ceph cluster address.
    default: localhost
    type: str
  ceph_port:
    description:
      - Ceph cluster port.
    default: 3300
    type: int
  ceph_secret_uuid:
    description:
      - Ceph secret UUID for authentication.
    type: str
  agents:
    description:
      - List of agent names (or IDs) managing this storage pool.
    required: true
    type: list
  region:
    description:
      - Name (or ID) of the region where the storage pool will be created.
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
- name: Create a storage pool
  kowabunga.cloud.pool:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: pool-01
    pool: ceph-pool
    agents:
      - my-agent
    region: eu-west-1

- name: Delete a storage pool
  kowabunga.cloud.pool:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: pool-01
    region: eu-west-1
    state: absent
'''

RETURN = r'''
pool:
  description: Dictionary describing the storage pool.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Storage pool ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Storage pool name
      type: str
      sample: "pool-01"
    description:
      description: Storage pool description
      type: str
      sample: "Storage pool 01"
    pool:
      description: Ceph pool name
      type: str
      sample: "ceph-pool"
    ceph_address:
      description: Ceph cluster address
      type: str
      sample: "localhost"
    ceph_port:
      description: Ceph cluster port
      type: int
      sample: 3300
    agents:
      description: List of agent IDs
      type: list
      sample: ["6850281677f2462b6919dbe6"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class PoolModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        pool=dict(immutable=True, required=True, type='str'),
        ceph_address=dict(immutable=False, default='localhost', type='str'),
        ceph_port=dict(immutable=False, default=3300, type='int'),
        ceph_secret_uuid=dict(immutable=False, type='str'),
        agents=dict(immutable=False, required=True, type='list'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_arg_maps = ['agents']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        pool = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, pool))

        if state == 'present' and not pool:
            pool = self._create()
            self.exit_json(changed=True, pool=pool.to_dict(), action="create")
        elif state == 'present' and pool:
            update, pool = self._build_update(pool)
            if update:
                pool = self._update(pool)
            self.exit_json(changed=bool(update), pool=pool.to_dict(), action="update")
        elif state == 'absent' and pool:
            self._delete(pool)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not pool:
            self.exit_json(changed=False)

    def _read(self):
        return self._find_pool_by_name(self.params['name'])

    def _create(self):
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        pool = self.sdk.StoragePool.from_dict(self.kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_storage_pool(region.id, pool)

    def _update(self, pool):
        return self.sdk.PoolApi(self.client).update_storage_pool(pool.id, pool)

    def _delete(self, pool):
        return self.sdk.PoolApi(self.client).delete_storage_pool(pool.id)


def main():
    module = PoolModule()
    module()


if __name__ == '__main__':
    main()
