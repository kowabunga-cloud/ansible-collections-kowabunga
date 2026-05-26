#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: nfs
short_description: Manage Kowabunga NFS storage
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga NFS storage.
options:
  name:
    description:
      - Name for the NFS storage.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the NFS storage.
    type: str
  server:
    description:
      - NFS server address (IP or hostname).
      - This attribute cannot be updated.
    required: true
    type: str
  fs:
    description:
      - NFS filesystem type.
    default: nfs
    type: str
  backends:
    description:
      - List of backend addresses.
    type: list
  port:
    description:
      - NFS server port.
    default: 54934
    type: int
  region:
    description:
      - Name (or ID) of the region where the NFS storage will be created.
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
- name: Create NFS storage
  kowabunga.cloud.nfs:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: nfs-01
    server: 192.168.1.10
    region: eu-west-1

- name: Delete NFS storage
  kowabunga.cloud.nfs:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: nfs-01
    region: eu-west-1
    state: absent
'''

RETURN = r'''
nfs:
  description: Dictionary describing the NFS storage.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: NFS storage ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: NFS storage name
      type: str
      sample: "nfs-01"
    description:
      description: NFS storage description
      type: str
      sample: "NFS storage 01"
    endpoint:
      description: NFS server address
      type: str
      sample: "192.168.1.10"
    fs:
      description: Filesystem type
      type: str
      sample: "nfs"
    port:
      description: NFS server port
      type: int
      sample: 54934
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class NfsModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        # 'server' maps to the 'endpoint' field in StorageNFS model.
        # Not marked immutable to avoid conflict with the base 'endpoint' API URL param.
        server=dict(required=True, type='str'),
        fs=dict(immutable=False, default='nfs', type='str'),
        backends=dict(immutable=False, type='list'),
        port=dict(immutable=False, default=54934, type='int'),
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
        nfs = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, nfs))

        if state == 'present' and not nfs:
            nfs = self._create()
            self.exit_json(changed=True, nfs=nfs.to_dict(), action="create")
        elif state == 'present' and nfs:
            update, nfs = self._build_update(nfs)
            if update:
                nfs = self._update(nfs)
            self.exit_json(changed=bool(update), nfs=nfs.to_dict(), action="update")
        elif state == 'absent' and nfs:
            self._delete(nfs)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not nfs:
            self.exit_json(changed=False)

    def _read(self):
        return self._find_nfs_by_name(self.params['name'])

    def _create(self):
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        kwargs = dict(self.kwargs)
        kwargs['endpoint'] = self.params['server']
        nfs = self.sdk.StorageNFS.from_dict(kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_storage_nfs(region.id, nfs)

    def _update(self, nfs):
        return self.sdk.NfsApi(self.client).update_storage_nfs(nfs.id, nfs)

    def _delete(self, nfs):
        return self.sdk.NfsApi(self.client).delete_storage_nfs(nfs.id)


def main():
    module = NfsModule()
    module()


if __name__ == '__main__':
    main()
