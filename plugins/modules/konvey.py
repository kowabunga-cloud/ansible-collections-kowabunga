#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: konvey
short_description: Manage Kowabunga load balancers
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Konvey load balancer.
options:
  name:
    description:
      - Name for the load balancer.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the load balancer.
    type: str
  failover:
    description:
      - Whether to enable failover for the load balancer.
    default: true
    type: bool
  endpoints:
    description:
      - List of endpoint definitions. Each endpoint requires name, port, protocol (tcp/udp),
        and backends dict with addresses list and optionally port.
    required: true
    type: list
  project:
    description:
      - Name (or ID) of the project where the load balancer will be created.
    required: true
    type: str
  zone:
    description:
      - Name (or ID) of the availability zone where the load balancer will be created.
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
- name: Create a load balancer
  kowabunga.cloud.konvey:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: lb-01
    endpoints:
      - name: http
        port: 80
        protocol: tcp
        backends:
          addresses:
            - 192.168.1.10
            - 192.168.1.11
    project: my-project
    zone: eu-west-1a

- name: Delete a load balancer
  kowabunga.cloud.konvey:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: lb-01
    project: my-project
    zone: eu-west-1a
    state: absent
'''

RETURN = r'''
konvey:
  description: Dictionary describing the load balancer.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Konvey ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Konvey name
      type: str
      sample: "lb-01"
    description:
      description: Konvey description
      type: str
      sample: "Load balancer 01"
    vip:
      description: Virtual IP address
      type: str
      sample: "192.168.1.100"
    failover:
      description: Failover enabled
      type: bool
      sample: true
    endpoints:
      description: List of endpoint configurations
      type: list
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KonveyModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        failover=dict(immutable=False, default=True, type='bool'),
        endpoints=dict(immutable=False, required=True, type='list'),
        project=dict(required=True, type='str'),
        zone=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'konvey'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        konvey = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, konvey))

        if state == 'present' and not konvey:
            konvey = self._create()
            self.exit_json(changed=True, konvey=konvey.to_dict(), action="create")
        elif state == 'present' and konvey:
            update, konvey = self._build_update(konvey)
            if update:
                konvey = self._update(konvey)
            self.exit_json(changed=bool(update), konvey=konvey.to_dict(), action="update")
        elif state == 'absent' and konvey:
            self._delete(konvey)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not konvey:
            self.exit_json(changed=False)

    def _create(self):
        project = self._find_resource_by_name('project', self.params['project'])
        if not project:
            self.fail_json(msg=f"Project '{self.params['project']}' not found")
        zone = self._find_resource_by_name('zone', self.params['zone'])
        if not zone:
            self.fail_json(msg=f"Zone '{self.params['zone']}' not found")
        konvey = self.sdk.Konvey.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project_zone_konvey(project.id, zone.id, konvey)

    def _update(self, konvey):
        return self.sdk.KonveyApi(self.client).update_konvey(konvey.id, konvey)

    def _delete(self, konvey):
        return self.sdk.KonveyApi(self.client).delete_konvey(konvey.id)


def main():
    module = KonveyModule()
    module()


if __name__ == '__main__':
    main()
