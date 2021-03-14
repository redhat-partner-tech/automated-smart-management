theforeman.foreman.lifecycle_environments
=========================================

This role creates and manages Content Views.

Role Variables
--------------

This role supports the [Common Role Variables](https://github.com/theforeman/foreman-ansible-modules/blob/develop/README.md#common-role-variables).

The main data structure for this role is the list of `foreman_content_views`. Each Content View requires the following fields:

- `name`
- `content_view`
- `content_view_update`
- `repos`
  - `product`: required
  - `name`

The following fields are optional and will be omitted by default:

- `filters`

Example Playbooks
-----------------

```yaml
- hosts: localhost
  roles:
    - role: theforeman.foreman.content_views
      vars:
        server_url: https://foreman.example.com
        username: "admin"
        password: "changeme"
        organization: "Default Organization"
        foreman_content_views:
          - name: RHEL7
            content_view: RHEL7
            content_view_update: true
            repos:
            - name: Red Hat Enterprise Linux 7 Server (RPMs)
              basearch: x86_64
              releasever: 7Server
            - name: Red Hat Enterprise Linux 7 Server - Extras (RPMs)
              basearch: x86_64
            - name: Red Hat Satellite Tools 6.8 (for RHEL 7 Server) (RPMs)
              basearch: x86_64
```

satellite_content:
  - name:             "Ansible server"
    content_view:     "Ansible servers content"
    content_view_update: yes
    repos:
      - name: 'Red Hat Enterprise Linux 7 Server (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'
        releasever:  '7Server'

      - name: 'Red Hat Satellite Maintenance 6 (for RHEL 7 Server) (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'

====================================
:role: satellite-manage-content-view
:author: GPTE Team
:tag1: configure_satellite
:tag2: configure_satellite_content_view
:main_file: tasks/main.yml
:version_file: tasks/version_6.7.yml

Role: {role}
============

This role creates, adds repos and publish satellite content-view.

Requirements
------------

Following are the requirements:

. Satellite must be install and setup.
. Repository should be enabled and syncronized in the organization to add in content-view.


Role Variables
--------------

* Following are the variable which needs to be defined

|===
|satellite_version: "Digit" |Required |satellite version
|org: "String" |Required |Organization name
|org_label: "String" |Required | Organization label in string without space
|org_description: "String" |Required | Organization description
| satellite_content: {Dictionary} |Required | Main dictionary variable
| content_view: "String" | Requird | Name of content-view
| content_view_update: bool | Optional(*no*) | Wheter to publish new version
| repos: [list] | Required | List of repository name
| filters: [list]| Optional | Add filter rules
|===

* Exammple variables

[source=text]
----
satellite_version: 6.7
org: "gpte"
org_label: "gpte"
org_description: "Global Partner Training and Enablement"
satellite_content:
  - name:             "Ansible server"
    content_view:     "Ansible servers content"
    content_view_update: yes
    repos:
      - name: 'Red Hat Enterprise Linux 7 Server (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'
        releasever:  '7Server'

      - name: 'Red Hat Satellite Maintenance 6 (for RHEL 7 Server) (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'

  - name:             "Three Tier App"
    content_view:     "Three Tier App"
    repos:
      - name: 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)'
        product: 'Red Hat Enterprise Linux for x86_64'
        releasever:  '8'
    filters:
      - name: 'Exclude Errata after 2019-09-01'
        start_date: '2019-09-01'
        type: 'erratum'
        inclusion: False
      - name: 'Include package foo'
        rule_name: 'foo'
        inclusion: True
----

Tags
---

|===
|{tag1} |Consistent tag for all satellite config roles
|{tag2} |This tag is specific to this role only
|===

* Example tags

----
## Tagged jobs
ansible-playbook playbook.yml --tags configure_satellite,configure_satellite_content_view

## Skip tagged jobs
ansible-playbook playbook.yml --skip-tags configure_satellite,configure_satellite_content_view
----

Example Playbook
----------------

How to use your role (for instance, with variables passed in playbook).

[source=text]
----
[user@desktop ~]$ cat sample_vars.yml
satellite_version: 6.7
org: "gpte"
org_label: "gpte"
org_description: "Global Partner Training and Enablement"
satellite_content:
  - name:             "Ansible server"
    content_view:     "Ansible servers content"
    content_view_update: yes
    repos:
      - name: 'Red Hat Enterprise Linux 7 Server (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'
        releasever:  '7Server'

      - name: 'Red Hat Satellite Maintenance 6 (for RHEL 7 Server) (RPMs)'
        product: 'Red Hat Enterprise Linux Server'
        basearch: 'x86_64'

  - name:             "Three Tier App"
    content_view:     "Three Tier App"
    repos:
      - name: 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)'
        product: 'Red Hat Enterprise Linux for x86_64'
        releasever:  '8'
    filters:
      - name: 'Include Errata before 2019-09-01'
        end_date: '2019-09-01'
        type: 'erratum'
        inclusion: True
[user@desktop ~]$ cat playbook.yml
- hosts: satellite.example.com
  vars_files:
    - sample_vars.yml
  roles:
    - satellite-manage-content-view

[user@desktop ~]$ ansible-playbook playbook.yml
----

Tips to update Role
------------------

To extend role works for other version, if needed create new file named  version_{{satellite_version}}.yml and import newly created file in main.yml

for reference look at link:{main_file}[main.yml] and link:{version_file}[version_6.x.yml]


Author Information
------------------

{author}
