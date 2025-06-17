#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

class ModuleDocFragment(object):

    # Standard kowabunga documentation fragment
    DOCUMENTATION = r'''
options:
  endpoint:
    description:
      - HTTPS(S) URI of the Kowabunga Kahuna endpoint.
        Should be formatted as https://kowabunga.acme.com for example.
    required: true
    type: str
  api_key:
    description:
      - Private API key used to connect with specified Kowabunga Kahuna endpoint.
        Recommended to be encrypted using Ansible Vault or SOPS.
    required: true
    type: str
requirements:
  - "python >= 3.8"
  - "kowabunga >= 0.52.5"
'''
