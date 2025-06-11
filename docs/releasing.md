# Release process for Ansible Kowabunga collection

## Publishing to Ansible Galaxy

1. Create entry in [changelog.yaml](../changelogs/changelog.yaml) with changes since last release.
   * Modules should be in a separate section `modules`
   * Bugfixes and minor changes in their sections
2. Change version in [galaxy.yml](../galaxy.yml). Apply [Semantic Versioning](https://semver.org/):
   * Increase major version for breaking changes or modules were removed
   * Increase minor version when modules were added
   * Increase patch version for bugfixes
3. Run `antsibull-changelog release` command (run `pip install antsibull` before) to generate [CHANGELOG.rst](
   ../CHANGELOG.rst) and verify correctness of generated files.
4. Commit changes to `changelog.yaml` and `galaxy.yml`, submit patch and wait until it has been merged
5. Tag the release with version.
6. When your tag has been pushed in the previous step, our release workflow, defined n [release.yml](../.github/workflows/release.yml), will run automatically and publish a new release with your tag to [Ansible Galaxy](https://galaxy.ansible.com/kowabunga/cloud).
