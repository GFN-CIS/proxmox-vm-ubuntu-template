#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '0.2',
    'status': ['preview'],
    'supported_by': 'godspeed-you'
}

DOCUMENTATION = """
---
module: pvesh

short_description: Managing Proxmox Nodes and Cluster through the command line tool pvesh

description: With the C(pvesh) module it is possible to use the Proxmox API directly on a Proxmox node instad of going through a HTTPS connection providing user and password in a ansible role. 

author: "Marcel Arentz (@gdspd_you@open-one.de)"

options:
    command:
        description: The command to be used. The useable commands for a specific task can seen in the official documentation of the Proxmox API: https://pve.proxmox.com/pve-docs/api-viewer/
        required: true
        choices:
            - ls
            - get
            - create
            - set
            - delete
    path:
        description: The path in the API to work on. Also explained in the official documentation
        required: true
    options:
        description: All other values, that can be specified or are needed for an API call. These values are provided as a dictionary. 
        required: false
"""

EXAMPLES = """
---
- name: Add a user to proxmox cluster
  pvesh:
    command: create
    path: access/users
    options:
      userid: myUser@pam
      email: myuser@mydomain.net

- name: Get all nodes of proxmox cluster
  pvesh:
    command: get
    path: /nodes

- name: Renew acme certificate
  pvesh:
    command: set
    path: 'nodes/{{ ansible_hostname }}/certificates/acme/certificate'
    options:
      node: '{{ ansible_fqdn }}'
"""

RETURN = """
---
status:
    description: The status code as returned from the API or defined in the module. HTTP status codes are used.
    type: int
result:
    description: The return value provided by pvesh.
    type: dict
command:
    description: The exact command created and used by the module. 
    type: str
"""

import subprocess
import logging
import json
from ansible.module_utils.basic import AnsibleModule


def execute_pvesh(handler, api_path, **params):
    """building the command, executing it and providing some basic
       classification. """
    command = [
        "/usr/bin/pvesh",
        handler.lower(),
        api_path,
        "--output=json"]
    for parameter, value in params.items():
        command += ["-%s" % parameter, "%s" % value]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stderr: str
    (result, stderr) = pipe.communicate()
    if pipe.returncode != 0:
        try:  # Sometimes pvesh is very kind and provides already a status code
            return dict(status=int(stderr[:4]),
                        stderr_message=stderr[:4],
                        result=result,
                        command=command)
        except ValueError:
            status = 400
        logging.error(stderr)
        stderr = str(stderr)
        if "handler defined for" in stderr:
            status = 405
        elif "already exists" in stderr:
            status = 304
        elif "does not exist" in stderr or \
                "no such" in stderr or \
                "not found" in stderr:
            status = 404

        return dict(status=status,
                    stderr_message=stderr,
                    result=result,
                    command=command)

    if handler in ['set', 'create', 'delete']:
        if not result:
            status = 204
        else:
            status = 201
    else:
        status = 200

    try:
        result = json.loads(result)
    except ValueError:
        pass

    return dict(status=status,
                stderr_message='',
                result=result,
                command=command)


def map_status(status, command):
    """ Each status code leads to a specific ansible status. We map that here!"""
    status_map = {'get': {200: 'ok'},
                  'ls': {200: 'ok'},
                  'set': {201: 'changed', 204: 'changed'},
                  'create': {201: 'changed', 204: 'changed', 304: 'ok'},
                  'delete': {201: 'changed', 204: 'changed', 404: 'ok'}}
    return status_map[command].get(status, 'failed')


def main():
    """ Main function to provide pvesh functionality as an Ansible module."""
    args = dict(
        handler=dict(type='str',
                     choices=['create', 'delete', 'get', 'ls', 'set', ],
                     required=True,
                     aliases=['command']),
        path=dict(type='str',
                  required=True),
        options=dict(type='dict',
                     default={},
                     required=False),
    )

    ansible = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True)

    handler = ansible.params['handler']
    path = ansible.params['path']
    options = ansible.params['options']

    result = execute_pvesh(handler, path, **options)
    status = result['status']
    command = result['command']
    result_final = result['result']

    check_status = map_status(status, handler)
    if check_status == 'ok':
        changed = False
    elif check_status == 'changed':
        changed = True
    elif check_status == 'failed':
        ansible.fail_json(msg=result.get('stderr_message'),
                          status=status,
                          result=result_final,
                          command=' '.join(command))

    ansible_result = dict(
        status=status,
        changed=changed,
        result=result_final,
        command=' '.join(command))

    ansible.exit_json(**ansible_result)


if __name__ == '__main__':
    main()
