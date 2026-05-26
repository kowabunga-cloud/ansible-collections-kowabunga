#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: user
short_description: Manage Kowabunga users
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga user.
options:
  name:
    description:
      - Name for the user.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the user.
    type: str
  email:
    description:
      - Email address for the user.
      - This attribute cannot be updated.
    required: true
    type: str
  role:
    description:
      - Role assigned to the user.
    required: true
    choices: [superAdmin, projectAdmin, user]
    type: str
  notifications:
    description:
      - Whether the user receives notifications.
    default: false
    type: bool
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
- name: Create a user
  kowabunga.cloud.user:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: alice
    email: alice@acme.com
    role: user

- name: Delete a user
  kowabunga.cloud.user:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: alice
    state: absent
'''

RETURN = r'''
user:
  description: Dictionary describing the user.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: User ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: User name
      type: str
      sample: "alice"
    description:
      description: User description
      type: str
      sample: "Alice"
    email:
      description: User email
      type: str
      sample: "alice@acme.com"
    role:
      description: User role
      type: str
      sample: "user"
    notifications:
      description: Notifications enabled
      type: bool
      sample: false
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class UserModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        email=dict(immutable=True, required=True, type='str'),
        role=dict(immutable=False, required=True, type='str', choices=['superAdmin', 'projectAdmin', 'user']),
        notifications=dict(immutable=False, default=False, type='bool'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'user'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        user = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, user))

        if state == 'present' and not user:
            user = self._create()
            self.exit_json(changed=True, user=user.to_dict(), action="create")
        elif state == 'present' and user:
            update, user = self._build_update(user)
            if update:
                user = self._update(user)
            self.exit_json(changed=bool(update), user=user.to_dict(), action="update")
        elif state == 'absent' and user:
            self._delete(user)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not user:
            self.exit_json(changed=False)

    def _create(self):
        user = self.sdk.User.from_dict(self.kwargs)
        api = self.sdk.UserApi(self.client)
        return api.create_user(user)

    def _update(self, user):
        return self.sdk.UserApi(self.client).update_user(user.id, user)

    def _delete(self, user):
        return self.sdk.UserApi(self.client).delete_user(user.id)


def main():
    module = UserModule()
    module()


if __name__ == '__main__':
    main()
