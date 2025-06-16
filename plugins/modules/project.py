#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: project
short_description: Manage Kowabunga projects
author: The Kowabunga Project
description:
  - Create, update or delete a Kowabunga project.
options:
  name:
    description:
      - Name for the project.
      - This attribute cannot be updated.
    required: true
    type: str
  description:
    description:
      - Description for the project.
    type: str
  domain:
    description:
      - Fully qualified domain name for project's kompute instances.
    type: str
  root_password:
    description:
      - Default root password to be set of project's kompute instances to be created (auto-generated if unspecified).
      - This attribute cannot be updated.
    type: str
  bootstrap_user:
    description:
      - Templated user to be created to bootstrap project's kompute instances.
      - This attribute cannot be updated.
    type: str
  bootstrap_pubkey:
    description:
      - Templated SSH public key to be used to bootstrap project's kompute instances.
      - This attribute cannot be updated.
    type: str
  subnet_size:
    description:
      - Private subnet netmask size (e.g. /26) requested at project's creation.
      - This attribute cannot be updated.
    default: 26
    type: int
  teams:
    description:
      - Name of teams with access to the project.
    type: list
  regions:
    description:
      - Name of regions where the project can create instances on.
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
- name: Create a project
  kowabunga.cloud.project:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: my-project
    teams:
      - dev
      - ops
    regions:
      - eu-west-1

- name: Delete a project
  kowabunga.cloud.project:
    endpoint: https://kowabunga.acme.com
    api_key: API_KEY
    name: my-project
    state: absent
'''

RETURN = r'''
project:
  description: Dictionary describing the project.
  returned: On success when I(state) is C(present).
  type: dict
  contains:
    name:
      description: Project name
      type: str
      sample: "my-project"
    description:
      description: Project description
      type: str
      sample: "My Project"
    domain:
      description: Private domain FQDN
      type: str
      sample: "project.acme.local"
    id:
      description: Project ID
      type: str
      sample: "6850281677f2462b6919dbe5"
    bootstrap_user:
      description: Username used to bootstrap project's kompute instances.
      type: str
      sample: "kowabunga"
    bootstrap_pubkey:
      description: SSH public key used to bootstrap project's kompute instances.
      type: str
      sample: "ecdsa-sha2-nistp256 AAA...e8sKU="
'''

from ansible_collections.kowabunga.cloud.plugins.module_utils.kowabunga import KowabungaModule

class ProjectModule(KowabungaModule):
    argument_spec = dict(
        name=dict(immutable=True, required=True, type='str'),
        description=dict(immutable=False, type='str'),
        domain=dict(immutable=False, type='str'),
        root_password=dict(immutable=True, type='str'),
        bootstrap_user=dict(immutable=True, type='str'),
        bootstrap_pubkey=dict(immutable=True, type='str'),
        subnet_size=dict(default=26, type='int'),
        teams=dict(immutable=False, required=True, type='list'),
        regions=dict(immutable=False, required=True, type='list'),
        state=dict(default='present', choices=['absent', 'present'])
    )
    module_kwargs = dict(
        supports_check_mode=True
    )
    resource_spec = 'project'
    resource_arg_maps = ['teams', 'regions']

    def run(self):
        self._build_params()
        self._build_kwargs()

        state = self.params['state']
        project = self._read()

        if self.ansible.check_mode:
            self.exit_json(changed=self._will_change(state, project))

        if state == 'present' and not project:
            # Create project
            project = self._create()
            self.exit_json(changed=True, project=project.to_dict(), action="create")
        elif state == 'present' and project:
            # Update project
            update, project = self._build_update(project)
            if update:
                project = self._update(project)
            self.exit_json(changed=bool(update), project=project.to_dict(), action="update")
        elif state == 'absent' and project:
            # Delete project
            self._delete(project)
            self.exit_json(changed=True, action="delete")
        elif state == 'absent' and not project:
            # Do nothing
            self.exit_json(changed=False)

    def _create(self):
        project = self.sdk.Project.from_dict(self.kwargs)
        api = self.sdk.ProjectApi(self.client)
        return api.create_project(project, self.params['subnet_size'])

    def _update(self, project):
        return self.sdk.ProjectApi(self.client).update_project(project.id, project)

    def _delete(self, project):
        return self.sdk.ProjectApi(self.client).delete_project(project.id)

def main():
    module = ProjectModule()
    module()

if __name__ == '__main__':
    main()
