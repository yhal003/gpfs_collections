from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import FilesetQuota, Fileset #type: ignore

DOCUMENTATION=r'''
---
module: fileset_quota_info
author: Yuriy Halytskyy (@yhal003)
short_description: TODO
description:
- TODO
'''

EXAMPLES=r'''
'''

RETURN=r'''
'''

def argument_spec():
    return dict(
        fileset_name       = dict(type='str', required=True),
        filesystem         = dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)
    name = module.params["fileset_name"]
    filesystem = module.params["filesystem"]
    try:
        fset = Fileset(filesystem, name)
    except IndexError:
        module.fail_json(msg=f"fileset {name} not found in {filesystem}")
    quota = FilesetQuota.read(filesystem, name)
    module.exit_json(changed=False,
                     fileset_quota_info = quota.__dict__)

if __name__ == '__main__':
    main()
