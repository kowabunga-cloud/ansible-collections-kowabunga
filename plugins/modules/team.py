#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: team
short_description: Manage Kowabunga teams
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga team.
options:
  name:
    description:
      - Name for the team.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the team.
    type: str
  users:
    description:
      - List of user names (or IDs) belonging to the team.
    required: true
    type: list
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
- name: Create a team
  kowabunga.cloud.team:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: dev
    users:
      - alice
      - bob

- name: Delete a team
  kowabunga.cloud.team:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: dev
    state: absent
'''

RETURN = r'''
team:
  description: Dictionary describing the team.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Team ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Team name
      type: str
      sample: "dev"
    description:
      description: Team description
      type: str
      sample: "Development team"
    users:
      description: List of user IDs
      type: list
      sample: ["6850281677f2462b6919dbe6"]
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class TeamModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        users=dict(immutable=False, required=True, type='list'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'team'
    resource_arg_maps = ['users']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        team = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, team))

        if state == 'present' and not team:
            team = self._create()
            self.exit_json(changed=True, team=team.to_dict(), action="create")
        elif state == 'present' and team:
            update, team = self._build_update(team)
            if update:
                team = self._update(team)
            self.exit_json(changed=bool(update), team=team.to_dict(), action="update")
        elif state == 'absent' and team:
            self._delete(team)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not team:
            self.exit_json(changed=False)

    def _create(self):
        team = self.sdk.Team.from_dict(self.kwargs)
        api = self.sdk.TeamApi(self.client)
        return api.create_team(team)

    def _update(self, team):
        return self.sdk.TeamApi(self.client).update_team(team.id, team)

    def _delete(self, team):
        return self.sdk.TeamApi(self.client).delete_team(team.id)


def main():
    module = TeamModule()
    module()


if __name__ == '__main__':
    main()
