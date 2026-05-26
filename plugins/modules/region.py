#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: region
short_description: Manage Kowabunga regions
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga region.
options:
  name:
    description:
      - Name for the region.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the region.
    type: str
  domain:
    description:
      - Fully qualified domain name for the region.
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
- name: Create a region
  kowabunga.cloud.region:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: eu-west-1
    domain: eu-west-1.acme.local

- name: Delete a region
  kowabunga.cloud.region:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: eu-west-1
    state: absent
'''

RETURN = r'''
region:
  description: Dictionary describing the region.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Region ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Region name
      type: str
      sample: "eu-west-1"
    description:
      description: Region description
      type: str
      sample: "EU West 1"
    domain:
      description: Region domain
      type: str
      sample: "eu-west-1.acme.local"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class RegionModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        domain=dict(immutable=False, required=True, type='str'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'region'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        region = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, region))

        if state == 'present' and not region:
            region = self._create()
            self.exit_json(changed=True, region=region.to_dict(), action="create")
        elif state == 'present' and region:
            update, region = self._build_update(region)
            if update:
                region = self._update(region)
            self.exit_json(changed=bool(update), region=region.to_dict(), action="update")
        elif state == 'absent' and region:
            self._delete(region)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not region:
            self.exit_json(changed=False)

    def _create(self):
        region = self.sdk.Region.from_dict(self.kwargs)
        api = self.sdk.RegionApi(self.client)
        return api.create_region(region)

    def _update(self, region):
        return self.sdk.RegionApi(self.client).update_region(region.id, region)

    def _delete(self, region):
        return self.sdk.RegionApi(self.client).delete_region(region.id)


def main():
    module = RegionModule()
    module()


if __name__ == '__main__':
    main()
