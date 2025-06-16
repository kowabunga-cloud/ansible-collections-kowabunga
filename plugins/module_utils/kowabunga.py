# Copyright (c) The Kowabunga Project
# Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0.txt)
# SPDX-License-Identifier: Apache-2.0

import abc
import copy
from ansible.module_utils.six import raise_from
try:
    from ansible.module_utils.compat.version import StrictVersion
except ImportError:
    try:
        from distutils.version import StrictVersion
    except ImportError as exc:
        raise_from(ImportError('To use this plugin or module with ansible-core'
                               ' < 2.11, you need to use Python < 3.12 with '
                               'distutils.version present'), exc)
import importlib
import os

from ansible.module_utils.basic import AnsibleModule

CUSTOM_VAR_PARAMS = ['min_ver', 'max_ver']

MINIMUM_SDK_VERSION = '0.52.5'
MAXIMUM_SDK_VERSION = None

def ensure_compatibility(version, min_version=None, max_version=None):
    """ Raises ImportError if the specified version does not
        meet the minimum and maximum version requirements"""

    if min_version and MINIMUM_SDK_VERSION:
        min_version = max(StrictVersion(MINIMUM_SDK_VERSION),
                          StrictVersion(min_version))
    elif MINIMUM_SDK_VERSION:
        min_version = StrictVersion(MINIMUM_SDK_VERSION)

    if max_version and MAXIMUM_SDK_VERSION:
        max_version = min(StrictVersion(MAXIMUM_SDK_VERSION),
                          StrictVersion(max_version))
    elif MAXIMUM_SDK_VERSION:
        max_version = StrictVersion(MAXIMUM_SDK_VERSION)

    if min_version and StrictVersion(version) < min_version:
        raise ImportError(
            "Version MUST be >={min_version} and <={max_version}, but"
            " {version} is smaller than minimum version {min_version}"
            .format(version=version,
                    min_version=min_version,
                    max_version=max_version))

    if max_version and StrictVersion(version) > max_version:
        raise ImportError(
            "Version MUST be >={min_version} and <={max_version}, but"
            " {version} is larger than maximum version {max_version}"
            .format(version=version,
                    min_version=min_version,
                    max_version=max_version))

def kowabunga_argument_spec(**kwargs):
    spec = dict(
        endpoint=dict(required=True, type='str'),
        api_key=dict(required=True, type='str'),
    )
    # Filter out all our custom parameters before passing to AnsibleModule
    kwargs_copy = copy.deepcopy(kwargs)
    for v in kwargs_copy.values():
        for c in CUSTOM_VAR_PARAMS:
            v.pop(c, None)
    spec.update(kwargs_copy)
    return spec


class KowabungaModule:
    """Kowabunga Module is a base class for all Kowabunga Module classes.

    The class has `run` function that should be overriden in child classes,
    the provided methods include:

    Methods:
        params: Dictionary of Ansible module parameters.
        module_name: Module name (i.e. server_action)
        sdk_version: Version of used Kowabunga SDK.
        results: Dictionary for return of Ansible module,
                 must include `changed` keyword.
        exit, exit_json: Exit module and return data inside, must include
                         changed` keyword in a data.
        fail, fail_json: Exit module with failure, has `msg` keyword to
                         specify a reason of failure.
        client: Connection to SDK object.
        log: Print message to system log.
        debug: Print debug message to system log, prints if Ansible Debug is
               enabled or verbosity is more than 2.
        check_deprecated_names: Function that checks if module was called with
                                a deprecated name and prints the correct name
                                with deprecation warning.
        check_versioned: helper function to check that all arguments are known
                         in the current SDK version.
        run: method that executes and shall be overriden in inherited classes.

    Args:
        deprecated_names: Should specify deprecated modules names for current
                          module.
        argument_spec: Used for construction of Kowabunga common arguments.
        module_kwargs: Additional arguments for Ansible Module.
    """

    deprecated_names = ()
    argument_spec = {}
    module_kwargs = {}
    module_min_sdk_version = None
    module_max_sdk_version = None

    def __init__(self):
        """Initialize Kowabunga base class.

        Set up variables, connection to SDK and check if there are
        deprecated names.
        """
        self.ansible = AnsibleModule(kowabunga_argument_spec(**self.argument_spec), **self.module_kwargs)
        self.params = self.ansible.params
        self.module_name = self.ansible._name
        self.check_mode = self.ansible.check_mode
        self.sdk_version = None
        self.results = {'changed': False}
        self.exit = self.exit_json = self.ansible.exit_json
        self.fail = self.fail_json = self.ansible.fail_json
        self.warn = self.ansible.warn
        self.sdk, self.client = self.kowabunga_cloud_from_module()

    def log(self, msg):
        """Prints log message to system log.

        Arguments:
            msg {str} -- Log message
        """
        self.ansible.log(msg)

    def debug(self, msg):
        """Prints debug message to system log

        Arguments:
            msg {str} -- Debug message.
        """
        if self.ansible._debug or self.ansible._verbosity > 2:
            self.ansible.log(
                " ".join(['[DEBUG]', msg]))

    def kowabunga_cloud_from_module(self):
        """Sets up connection to Kowabunga using provided options. Checks if all
           provided variables are supported for the used SDK version.
        """
        try:
            # Due to the name shadowing we should import other way
            sdk = importlib.import_module('kowabunga')
            self.sdk_version = sdk.__version__
        except ImportError:
            self.fail_json(msg='kowabunga is required for this module')

        try:
            ensure_compatibility(self.sdk_version,
                                 self.module_min_sdk_version,
                                 self.module_max_sdk_version)
        except ImportError as e:
            self.fail_json(
                msg="Incompatible kowabunga library found: {error}."
                    .format(error=str(e)))

        try:
            endpoint = self.params['endpoint']
            if endpoint[-1] == "/":
                endpoint = endpoint[:-1]

            cfg = sdk.Configuration(
                host = f"{endpoint}/api/v1"
            )
            cfg.api_key['ApiKeyAuth'] = self.params['api_key']

            return sdk, sdk.ApiClient(cfg)
        except sdk.rest.ApiException as e:
            # Probably an endpoint configuration/login error
            self.fail_json(msg=str(e))

    # Filter out all arguments that are not from current SDK version
    def check_versioned(self, **kwargs):
        """Check that provided arguments are supported by current SDK version

        Returns:
            versioned_result {dict} dictionary of only arguments that are
                                    supported by current SDK version. All others
                                    are dropped.
        """
        versioned_result = {}
        for var_name in kwargs:
            if ('min_ver' in self.argument_spec[var_name]
                    and StrictVersion(self.sdk_version) < self.argument_spec[var_name]['min_ver']):
                continue
            if ('max_ver' in self.argument_spec[var_name]
                    and StrictVersion(self.sdk_version) > self.argument_spec[var_name]['max_ver']):
                continue
            versioned_result.update({var_name: kwargs[var_name]})
        return versioned_result

    # Fail on empty resource lists
    def _verify_list_param(self, l, param):
        """Check that provided resource list is non-empty.
        """
        if len(l) == 0:
            params = {
                'msg': f"Invalid or non existant {param}",
                param: self.params[param],
            }
            self.ansible.fail_json(**params)

    def _will_change(self, state, obj):
        """Check if resource object's update will trigger any change.

        Returns:
            {bool} triggered update status.
        """
        if state == 'present' and not obj:
            return True
        elif state == 'present' and obj:
            update, _ = self._build_update(obj)
            return bool(update)
        elif state == 'absent' and obj:
            return True

        # state == 'absent' and not obj:
        return False

    def _build_kwargs(self):
        """Construct a list of kwargs to be used to create/update resource objects.
        """
        self.kwargs = dict((k, self.params[k]) for k in self.create_params if self.params[k] is not None)
        for k in self.resource_arg_maps:
            func = getattr(self, f'_find_{k}')
            self.kwargs[k] = func()

    def _build_params(self):
        """Set lists of (in)mutable kwargs parameters.
        """
        self.update_mutable_params = [k for k in self.argument_spec
                                      if 'immutable' in self.argument_spec[k]
                                      and not self.argument_spec[k]['immutable']]
        self.update_immutable_params = [k for k in self.argument_spec
                                        if 'immutable' in self.argument_spec[k]
                                        and self.argument_spec[k]['immutable']]
        self.create_params = self.update_mutable_params + self.update_immutable_params

    # Update resource object from kwargs
    def _build_update(self, obj):
        """Update resource object from provided kwargs parameters.

        Arguments:
            obj {obj}              -- resource object to be updated.

        Returns:
            {bool} whether the original resource object has been updated.
            obj {obj} resource object.
        """
        non_updateable_keys = [k for k in self.update_immutable_params
                               if self.params[k] is not None
                               and self.params[k] != obj.to_dict()[k]]

        if non_updateable_keys:
            self.fail_json(msg='Cannot update parameters {0}'.format(non_updateable_keys))

        attributes = dict((k, self.kwargs[k])
                          for k in self.update_mutable_params
                          if (k in self.kwargs and self.kwargs[k] is not None)
                          and (k not in obj.to_dict() or self.kwargs[k] != obj.to_dict()[k]))

        if attributes:
            return True, obj.model_copy(update=attributes, deep=True)

        return False, obj

    # Generic wrapper to retrieve resource ID from their resource name
    def _find_resource_by_name(self, res, name=None):
        """Retrieve a resources based on it's name or ID provided as parameter.

        Arguments:
            res {str}       -- lower-case resource type.
            name {str}      -- resource name or ID.

        Returns:
            r {obj} resource object.
        """
        if not name:
            name = self.params['name']
        func = getattr(self.sdk, f'{res[0].upper()}{res[1:]}Api')
        api = func(self.client)
        func_list = getattr(api, f'list_{res}s')
        for id in func_list():
            func_read = getattr(api, f'read_{res}')
            r = func_read(id)
            if name in [r.id, r.name]:
                return r
        return None

    # Generic wrapper to retrieve list of resource IDs from their resource names
    def _find_resources_by_name(self, res, p, strict=False):
        """Provides a list of resources IDs based on resources names provided as parameter.

        Arguments:
            res {str}       -- lower-case resource type.
            p {str}         -- parameter name from kwargs.
            strict {bool}   -- whether to bail on empty list result.

        Returns:
            ids {list} list of requested resource IDs.
        """
        ids = []
        func = getattr(self.sdk, f'{res[0].upper()}{res[1:]}Api')
        api = func(self.client)
        func_list = getattr(api, f'list_{res}s')
        for id in func_list():
            func_read = getattr(api, f'read_{res}')
            r = func_read(id)
            for i in self.params[p]:
                if i in [r.id, r.name]:
                    ids.append(id)
        if strict:
            self._verify_list_param(ids, p)
        return ids

    def _find_teams(self):
        """Retrieve list of team resource IDs from requested team names.
        """
        return self._find_resources_by_name('team', 'teams', strict=True)

    def _find_regions(self):
        """Retrieve list of region resource IDs from requested region names.
        """
        return self._find_resources_by_name('region', 'regions', strict=True)

    @abc.abstractmethod
    def run(self):
        """Function for overriding in inhetired classes, it's executed by default.
        """
        pass

    def __call__(self):
        """Execute `run` function when calling the class.
        """
        try:
            results = self.run()
            if results and isinstance(results, dict):
                self.ansible.exit_json(**results)
        except self.sdk.exceptions.OpenApiException as e:
            params = {
                'msg': str(e),
            }
            self.ansible.fail_json(**params)
        # if we got to this place, modules didn't exit
        self.ansible.exit_json(**self.results)

    def _read(self):
        """Read a generic resource object.
        """
        return self._find_resource_by_name(self.resource_spec)

