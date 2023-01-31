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
        path       = dict(type='str', required=False),
        comment    = dict(type='str', required=False),
        unlink     = dict(type='bool', default=False),
        state      = dict(type='str', default='present',
                          choices=['present', 'absent']),
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
    permChangeFlag = module.params["allow_permission_change"] 
    permInheritFlag = module.params["allow_permission_inherit"]
    comment = module.params["comment"]
    filesystem = module.params["filesystem"]
    name = module.params["name"]
    path  = module.params.get("path", None)
    unlink = module.params["unlink"]

    changed = False
    if (permChangeFlag != existing_fileset.permChangeFlag or
        permInheritFlag != existing_fileset.permInheritFlag or
        comment != existing_fileset.comment):
        Fileset.update(filesystem,
                       name,
                       allow_permission_change = permChangeFlag,
                       allow_permission_inherit = permInheritFlag,
                       comment = comment)
        changed = True

    if (path is not None and existing_fileset.status == "Unlinked"):
        Fileset.link(filesystem, name, path)
        changed = True

    if (path is not None and existing_fileset.status == "Linked"):
        Fileset.unlink(filesystem, name)
        Fileset.link(filesystem, name, path)
        changed = True

    if (unlink and existing_fileset.status == "Linked"):
        Fileset.unlink(filesystem, name)

    return changed

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
            changed = ensure(module, existing_fileset)
            module.exit_json(changed=changed)
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
