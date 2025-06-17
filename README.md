<p align="center">
  <a href="https://www.kowabunga.cloud/?utm_source=github&utm_medium=logo" target="_blank">
    <picture>
      <source srcset="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-white.png" media="(prefers-color-scheme: dark)" />
      <source srcset="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-black.png" media="(prefers-color-scheme: light), (prefers-color-scheme: no-preference)" />
      <img src="https://raw.githubusercontent.com/kowabunga-cloud/infographics/master/art/kowabunga-title-black.png" alt="Kowabunga" width="800">
    </picture>
  </a>
</p>

# Ansible Kowabunga Collection

Ansible Kowabunga collection aka `kowabunga.cloud` provides:

- Ansible roles and playbooks for automating deployment of **Kowabunga core modules**:
  - **Kahuna** API orchestration engine,
  - **Koala** Web interface,
  - **Kiwi** SD-WAN nodes,
  - **Kaktus** HCI storage and computing nodes,
- Ansible modules and plugins for managing Kowabunga cloud resources.

It is supported and maintained by the Kowabunga community.

[![License: Apache License, Version 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://spdx.org/licenses/Apache-2.0.html)
[![time tracker](https://wakatime.com/badge/github/kowabunga-cloud/ansible-collections-kowabunga.svg)](https://wakatime.com/badge/github/kowabunga-cloud/ansible-collections-kowabunga)
![Code lines](https://sloc.xyz/github/kowabunga-cloud/ansible-collections-kowabunga/?category=code)
![Comments](https://sloc.xyz/github/kowabunga-cloud/ansible-collections-kowabunga/?category=comments)
![COCOMO](https://sloc.xyz/github/kowabunga-cloud/ansible-collections-kowabunga/?category=cocomo&avg-wage=100000)

## Current Releases

| Project            | Release Badge                                                                                       |
|--------------------|-----------------------------------------------------------------------------------------------------|
| **Kowabunga**           | [![Kowabunga Release](https://img.shields.io/github/v/release/kowabunga-cloud/kowabunga)](https://github.com/kowabunga-cloud/kowabunga/releases) |
| **Kowabunga Python SDK**     | [![Kowabunga Python SDK Release](https://img.shields.io/github/v/release/kowabunga-cloud/kowabunga-python)](https://github.com/kowabunga-cloud/kowabunga-python/releases) |
| **Kowabunga Ansible Collection**     | [![Kowabunga Ansible Collection Release](https://img.shields.io/github/v/release/kowabunga-cloud/ansible-collections-kowabunga)](https://github.com/kowabunga-cloud/ansible-collections-kowabunga/releases) |

Check out the [list of released versions](https://github.com/kowabunga-cloud/ansible-collections-kowabunga/releases).

[kowabunga-python]: https://github.com/kowabunga-cloud/kowabunga-python

## Installation

For using this collection, first you have to install Python `kowabunga` package on your Ansible controller:

```sh
pip install kowabunga
```

[Kowabunga SDK][kowabunga-python] has to be available on the Ansible host running the Kowabunga modules. Depending on the Ansible playbook and roles you use, this host is not necessarily the Ansible controller. Sometimes Ansible might invoke a non-standard Python interpreter on the target Ansible host.

Before using this collection, you have to install it with `ansible-galaxy`:

```sh
ansible-galaxy collection install kowabunga.cloud
```

You can also include it in a `requirements.yml` file:

```yaml
collections:
- name: kowabunga.cloud
```

And then install it with:

```sh
ansible-galaxy collection install -r requirements.yml
```

## Usage

To use a module from the Ansible Kowabunga collection, call them by their Fully Qualified Collection Name (FQCN), composed of their namespace, collection name and module name:

```yaml
---
- hosts: localhost
  tasks:
    - name: Create Project
      kowabunga.cloud.project:
        endpoint: https://kowabunga.acme.com
        api_key: SECRET_API_KEY
        name: my-project
        description: My Project
        teams:
          - dev
          - ops
        regions:
          - eu-west-1
        state: present
```

[Ansible module defaults](https://docs.ansible.com/ansible/latest/user_guide/playbooks_module_defaults.html) are supported as well:

```
---
- hosts: localhost

  module_defaults:
    group/kowabunga.cloud.kowabunga:
      endpoint: https://kowabunga.acme.com
      api_key: SECRET_API_KEY

  tasks:
    - name: Create Project
      kowabunga.cloud.project:
        name: my-project
        description: My Project
        teams:
          - dev
          - ops
        regions:
          - eu-west-1
        state: present
```

<!-- ## Documentation -->

<!-- See collection docs at Ansible's main page: -->

<!-- * [kowabunga.cloud collection docs (version released in Ansible package)]( -->
<!--   https://docs.ansible.com/ansible/latest/collections/kowabunga/cloud/index.html) -->

<!-- * [kowabunga.cloud collection docs (devel version)]( -->
<!--   https://docs.ansible.com/ansible/devel/collections/kowabunga/cloud/index.html) -->

## License

Licensed under [Apache License, Version 2.0](https://opensource.org/license/apache-2-0), see [`LICENSE`](LICENSE).
