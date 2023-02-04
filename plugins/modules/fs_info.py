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
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import FS # type: ignore pylint:disable=import-error

def argument_spec():
    return dict(
        name=dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)
    name = module.params["name"]
    try:
        module.exit_json(changed=False, fs_info = FS(name).__dict__)
    except IndexError:
        module.fail_json(msg=f"filesystem {name} not found",
                         exception = traceback.format_exc())
    except ValueError:
        module.fail_json(msg=f"{name} is not a valid filesystem name",
                         exception= traceback.format_exc())
    except Exception: # pylint: disable=broad-except
        module.fail_json(msg="fs_info failed",
                         exception = traceback.format_exc())

if __name__ == '__main__':
    main()

