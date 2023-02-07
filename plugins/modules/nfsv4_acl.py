from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.acl import NFSv4_ACL # type: ignore pylint:disable=import-error

DOCUMENTATION=r'''
---
module: nfsv4_acl
author: Yuriy Halytskyy (@yhal003)
short_description: Assign NFSv4 ACLs to files or directories on Spectrum Scale
description:
- Assign NFSv4 ACLs to files or directories on Spectrum Scale
options:
 path:
   description:
   - path of a file or a directory on Spectrum Scale filesystem.
   required: true
   type: str
 acl:
   description:
   - NFSv4 ACL to be assigned to a file or directory.
   - |
    Each list item is a dictionary with (spec) corresponding
    to the first line of ACL entry and one of (yes_except),
    (yes_only), (no_except) and (no_only)
   - See Examples for more details
   -|
    Spectrum Scale NFSv4 ACL syntax is documented at
    https://www.ibm.com/docs/en/spectrum-scale/5.0.2?topic=administration-nfs-v4-acl-syntax
   required: true
   type: list
'''

EXAMPLES=r'''
 - name: Assign ACL
   nfsv4_acl:
    path: /fs/name
    acl:
     - spec: "special:owner@:rwxc:allow:FileInherit:DirInherit"
       yes_except: ["DELETE"]
     - spec: "special:group@:rwxc:allow:FileInherit:DirInherit"
       yes_except: ["DELETE"]
     - spec: "special:everyone@:----:allow:FileInherit:DirInherit"
       yes_only: ["SYNCHRONIZE",
                  "READ_ACL", "READ_ATTR", "READ_NAMED"]
     - spec: "group:agresearch_admins:rwxc:allow:DirInherit"
        yes_except: ["DELETE"]
'''

RETURN=r'''

'''

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
