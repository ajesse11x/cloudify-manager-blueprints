########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import tempfile
import json

import fabric
import fabric.api
from fabric.context_managers import settings

from cloudify import ctx
from openstack_plugin_common import (
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    USE_EXTERNAL_RESOURCE_PROPERTY,
    Config
)
from openstack_plugin_common.floatingip import (
    FLOATINGIP_OPENSTACK_TYPE,
    IP_ADDRESS_PROPERTY
)
from cloudify_cli.bootstrap.tasks import (
    PUBLIC_IP_RUNTIME_PROPERTY,
    PROVIDER_RUNTIME_PROPERTY
)


def configure(openstack_config):

    manager_public_ip = _configure_public_ip()

    _set_provider_context()

    _copy_openstack_configuration_to_manager(manager_public_ip,
                                             openstack_config)


def _configure_public_ip():
    floatingip_runtime_props = \
        _get_runtime_props_by_node_name_and_openstack_type(
            'manager_server_ip', FLOATINGIP_OPENSTACK_TYPE)
    manager_public_ip = floatingip_runtime_props[IP_ADDRESS_PROPERTY]
    ctx.instance.runtime_properties[PUBLIC_IP_RUNTIME_PROPERTY] = \
        manager_public_ip
    return manager_public_ip


def _copy_openstack_configuration_to_manager(manager_public_ip,
                                             openstack_config):
    tmp = tempfile.mktemp()
    with open(tmp, 'w') as f:
        json.dump(openstack_config, f)
    with settings(host_string=manager_public_ip):
        fabric.api.put(tmp, Config.OPENSTACK_CONFIG_PATH_DEFAULT_PATH)


def _get_runtime_props_by_node_name_and_openstack_type(
        node_name, node_openstack_type):
    node_runtime_props = [v for k, v in ctx.capabilities.get_all().iteritems()
                          if k.startswith(node_name) and
                          v[OPENSTACK_TYPE_PROPERTY] == node_openstack_type][0]
    return node_runtime_props


def _set_provider_context():
    # Do not use this code section as a reference - it is a workaround for a
    #  deprecated feature and will be removed in the near future

    resources = dict()

    # the reference to storage only works the workflow is executed as a
    # local workflow (i.e. in a local environment context)
    node_instances = ctx._endpoint.storage.get_node_instances()
    nodes_by_id = \
        {node.id: node for node in ctx._endpoint.storage.get_nodes()}

    node_id_to_provider_context_field = {        
        'agents_security_group': 'agents_security_group',
        'management_security_group': 'management_security_group',
        'manager_server_ip': 'floating_ip',        
        'manager_server': 'management_server',
        'management_keypair': 'management_keypair',
        'agent_keypair': 'agents_keypair'
    }
    for node_instance in node_instances:
        if node_instance.node_id in node_id_to_provider_context_field:
            run_props = node_instance.runtime_properties
            props = nodes_by_id[node_instance.node_id].properties
            provider_context_field = \
                node_id_to_provider_context_field[node_instance.node_id]
            resources[provider_context_field] = {
                'external_resource': props[USE_EXTERNAL_RESOURCE_PROPERTY],
                'type': run_props[OPENSTACK_TYPE_PROPERTY],
                'id': run_props[OPENSTACK_ID_PROPERTY],
            }
            if node_instance.node_id == 'manager_server_ip':
                resources[provider_context_field]['ip'] = \
                    run_props[IP_ADDRESS_PROPERTY]
            else:
                resources[provider_context_field]['name'] = \
                    run_props[OPENSTACK_NAME_PROPERTY]

    provider = {
        'resources': resources
    }

    ctx.instance.runtime_properties[PROVIDER_RUNTIME_PROPERTY] = provider
