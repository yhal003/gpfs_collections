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
from ansible_collections.nesi.gpfs.plugins.module_utils.fs import FS

def argument_spec():
    return dict(
        name=dict(type='str', required=True)
    )

def main():
    module = AnsibleModule(argument_spec=argument_spec(), 
                          supports_check_mode=True)
    name = module.params["name"]
    try:
        module.exit_json(changed=False, fs_info = FS(name)._dict_)
    except IndexError as e:
        module.fail_json(msg=f"filesystem {name} not found",
                         exception = e)
    except ValueError as e:
        module.fail_json(msg=f"{name} is not a valid filesystem name",
                         exception= e)
    except Exception as e: # pylint: disable=broad-except
        module.fail_json(msg="fs_info failed", exception = e)

if __name__ == '__main__':
    main()

