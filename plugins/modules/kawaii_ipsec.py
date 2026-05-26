#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: kawaii_ipsec
short_description: Manage Kowabunga IPsec connections
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga Kawaii IPsec connection.
options:
  name:
    description:
      - Name for the IPsec connection.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the IPsec connection.
    type: str
  remote_ip:
    description:
      - Remote peer IP address.
      - This attribute cannot be updated.
    required: true
    type: str
  remote_subnet:
    description:
      - Remote subnet in CIDR notation.
      - This attribute cannot be updated.
    required: true
    type: str
  pre_shared_key:
    description:
      - Pre-shared key for IKE authentication.
    required: true
    type: str
  dpd_timeout_action:
    description:
      - Action to take when DPD timeout is reached.
    type: str
  dpd_timeout:
    description:
      - DPD timeout duration.
    type: str
  start_action:
    description:
      - Action to take at connection start.
    type: str
  rekey_time:
    description:
      - Time interval before re-keying.
    type: str
  phase1_lifetime:
    description:
      - Phase 1 SA lifetime.
    type: str
  phase1_dh_group_number:
    description:
      - Phase 1 Diffie-Hellman group number.
    required: true
    type: int
  phase1_integrity_algorithm:
    description:
      - Phase 1 integrity algorithm.
    required: true
    type: str
  phase1_encryption_algorithm:
    description:
      - Phase 1 encryption algorithm.
    required: true
    type: str
  phase2_lifetime:
    description:
      - Phase 2 SA lifetime.
    type: str
  phase2_dh_group_number:
    description:
      - Phase 2 Diffie-Hellman group number.
    required: true
    type: int
  phase2_integrity_algorithm:
    description:
      - Phase 2 integrity algorithm.
    required: true
    type: str
  phase2_encryption_algorithm:
    description:
      - Phase 2 encryption algorithm.
    required: true
    type: str
  kawaii:
    description:
      - Name (or ID) of the kawaii gateway where the IPsec connection will be created.
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
- name: Create an IPsec connection
  kowabunga.cloud.kawaii_ipsec:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: ipsec-to-hq
    remote_ip: 203.0.113.1
    remote_subnet: 10.0.0.0/8
    pre_shared_key: mysecretkey
    phase1_dh_group_number: 14
    phase1_integrity_algorithm: sha256
    phase1_encryption_algorithm: aes256
    phase2_dh_group_number: 14
    phase2_integrity_algorithm: sha256
    phase2_encryption_algorithm: aes256
    kawaii: gw-01

- name: Delete an IPsec connection
  kowabunga.cloud.kawaii_ipsec:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: ipsec-to-hq
    kawaii: gw-01
    state: absent
'''

RETURN = r'''
kawaii_ipsec:
  description: Dictionary describing the IPsec connection.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: IPsec connection ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: IPsec connection name
      type: str
      sample: "ipsec-to-hq"
    remote_ip:
      description: Remote peer IP
      type: str
      sample: "203.0.113.1"
    remote_subnet:
      description: Remote subnet
      type: str
      sample: "10.0.0.0/8"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class KawaiiIpsecModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        remote_ip=dict(immutable=True, required=True, type='str'),
        remote_subnet=dict(immutable=True, required=True, type='str'),
        pre_shared_key=dict(immutable=False, required=True, type='str', no_log=True),
        dpd_timeout_action=dict(immutable=False, type='str'),
        dpd_timeout=dict(immutable=False, type='str'),
        start_action=dict(immutable=False, type='str'),
        rekey_time=dict(immutable=False, type='str'),
        phase1_lifetime=dict(immutable=False, type='str'),
        phase1_dh_group_number=dict(immutable=False, required=True, type='int'),
        phase1_integrity_algorithm=dict(immutable=False, required=True, type='str'),
        phase1_encryption_algorithm=dict(immutable=False, required=True, type='str'),
        phase2_lifetime=dict(immutable=False, type='str'),
        phase2_dh_group_number=dict(immutable=False, required=True, type='int'),
        phase2_integrity_algorithm=dict(immutable=False, required=True, type='str'),
        phase2_encryption_algorithm=dict(immutable=False, required=True, type='str'),
        kawaii=dict(required=True, type='str'),
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
        ipsec = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, ipsec))

        if state == 'present' and not ipsec:
            ipsec = self._create()
            self.exit_json(changed=True, kawaii_ipsec=ipsec.to_dict(), action="create")
        elif state == 'present' and ipsec:
            update, ipsec = self._build_update(ipsec)
            if update:
                ipsec = self._update(ipsec)
            self.exit_json(changed=bool(update), kawaii_ipsec=ipsec.to_dict(), action="update")
        elif state == 'absent' and ipsec:
            self._delete(ipsec)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not ipsec:
            self.exit_json(changed=False)

    def _find_kawaii(self):
        kawaii = self._find_resource_by_name('kawaii', self.params['kawaii'])
        if not kawaii:
            self.fail_json(msg=f"Kawaii '{self.params['kawaii']}' not found")
        return kawaii

    def _read(self):
        kawaii = self._find_kawaii()
        return self._find_kawaii_ipsec_in_kawaii(self.params['name'], kawaii.id)

    def _create(self):
        kawaii = self._find_kawaii()
        ipsec = self.sdk.KawaiiIpSec.from_dict(self.kwargs)
        api = self.sdk.KawaiiApi(self.client)
        return api.create_kawaii_ip_sec(kawaii.id, ipsec)

    def _update(self, ipsec):
        kawaii = self._find_kawaii()
        return self.sdk.KawaiiApi(self.client).update_kawaii_ip_sec(kawaii.id, ipsec.id, ipsec)

    def _delete(self, ipsec):
        kawaii = self._find_kawaii()
        return self.sdk.KawaiiApi(self.client).delete_kawaii_ip_sec(kawaii.id, ipsec.id)


def main():
    module = KawaiiIpsecModule()
    module()


if __name__ == '__main__':
    main()
