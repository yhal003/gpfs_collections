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
from ansible_collections.nesi.gpfs.plugins.module_utils.acl import NFSv4_ACL # type: ignore pylint:disable=import-error

def argument_spec():
    return dict(
        acl       = dict(type='list', required=True),
        path   = dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)

    path = module.params["path"]
    acl  = module.params["acl"]
    existing_acl = NFSv4_ACL.mmgetacl(path)
    ansible_acl  = NFSv4_ACL.from_ansible(acl)

    diff1 = existing_acl.diff(ansible_acl)
    diff2 = ansible_acl.diff(existing_acl)

    if (len(diff1) == 0 and len(diff2) == 0):
        module.exit_json(changed = False, nfsv4_acl = str(existing_acl))
    else:
        NFSv4_ACL.mmputacl(path, ansible_acl)
        module.exit_json(changed=True, diff1 = str(diff1), diff2 = str(diff2))

if __name__ == '__main__':
    main()
