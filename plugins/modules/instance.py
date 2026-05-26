#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: instance
short_description: Manage Kowabunga virtual machine instances
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga virtual machine instance.
options:
  name:
    description:
      - Name for the instance.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the instance.
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
  adapters:
    description:
      - List of network adapter names (or IDs) to attach to the instance.
    type: list
  volumes:
    description:
      - List of storage volume names (or IDs) to attach to the instance.
    type: list
  project:
    description:
      - Name (or ID) of the project where the instance will be created.
    required: true
    type: str
  zone:
    description:
      - Name (or ID) of the availability zone where the instance will be created.
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
- name: Create an instance
  kowabunga.cloud.instance:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vm-01
    memory: 2048
    vcpus: 2
    project: my-project
    zone: eu-west-1a

- name: Delete an instance
  kowabunga.cloud.instance:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: vm-01
    project: my-project
    zone: eu-west-1a
    state: absent
'''

RETURN = r'''
instance:
  description: Dictionary describing the instance.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Instance ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Instance name
      type: str
      sample: "vm-01"
    description:
      description: Instance description
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
    adapters:
      description: List of attached adapter IDs
      type: list
      sample: ["6850281677f2462b6919dbe6"]
    volumes:
      description: List of attached volume IDs
      type: list
      sample: ["6850281677f2462b6919dbe7"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class InstanceModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        memory=dict(immutable=True, required=True, type='int'),
        vcpus=dict(immutable=True, required=True, type='int'),
        adapters=dict(immutable=False, type='list'),
        volumes=dict(immutable=False, type='list'),
        project=dict(required=True, type='str'),
        zone=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'instance'
    resource_arg_maps = ['adapters', 'volumes']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        instance = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, instance))

        if state == 'present' and not instance:
            instance = self._create()
            self.exit_json(changed=True, instance=instance.to_dict(), action="create")
        elif state == 'present' and instance:
            update, instance = self._build_update(instance)
            if update:
                instance = self._update(instance)
            self.exit_json(changed=bool(update), instance=instance.to_dict(), action="update")
        elif state == 'absent' and instance:
            self._delete(instance)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not instance:
            self.exit_json(changed=False)

    def _find_adapters(self):
        if not self.params.get('adapters'):
            return []
        return self._find_resources_by_name('adapter', 'adapters')

    def _find_volumes(self):
        if not self.params.get('volumes'):
            return []
        return self._find_resources_by_name('volume', 'volumes')

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        zone = self._find_resource_by_name('zone', self.params['zone'])
        if not zone:
            self.fail_json(msg=f"Zone '{self.params['zone']}' not found")
        instance = self.sdk.Instance.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_zone_instance(project.id, zone.id, instance)

    def _update(self, instance):
        return self.sdk.InstanceApi(self.client).update_instance(instance.id, instance)

    def _delete(self, instance):
        return self.sdk.InstanceApi(self.client).delete_instance(instance.id)


def main():
    module = InstanceModule()
    module()


if __name__ == '__main__':
    main()
