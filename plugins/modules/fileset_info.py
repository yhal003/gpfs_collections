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
