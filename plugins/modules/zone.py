#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: zone
short_description: Manage Kowabunga availability zones
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga availability zone.
options:
  name:
    description:
      - Name for the zone.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the zone.
    type: str
  region:
    description:
      - Name (or ID) of the region where the zone will be created.
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
- name: Create a zone
  kowabunga.cloud.zone:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: eu-west-1a
    region: eu-west-1

- name: Delete a zone
  kowabunga.cloud.zone:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: eu-west-1a
    region: eu-west-1
    state: absent
'''

RETURN = r'''
zone:
  description: Dictionary describing the zone.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Zone ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Zone name
      type: str
      sample: "eu-west-1a"
    description:
      description: Zone description
      type: str
      sample: "EU West 1 - AZ A"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class ZoneModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        region=dict(required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'zone'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        zone = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, zone))

        if state == 'present' and not zone:
            zone = self._create()
            self.exit_json(changed=True, zone=zone.to_dict(), action="create")
        elif state == 'present' and zone:
            update, zone = self._build_update(zone)
            if update:
                zone = self._update(zone)
            self.exit_json(changed=bool(update), zone=zone.to_dict(), action="update")
        elif state == 'absent' and zone:
            self._delete(zone)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not zone:
            self.exit_json(changed=False)

    def _create(self):
        region = self._find_resource_by_name('region', self.params['region'])
        if not region:
            self.fail_json(msg=f"Region '{self.params['region']}' not found")
        zone = self.sdk.Zone.from_dict(self.kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_zone(region.id, zone)

    def _update(self, zone):
        return self.sdk.ZoneApi(self.client).update_zone(zone.id, zone)

    def _delete(self, zone):
        return self.sdk.ZoneApi(self.client).delete_zone(zone.id)


def main():
    module = ZoneModule()
    module()


if __name__ == '__main__':
    main()
