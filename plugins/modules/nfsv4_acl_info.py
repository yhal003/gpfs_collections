from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.acl import NFSv4_ACL # type: ignore pylint:disable=import-error

DOCUMENTATION=r'''
---
module: nfsv4_acl_info
author: Yuriy Halytskyy (@yhal003)
short_description: read NFSv4 ACL from file or directory on Spectrum Scale
description:
- read NFSv4 ACL from file or directory on Spectrum Scale
'''

EXAMPLES=r'''
'''

RETURN=r'''
'''

def argument_spec():
    return dict(
        path   = dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)

    path = module.params["path"]
    acl = NFSv4_ACL.mmgetacl(path)
    module.exit_json(changed = False, nfsv4_acl = str(acl))

if __name__ == '__main__':
    main()
