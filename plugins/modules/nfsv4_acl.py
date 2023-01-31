DOCUMENTATION=r'''
TODO: Document this module
'''

EXAMPLES=r'''
TODO: Provide Examples
'''

RETURN=r'''
TODO: Provide return
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.acl import NFSv4ACL

def argument_spec():
    return dict(
        acls       = dict(type='dict', required=True),
        filename   = dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(), 
                          supports_check_mode=True)
    module.exit_json(changed=False)

if __name__ == '__main__':
    main()
