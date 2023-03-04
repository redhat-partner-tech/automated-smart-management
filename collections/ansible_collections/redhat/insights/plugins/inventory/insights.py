from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: insights
    plugin_type: inventory
    short_description: insights inventory source
    requirements:
        - requests >= 1.1
    description:
        - Get inventory hosts from the cloud.redhat.com inventory service.
        - Uses a YAML configuration file that ends with ``insights.(yml|yaml)``.
    extends_documentation_fragment:
        - constructed
    options:
      plugin:
        description: the name of this plugin, it should always be set to 'redhat.insights.insights' for this plugin to recognize it as it's own.
        required: True
        choices: ['redhat.insights.insights']
      user:
        description: Red Hat username
        required: True
        env:
            - name: INSIGHTS_USER
      password:
        description: Red Hat password
        required: True
        env:
            - name: INSIGHTS_PASSWORD
      server:
        description: Inventory server to connect to
        default: https://cloud.redhat.com
      selection:
        description: Choose what variable to use for ansible_host
        default: fqdn
        type: str
      staleness:
        description: Choose what hosts to return, based on staleness
        default: [ 'fresh', 'stale', 'unknown' ]
        type: list
      registered_with:
        description: Filter out any host not registered with the specified service
        default: insights
        type: str
      vars_prefix:
        description: prefix to apply to host variables
        default: insights_
        type: str
      get_patches:
        description: Fetch patching information for each system.
        required: False
        type: bool
        default: False
      get_system_advisories:
        description: Fetch advisories information for each system. If enabled will also fetch pathching information.
        required: False
        type: bool
        default: False
      get_system_packages:
        description: Fetch packages information for each system. If enabled will also fetch pathching information.
        required: False
        type: bool
        default: False
      get_tags:
        description: Fetch tag data for each system.
        required: False
        type: bool
        default: False
      filter_tags:
        description: Filter hosts with given tags
        required: False
        type: list
        default: []
'''

EXAMPLES = '''
# basic example using environment vars for auth
plugin: redhat.insights.insights

# create groups for patching
plugin: redhat.insights.insights
get_patches: yes
groups:
  patching: insights_patching.enabled
  stale: insights_patching.stale
  bug_patch: insights_patching.rhba_count > 0
  security_patch: insights_patching.rhsa_count > 0
  enhancement_patch: insights_patching.rhea_count > 0

# filter host by tags and create groups from tags
plugin: redhat.insights.insights
get_tags: True
filter_tags:
  - insights-client/env=prod
keyed_groups:
  - key: insights_tags['insights-client']
    prefix: insights
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.errors import AnsibleError
from distutils.version import LooseVersion

try:
    import requests
    if LooseVersion(requests.__version__) < LooseVersion('1.1.0'):
        raise ImportError
except ImportError:
    raise AnsibleError('This script requires python-requests 1.1 as a minimum version')


class InventoryModule(BaseInventoryPlugin, Constructable):
    ''' Host inventory parser for ansible using foreman as source. '''

    NAME = 'redhat.insights.insights'

    def get_patches(self, stale, get_system_advisories,get_system_packages,filter_tags):
        def get_system_patching_info(system_id,info):
            query = "api/patch/v1/export/systems"
            url = "%s/%s/%s/%s" % (self.server, query, system_id, info)
            response = self.session.get(url, auth=self.auth, headers=self.headers)
            if response.status_code != 200:
                raise AnsibleError("http error (%s): %s" %
                                    (response.status_code, response.text))
            system_patching_info = response.json()
            return system_patching_info
        def format_url(server,api_call,filter_tags):
            url = "%s/%s" % (server, api_call)
            if len(filter_tags) > 0:
                url = "%s&tags=%s" % (url, '&tags='.join(filter_tags))
            return url
        def add_patching_data(results,patching_info):
            for result in results:
                id = result['id']
                patching_info_result = get_system_patching_info(id,patching_info)
                result['attributes'][patching_info] = patching_info_result
            return results
        query = "api/patch/v1/systems?filter[stale]=%s" % stale
        url = format_url(self.server, query, filter_tags)
        results = []
        while url:
            response = self.session.get(url, auth=self.auth, headers=self.headers)
            if response.status_code != 200:
                raise AnsibleError("http error (%s): %s" %
                                   (response.status_code, response.text))
            elif response.status_code == 200:
                results += response.json()['data']
                next_page = response.json()['links']['next']
                if next_page:
                    url = format_url(self.server, next_page, filter_tags)
                else:
                    url = None 
        if get_system_advisories:
            results = add_patching_data(results,"advisories")
        if get_system_packages:
            results = add_patching_data(results,"packages")
        return results

    def get_tags(self, ids):
        first_url = "api/inventory/v1/hosts/%s/tags?per_page=50" % ','.join(ids)
        url = '%s/%s' % (self.server, first_url)
        results = {}

        while url:
            response = self.session.get(url, auth=self.auth, headers=self.headers)

            if response.status_code != 200:
                raise AnsibleError("http error (%s): %s" %
                                   (response.status_code, response.text))
            elif response.status_code == 200:
                results.update(response.json()['results'])
                total = response.json()['total']
                count = response.json()['count']
                per_page = response.json()['per_page']
                page = response.json()['page']
                if per_page * (page - 1) + count < total:
                    url = "%s/%s&page=%s" % (self.server, first_url, (page + 1))
                else:
                    url = None
        return results

    def parse_tags(self, tag_list):
        results = {}
        if len(tag_list) > 0:
            for tag in tag_list:
                if tag['namespace'] not in results.keys():
                    results[tag['namespace']] = {tag['key']: tag['value']}
                else:
                    results[tag['namespace']].update({tag['key']: tag['value']})
        return results

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('insights.yaml', 'insights.yml')):
                valid = True
            else:
                self.display.vvv('Skipping due to inventory source not ending in "insights.yaml" nor "insights.yml"')
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        self.server = self.get_option('server')
        url = "%s/api/inventory/v1/hosts?" % (self.server)
        strict = self.get_option('strict')
        get_patches = self.get_option('get_patches')
        get_system_advisories = self.get_option('get_system_advisories')
        get_system_packages = self.get_option('get_system_packages')
        staleness = self.get_option('staleness')
        selection = self.get_option('selection')
        vars_prefix = self.get_option('vars_prefix')
        get_tags = self.get_option('get_tags')
        filter_tags = self.get_option('filter_tags')
        registered_with = self.get_option('registered_with')
        systems_by_id = {}
        system_tags = {}
        results = []
        get_patching_info = get_patches or get_system_advisories or get_system_packages

        if len(filter_tags) > 0:
            url = "%s&tags=%s" % (url, '&tags='.join(filter_tags))
        if len(staleness) > 0:
            url = "%s&staleness=%s" % (url, '&staleness='.join(staleness))
        if registered_with:
            url = "%s&registered_with=%s" % (url, registered_with)

        self.headers = {"Accept": "application/json"}
        self.auth = requests.auth.HTTPBasicAuth(self.get_option('user'), self.get_option('password'))
        self.session = requests.Session()

        while url:
            response = self.session.get(url, auth=self.auth, headers=self.headers)

            if response.status_code != 200:
                raise AnsibleError("http error (%s): %s" %
                                   (response.status_code, response.text))
            elif response.status_code == 200:
                results += response.json()['results']
                total = response.json()['total']
                count = response.json()['count']
                per_page = response.json()['per_page']
                page = response.json()['page']
                if per_page * (page - 1) + count < total:
                    url = "%s&page=%s" % (url, (page + 1))
                    if len(filter_tags) > 0:
                        url = "%s&tags=%s" % (url, '&tags='.join(filter_tags))
                else:
                    url = None

        if get_patching_info:
            stale_patches = self.get_patches(stale=True,get_system_advisories=get_system_advisories,get_system_packages=get_system_packages,filter_tags=filter_tags)
            patches = self.get_patches(stale=False,get_system_advisories=get_system_advisories,get_system_packages=get_system_packages,filter_tags=filter_tags)
            patching_results = patches + stale_patches
            patching = {}

            for system in patching_results:
                display_name = system['attributes']['display_name']
                patching[display_name] = {}
                for attribute in system['attributes']:
                    if attribute != 'display_name':
                        patching[display_name][attribute] = system['attributes'][attribute]

        for host in results:
            host_name = self.inventory.add_host(host['display_name'])
            systems_by_id[host['id']] = host_name
            for item in host.keys():
                self.inventory.set_variable(host_name, vars_prefix + item, host[item])
                if item == selection:
                    self.inventory.set_variable(host_name, 'ansible_host', host[item])

            if get_patching_info:
                if host_name in patching.keys():
                    self.inventory.set_variable(host_name, vars_prefix + 'patching',
                                                patching[host['display_name']])
                else:
                    self.inventory.set_variable(host_name, vars_prefix + 'patching', {'enabled': False})

        if get_tags:
            system_tags = {}
            systems_by_id_list = list(systems_by_id.keys())
            chunk_size=20
            systems_by_id_list_split=[systems_by_id_list[i:i + chunk_size] for i in range(0, len(systems_by_id_list), chunk_size)]
            for items in systems_by_id_list_split:
                partial_system_tags = self.get_tags(items)
                system_tags = {**system_tags, **partial_system_tags}

        for uuid in systems_by_id:
            host_name = systems_by_id[uuid]

            if get_tags:
                self.inventory.set_variable(host_name, vars_prefix + 'tags', self.parse_tags(system_tags[uuid]))

            self._set_composite_vars(
                self.get_option('compose'),
                self.inventory.get_host(host_name).get_vars(),
                host_name, strict)

            self._add_host_to_composed_groups(self.get_option('groups'),
                                              dict(), host_name, strict)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'),
                                           dict(), host_name, strict)