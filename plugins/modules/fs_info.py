DOCUMENTATION=r'''
TODO: Document this module
'''

EXAMPLES=r'''
TODO: Provide Examples
'''

RETURN=r'''
TODO: Provide return
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.fs import text2table

def argument_spec():
    return dict(
        name=dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(), 
                          supports_check_mode=True)
    module.exit_json(changed=True, fs_info = {})


if __name__ == '__main__':
    main()

