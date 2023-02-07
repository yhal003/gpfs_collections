DOCUMENTATION=r'''
---
module: fileset_info
author: Yuriy Halytskyy (@yhal003)
short_description: Provides information about Spectrum Scale fileset
description:
- The same output as mmlsfileset -Y provided as a dictionary
options:
 name:
   description:
   - name of the fileset.
   required: true
   type: str
 filesystem:
   description:
   - Spectrum Scale filesystem name.
   required: true
   type: str
'''

EXAMPLES=r'''
- name: Info for projects fileset
  nesi.gpfs.fileset_info:
   filesystem: filesystem1
   name: projects
  register: fs_result
'''

RETURN=r'''
fileset_info:
 description: output of mmlsfileset -Y
 returned: always
 type: dict
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import Fileset #type: ignore

def argument_spec():
    return dict(
        name       = dict(type='str', required=True),
        filesystem = dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)
    name = module.params["name"]
    filesystem = module.params["filesystem"]
    try:
        module.exit_json(changed=False,
                         fileset_info = Fileset(filesystem,name).__dict__)
    except IndexError:
        module.fail_json(msg=f"fileset {name} not found in {filesystem}",
                         exception = traceback.format_exc())
    except Exception: # pylint: disable=broad-except
        module.fail_json(msg="fileset_info failed",
                         exception = traceback.format_exc())

if __name__ == '__main__':
    main()
