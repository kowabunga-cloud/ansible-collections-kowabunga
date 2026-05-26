#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: record
short_description: Manage Kowabunga DNS records
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga DNS record.
  - Specify either C(project) or C(region) to determine where the record is created.
options:
  name:
    description:
      - Name for the DNS record (hostname or FQDN).
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the DNS record.
    type: str
  addresses:
    description:
      - List of IP addresses for the DNS record.
    required: true
    type: list
  project:
    description:
      - Name (or ID) of the project where the DNS record will be created.
      - Mutually exclusive with C(region).
    type: str
  region:
    description:
      - Name (or ID) of the region where the DNS record will be created.
      - Mutually exclusive with C(project).
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
- name: Create a project DNS record
  kowabunga.cloud.record:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: myapp
    addresses:
      - 192.168.1.10
    project: my-project

- name: Create a region DNS record
  kowabunga.cloud.record:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: service
    addresses:
      - 10.0.0.1
    region: eu-west-1

- name: Delete a DNS record
  kowabunga.cloud.record:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: myapp
    project: my-project
    state: absent
'''

RETURN = r'''
record:
  description: Dictionary describing the DNS record.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Record ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Record name
      type: str
      sample: "myapp"
    description:
      description: Record description
      type: str
      sample: "My App"
    domain:
      description: DNS domain
      type: str
      sample: "project.acme.local"
    addresses:
      description: List of IP addresses
      type: list
      sample: ["192.168.1.10"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class RecordModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        addresses=dict(immutable=False, required=True, type='list'),
        project=dict(type='str'),
        region=dict(type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True,
        mutually_exclusive=[['project', 'region']],
        required_one_of=[['project', 'region']],
    )
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        record = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, record))

        if state == 'present' and not record:
            record = self._create()
            self.exit_json(changed=True, record=record.to_dict(), action="create")
        elif state == 'present' and record:
            update, record = self._build_update(record)
            if update:
                record = self._update(record)
            self.exit_json(changed=bool(update), record=record.to_dict(), action="update")
        elif state == 'absent' and record:
            self._delete(record)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not record:
            self.exit_json(changed=False)

    def _read(self):
        name = self.params['name']
        if self.params.get('project'):
            project = self._find_resource_by_name('project', self.params['project'])
            if not project:
                return None
            return self._find_record_in_project(name, project.id)
        else:
            region = self._find_resource_by_name('region', self.params['region'])
            if not region:
                return None
            return self._find_record_in_region(name, region.id)

    def _create(self):
        record = self.sdk.DnsRecord.from_dict(self.kwargs)
        if self.params.get('project'):
            project = self._find_resource_by_name('project', self.params['project'])
            if not project:
                self.fail_json(msg=f"Project '{self.params['project']}' not found")
            api = self.sdk.ProjectApi(self.client)
            return api.create_project_dns_record(project.id, record)
        else:
            region = self._find_resource_by_name('region', self.params['region'])
            if not region:
                self.fail_json(msg=f"Region '{self.params['region']}' not found")
            api = self.sdk.RegionApi(self.client)
            return api.create_region_dns_record(region.id, record)

    def _update(self, record):
        return self.sdk.RecordApi(self.client).update_dns_record(record.id, record)

    def _delete(self, record):
        return self.sdk.RecordApi(self.client).delete_dns_record(record.id)


def main():
    module = RecordModule()
    module()


if __name__ == '__main__':
    main()
