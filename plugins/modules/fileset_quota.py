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
from ansible_collections.nesi.gpfs.plugins.module_utils.gpfs import FilesetQuota, Fileset #type: ignore

def argument_spec():
    return dict(
        fileset_name       = dict(type='str', required=True),
        filesystem         = dict(type='str', required=True),
        file_soft          = dict(type='int', required=False),
        file_hard          = dict(type='int', required=False),
        block_soft         = dict(type='str', required=False),
        block_hard         = dict(type='str', required=False)
    )

def to_kb(size):
    suffixes = {
        "K": 1,
        "M": 1024,
        "G": 1024*1024,
        "T": 1024*1024*1024,
        "P": 1024*1024*1024*1024
    }
    value = int(size[:-1])
    suffix = size[-1]
    return value * suffixes[suffix]

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                           required_one_of=[('file_soft',
                                             'file_hard', 'block_soft','block_hard')],
                          supports_check_mode=True)
    name = module.params["fileset_name"]
    filesystem = module.params["filesystem"]
    try:
        fset = Fileset(filesystem, name)
    except IndexError:
        module.fail_json(msg=f"fileset {name} not found in {filesystem}")
    quota = FilesetQuota.read(filesystem, name)
    changed = False
    if "file_soft" in module.params:
        file_soft = module.params["file_soft"]
        if quota.file_soft != file_soft:
            changed = True
            quota.file_soft = file_soft
    if "file_hard" in module.params:
        file_hard = module.params["file_hard"]
        if quota.file_hard != file_hard:
            changed = True
            quota.file_hard = file_hard
    if "block_soft" in module.params:
        block_soft = to_kb(module.params["block_soft"])
        if quota.block_soft != block_soft:
            changed = True
            quota.block_soft = block_soft
    if "block_hard" in module.params:
        block_hard = to_kb(module.params["block_hard"])
        if quota.block_hard != block_hard:
            changed = True
            quota.block_hard = block_hard
    if changed:
        quota.apply()
        module.exit_json(changed = True, quota = quota.__dict__)
    else:
        module.exit_json(changed = False, quota = quota.__dict__ )

if __name__ == '__main__':
    main()
