#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: agent
short_description: Manage Kowabunga remote agents
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga remote agent.
options:
  name:
    description:
      - Name for the agent.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the agent.
    type: str
  type:
    description:
      - Agent type.
      - This attribute cannot be updated.
    required: true
    choices: [Kiwi, Kaktus]
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
- name: Create an agent
  kowabunga.cloud.agent:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: my-agent
    type: Kaktus

- name: Delete an agent
  kowabunga.cloud.agent:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: my-agent
    state: absent
'''

RETURN = r'''
agent:
  description: Dictionary describing the agent.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    id:
      description: Agent ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    name:
      description: Agent name
      type: str
      sample: "my-agent"
    description:
      description: Agent description
      type: str
      sample: "My agent"
    type:
      description: Agent type
      type: str
      sample: "Kaktus"
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule


class AgentModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        type=dict(immutable=True, required=True, type='str', choices=['Kiwi', 'Kaktus']),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'agent'
    resource_arg_maps = []

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        agent = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, agent))

        if state == 'present' and not agent:
            agent = self._create()
            self.exit_json(changed=True, agent=agent.to_dict(), action="create")
        elif state == 'present' and agent:
            update, agent = self._build_update(agent)
            if update:
                agent = self._update(agent)
            self.exit_json(changed=bool(update), agent=agent.to_dict(), action="update")
        elif state == 'absent' and agent:
            self._delete(agent)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not agent:
            self.exit_json(changed=False)

    def _create(self):
        agent = self.sdk.Agent.from_dict(self.kwargs)
        api = self.sdk.AgentApi(self.client)
        return api.create_agent(agent)

    def _update(self, agent):
        return self.sdk.AgentApi(self.client).update_agent(agent.id, agent)

    def _delete(self, agent):
        return self.sdk.AgentApi(self.client).delete_agent(agent.id)


def main():
    module = AgentModule()
    module()


if __name__ == '__main__':
    main()
