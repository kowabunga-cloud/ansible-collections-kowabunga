#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: volume
short_description: Manage Kowabunga storage volumes
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga storage volume.
options:
  name:
    description:
      - Name for the storage volume.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the storage volume.
    type: str
  type:
    description:
      - Volume type.
      - This attribute cannot be updated.
    required: true
    choices: [os, iso, raw]
    type: str
  size:
    description:
      - Volume size in gigabytes.
      - This attribute cannot be updated.
    required: true
    type: int
  project:
    description:
      - Name (or ID) of the project where the volume will be created.
    required: true
    type: str
  region:
    description:
      - Name (or ID) of the region where the volume will be created.
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
- name: Create a storage volume
  kowabunga.cloud.volume:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: disk-01
    type: os
    size: 20
    project: my-project
    region: eu-west-1

- name: Delete a storage volume
  kowabunga.cloud.volume:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: disk-01
    project: my-project
    region: eu-west-1
    state: absent
'''

RETURN = r'''
volume:
  description: Dictionary describing the storage volume.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Volume ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Volume name
      type: str
      sample: "disk-01"
    description:
      description: Volume description
      type: str
      sample: "Disk 01"
    type:
      description: Volume type
      type: str
      sample: "os"
    size:
      description: Volume size in GB
      type: int
      sample: 20
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class VolumeModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        type=dict(immutable=True, required=True, type='str', choices=['os', 'iso', 'raw']),
        size=dict(immutable=True, required=True, type='int'),
        project=dict(required=True, type='str'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'volume'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        volume = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, volume))

        if state == 'present' and not volume:
            volume = self._create()
            self.exit_json(changed=True, volume=volume.to_dict(), action="create")
        elif state == 'present' and volume:
            update, volume = self._build_update(volume)
            if update:
                volume = self._update(volume)
            self.exit_json(changed=bool(update), volume=volume.to_dict(), action="update")
        elif state == 'absent' and volume:
            self._delete(volume)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not volume:
            self.exit_json(changed=False)

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        volume = self.sdk.Volume.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_region_volume(project.id, region.id, volume)

    def _update(self, volume):
        return self.sdk.VolumeApi(self.client).update_volume(volume.id, volume)

    def _delete(self, volume):
        return self.sdk.VolumeApi(self.client).delete_volume(volume.id)


def main():
    module = VolumeModule()
    module()


if __name__ == '__main__':
    main()
