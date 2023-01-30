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
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import Fileset

def argument_spec():
    return dict(
        name       = dict(type='str', required=True),
        filesystem = dict(type='str', required=True),
        comment = dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        allow_permission_change = dict(type = 'str',
                                       default = 'chmodAndSetAcl',
                                       choices = ['chmodAndSetAcl',
                                                  'setAclOnly',
                                                  'chmodOnly',
                                                  'chmodAndUpdateAcl']),
        allow_permission_inherit = dict(type='str',
                                        default = 'inheritAclOnly',
                                        choices = ['inheritAclOnly',
                                                   'inheritAclAndAddMode'])
    )

def delete_fileset(module):
    pass

def create_fileset(module):
    return Fileset.create(name = module.params["name"],
                          filesystem = module.params["filesystem"],
                          comment = module.params.get("comment",None),
                          allow_permission_change = 
                            module.params["allow_permission_change"],
                          allow_permission_inherit = 
                            module.params["allow_permission_inherit"])

def ensure(module, existing_fileset):
    return False

def main():
    module = AnsibleModule(argument_spec=argument_spec(), 
                          supports_check_mode=True)
    name = module.params["name"]
    filesystem = module.params["filesystem"]
    state = module.params["state"]

    try:
        existing_fileset = Fileset(filesystem, name)
        if (state == "present"):
            changed = ensure(module, existing_fileset)
            module.exit_json(changed=changed)
        else:
            delete_fileset(module)
            module.exit_json(changed=True)

    except IndexError:
        if (state == "absent"):
            module.exit_json(changed=False)
        else:
            fset = create_fileset(module)
            module.exit_json(changed=True, fileset = fset.__dict__)

if __name__ == '__main__':
    main()
