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
from types import SimpleNamespace
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nesi.gpfs.plugins.module_utils.acl import NFSv4ACL,yes_except,yes_only, no_except, no_only

def argument_spec():
    return dict(
        acl       = dict(type='list', required=True),
        path   = dict(type='str', required=True)
    )

def ansible2acl(ansible_acl):
    acl_obj = NFSv4ACL("")
    for entry in ansible_acl:
        spec = SimpleNamespace()
        if "user" in entry:
            spec.audience_type = "user"
            spec.audience = entry["user"]
        elif "group" in entry:
            spec.audience_type = "group"
            spec.audience = entry["group"]
        elif "special" in entry:
            spec.audience_type = "special"
            spec.audience = entry["special"]
        spec.type = entry["type"]
        spec.flags = []
        if entry.get("file_inherit",False):
            spec.flags += ["FileInherit"]
        if entry.get("dir_inherit",False):
            spec.flags += ["DirInherit"]
        if entry.get("inherit_only",False):
            spec.flags += ["InheritOnly"]
        if entry.get("no_propagate_inherit",False):
            spec.flags += ["NoPropagateInherit"]

        if "yes_except" in entry:
            permissions = yes_except(entry["yes_except"])
        elif "yes_only" in entry:
            permissions = yes_only(entry["yes_only"])
        elif "no_except" in entry:
            permissions = no_except(entry["no_except"])
        elif "no_only" in entry:
            permissions = no_only(entry["no_only"])
        acl_obj.entries += [{"spec": spec, "permissions": permissions}]
    return acl_obj

def spec_eql(spec1, spec2):
    """Ignores unix permissions because 
        those are computed by Spectrum Scale
    """
    return (spec1.audience_type == spec2.audience_type and
           spec1.audience       == spec2.audience and
           spec1.type           == spec2.type and
           set(spec1.flags)     == set(spec2.type))

def acl_diff(acl1, acl2):
    diff = NFSv4ACL("")
    for entry1 in acl1.entries:
        found = False
        if "InheritOnly" in entry1.spec.flags:
            continue
        for entry2 in acl2.entries:
            if "InheritOnly" in entry2.spec.flags:
                continue
            if (spec_eql(entry1.spec, entry2.spec) and
                entry1.permissions == entry2.permissions):
                found = True
        if found:
            diff.entries += [entry1]
    return diff

def main():
    module = AnsibleModule(argument_spec=argument_spec(),
                          supports_check_mode=True)
    
    path = module.params["path"]
    acl  = module.params["acl"]
    existing_acl = NFSv4ACL.getacl(path)
    ansible_acl  = ansible2acl(acl)

    diff1 = acl_diff(existing_acl, ansible_acl)
    diff2 = acl_diff(ansible_acl, existing_acl)

    if (len(diff1.entries) == 0 and len(diff2.entries) == 0):
        module.exit_json(changed=False, nfsv4_acl = str(existing_acl))
    else:
        NFSv4ACL.putacl(ansible_acl, path)
        module.exit_json(changed=True, diff1 = str(diff1), diff2 = str(diff2))

if __name__ == '__main__':
    main()
