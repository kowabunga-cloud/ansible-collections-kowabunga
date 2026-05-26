#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kompute
short_description: Manage Kowabunga virtual machines
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kompute virtual machine.
options:
  name:
    description:
      - Name for the kompute instance.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the kompute instance.
    type: str
  memory:
    description:
      - Memory in megabytes.
      - This attribute cannot be updated.
    required: true
    type: int
  vcpus:
    description:
      - Number of virtual CPUs.
      - This attribute cannot be updated.
    required: true
    type: int
  disk:
    description:
      - OS disk size in gigabytes.
      - This attribute cannot be updated.
    required: true
    type: int
  data_disk:
    description:
      - Data disk size in gigabytes (0 means no data disk).
    default: 0
    type: int
  project:
    description:
      - Name (or ID) of the project where the kompute will be created.
    required: true
    type: str
  zone:
    description:
      - Name (or ID) of the availability zone where the kompute will be created.
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
- name: Create a kompute instance
  kowabunga.cloud.kompute:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vm-01
    memory: 2048
    vcpus: 2
    disk: 20
    project: my-project
    zone: eu-west-1a

- name: Delete a kompute instance
  kowabunga.cloud.kompute:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vm-01
    project: my-project
    zone: eu-west-1a
    state: absent
'''

RETURN = r'''
kompute:
  description: Dictionary describing the kompute instance.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Kompute ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Kompute name
      type: str
      sample: "vm-01"
    description:
      description: Kompute description
      type: str
      sample: "VM 01"
    memory:
      description: Memory in MB
      type: int
      sample: 2048
    vcpus:
      description: Number of virtual CPUs
      type: int
      sample: 2
    disk:
      description: OS disk size in GB
      type: int
      sample: 20
    data_disk:
      description: Data disk size in GB
      type: int
      sample: 0
    ip:
      description: Assigned IP address
      type: str
      sample: "192.168.1.10"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KomputeModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        memory=dict(immutable=True, required=True, type='int'),
        vcpus=dict(immutable=True, required=True, type='int'),
        disk=dict(immutable=True, required=True, type='int'),
        data_disk=dict(immutable=False, default=0, type='int'),
        project=dict(required=True, type='str'),
        zone=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'kompute'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        kompute = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, kompute))

        if state == 'present' and not kompute:
            kompute = self._create()
            self.exit_json(changed=True, kompute=kompute.to_dict(), action="create")
        elif state == 'present' and kompute:
            update, kompute = self._build_update(kompute)
            if update:
                kompute = self._update(kompute)
            self.exit_json(changed=bool(update), kompute=kompute.to_dict(), action="update")
        elif state == 'absent' and kompute:
            self._delete(kompute)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not kompute:
            self.exit_json(changed=False)

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        zone = self._find_resource_by_name('zone', self.params['zone'])
        if not zone:
            self.fail_json(msg=f"Zone '{self.params['zone']}' not found")
        kompute = self.sdk.Kompute.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_zone_kompute(project.id, zone.id, kompute)

    def _update(self, kompute):
        return self.sdk.KomputeApi(self.client).update_kompute(kompute.id, kompute)

    def _delete(self, kompute):
        return self.sdk.KomputeApi(self.client).delete_kompute(kompute.id)


def main():
    module = KomputeModule()
    module()


if __name__ == '__main__':
    main()
