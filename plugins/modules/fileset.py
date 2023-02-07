from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import Fileset  # type: ignore

DOCUMENTATION=r'''
---
module: fileset
author: Yuriy Halytskyy (@yhal003)
short_description: Create or modify Spectrum Scale filesets
description:
- Create or modify Spectrum Scale filesets.
'''

EXAMPLES=r'''
'''

RETURN=r'''
'''

def argument_spec():
    return dict(name       =dict(type='str', required=True),
                filesystem =dict(type='str', required=True),
                path       =dict(type='str', required=False),
                comment    =dict(type='str', required=False),
                unlink     =dict(type='bool', default=False),
                state      =dict(type='str', default='present',
                                 choices=['present', 'absent']),
                allow_permission_change =dict(type    ='str',
                                              default ='chmodAndSetAcl',
                                              choices =['chmodAndSetAcl',
                                                          'setAclOnly',
                                                          'chmodOnly',
                                                          'chmodAndUpdateAcl']),
                allow_permission_inherit = dict(type='str',
                                                default = 'inheritAclOnly',
                                                choices = ['inheritAclOnly',
                                                           'inheritAclAndAddMode'])
                )

def delete_fileset(module):
    Fileset.delete(module.params["filesystem"], module.params["name"])

def create_fileset(module):
    return Fileset.create(name = module.params["name"],
                          filesystem = module.params["filesystem"],
                          comment = module.params.get("comment",None),
                          allow_permission_change =
                            module.params["allow_permission_change"],
                          allow_permission_inherit =
                            module.params["allow_permission_inherit"])

def ensure(module, existing_fileset):
    """
     ensure the fileset matches the module.
     returns None if no changes are made, otherwise returns new fileset
    """
    perm_change_flag = module.params["allow_permission_change"]
    perm_inherit_flag = module.params["allow_permission_inherit"]
    comment = module.params["comment"]
    filesystem = module.params["filesystem"]
    name = module.params["name"]
    path  = module.params.get("path", None)
    unlink = module.params["unlink"]

    new_fileset = None
    if (perm_change_flag != existing_fileset.permChangeFlag or
        perm_inherit_flag != existing_fileset.permInheritFlag or
        comment != existing_fileset.comment):
        new_fileset = Fileset.update(filesystem,
                                     name,
                                     allow_permission_change = perm_change_flag,
                                     allow_permission_inherit = perm_inherit_flag,
                                     comment = comment)

    if (path is not None and existing_fileset.status == "Unlinked"):
        new_fileset = Fileset.link(filesystem, name, path)

    if (path is not None and
        existing_fileset.status == "Linked" and
        path != existing_fileset.path ):
        Fileset.unlink(filesystem, name)
        new_fileset = Fileset.link(filesystem, name, path)

    if (unlink and existing_fileset.status == "Linked"):
        new_fileset = Fileset.unlink(filesystem, name)

    return new_fileset

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                           supports_check_mode=True)
    name = module.params["name"]
    filesystem = module.params["filesystem"]
    state = module.params["state"]
    path = module.params.get("path",None)
    unlink = module.params["unlink"]

    if (unlink and path is not None):
        module.fail_json(msg="path cannot be set when unlink is true")

    try:
        existing_fileset = Fileset(filesystem, name)
        if state == "present":
            new_fileset = ensure(module, existing_fileset)
            module.exit_json(changed=new_fileset is not None,
                             fileset = new_fileset.__dict__
                                       if new_fileset is not None
                                       else existing_fileset.__dict__)
        else:
            if (unlink and existing_fileset.status == "Linked"):
                Fileset.unlink(filesystem, name)
            delete_fileset(module)
            module.exit_json(changed=True)

    except IndexError:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            fset = create_fileset(module)
            if path is not None:
                Fileset.link(filesystem, name, path)
            module.exit_json(changed=True, fileset = fset.__dict__)

if __name__ == '__main__':
    main()
