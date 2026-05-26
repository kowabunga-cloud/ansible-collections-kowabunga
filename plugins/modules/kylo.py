#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kylo
short_description: Manage Kowabunga NFS-like remote storage volumes
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kylo elastic NFS-like remote storage volume.
options:
  name:
    description:
      - Name for the kylo volume.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the kylo volume.
    type: str
  access:
    description:
      - Access mode for the volume.
    default: RW
    choices: [RO, RW]
    type: str
  protocols:
    description:
      - List of NFS protocol versions to support (3 and/or 4).
    type: list
  project:
    description:
      - Name (or ID) of the project where the kylo will be created.
    required: true
    type: str
  region:
    description:
      - Name (or ID) of the region where the kylo will be created.
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
- name: Create a kylo volume
  kowabunga.cloud.kylo:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vol-01
    project: my-project
    region: eu-west-1

- name: Delete a kylo volume
  kowabunga.cloud.kylo:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vol-01
    project: my-project
    region: eu-west-1
    state: absent
'''

RETURN = r'''
kylo:
  description: Dictionary describing the kylo volume.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Kylo ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Kylo name
      type: str
      sample: "vol-01"
    description:
      description: Kylo description
      type: str
      sample: "Volume 01"
    access:
      description: Access mode
      type: str
      sample: "RW"
    protocols:
      description: NFS protocol versions
      type: list
      sample: [3, 4]
    endpoint:
      description: NFS mount endpoint
      type: str
      sample: "nfs.acme.local:/vol-01"
    size:
      description: Volume size in GB
      type: int
      sample: 100
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KyloModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        access=dict(immutable=False, default='RW', type='str', choices=['RO', 'RW']),
        protocols=dict(immutable=False, type='list'),
        project=dict(required=True, type='str'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'kylo'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        kylo = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, kylo))

        if state == 'present' and not kylo:
            kylo = self._create()
            self.exit_json(changed=True, kylo=kylo.to_dict(), action="create")
        elif state == 'present' and kylo:
            update, kylo = self._build_update(kylo)
            if update:
                kylo = self._update(kylo)
            self.exit_json(changed=bool(update), kylo=kylo.to_dict(), action="update")
        elif state == 'absent' and kylo:
            self._delete(kylo)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not kylo:
            self.exit_json(changed=False)

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        kylo = self.sdk.Kylo.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_region_kylo(project.id, region.id, kylo)

    def _update(self, kylo):
        return self.sdk.KyloApi(self.client).update_kylo(kylo.id, kylo)

    def _delete(self, kylo):
        return self.sdk.KyloApi(self.client).delete_kylo(kylo.id)


def main():
    module = KyloModule()
    module()


if __name__ == '__main__':
    main()
