import re
from types import SimpleNamespace
import subprocess

NFSv4_PERMISSIONS=["READ/LIST", "WRITE/CREATE",
                   "APPEND/MKDIR", "SYNCHRONIZE",
                   "READ_ACL", "READ_ATTR", "READ_NAMED",
                   "DELETE", "DELETE_CHILD", "CHOWN",
                   "EXEC/SEARCH", "WRITE_ACL", "WRITE_ATTR",
                   "WRITE_NAMED"]

NFSv4_YES = { permission: True  for permission in NFSv4_PERMISSIONS }
NFSv4_NO  = { permission: False for permission in NFSv4_PERMISSIONS }

NFSv4_HEADER = "#NFSv4 ACL\n"

def read_nfsv4_entry(entry):
    result = {}
    perms = entry.split()
    for p in perms:
        m = re.match(r"\((.)\)(.*)", p)
        allow = m.group(1)
        perm_name = m.group(2)
        if allow == "X":
            result[perm_name] = True           
        if allow == "-":
            result[perm_name] = False
    return result

def write_nfsv4_entry(entry_obj):
    result = ""
    for p in NFSv4_PERMISSIONS:
        value = "X" if entry_obj[p] else "-"
        result += f"({value}){p}"
        if p == "READ_NAMED":
            result += "\n"
        elif p != "WRITE_NAMED":
            result += " "
    return result

def yes_except(permissions):
    result = NFSv4_YES.copy()
    for p in permissions:
        result[p] = False
    return result

def yes_only(permissions):
    result = NFSv4_NO.copy()
    for p in permissions:
        result[p] = True
    return result

def no_except(permissions):
    return yes_only(permissions)

def no_only(permissions):
    return yes_except(permissions)

def read_nfsv4_spec(spec):
    values = spec.split(":")
    result = SimpleNamespace()
    result.audience_type = values[0]
    result.audience = values[1]
    result.unix = values[2]
    result.type = values[3]
    result.flags = set(values[4:])
    return result

def write_nfsv4_spec(spec_obj):
    if hasattr(spec_obj, "unix"):
        unix = spec_obj.unix
    else:
        unix = "----"
    result = ""
    result += f"{spec_obj.audience_type}:"
    result += f"{spec_obj.audience}:"
    result += f"{unix}:"
    result += f"{spec_obj.type}:"
    result += ":".join(spec_obj.flags)
    return result

class NFSv4ACL:

    @staticmethod
    def getacl(filename):
        acl_proc = subprocess.run(["/usr/lpp/mmfs/bin/mmgetacl",
                                   "-k", "nfs4", filename],
                                   check = True,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        return NFSv4ACL(acl_proc.stdout.decode())

    @staticmethod
    def putacl(acl, filename):
        acl_proc = subprocess.run(["/usr/lpp/mmfs/bin/mmputacl",
                                   "-k", "nfs4", filename],
                                   check = False,
                                   input = str(acl).encode(),
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        if acl_proc.returncode != 0:
            raise Exception(f"error: {acl_proc.stderr.decode()} status: {acl_proc.returncode}")

    def __init__(self, acl_string):
        self.entries = []
        for entry in acl_string.split("\n\n"):
            if entry.strip() == "":
                continue
            else:
                lines = entry.split("\n")
                content_lines = [l for l in lines 
                                 if not (l.startswith("#") or l == "")]
                entry = SimpleNamespace()
                entry.spec = read_nfsv4_spec(content_lines[0])
                entry.permissions = read_nfsv4_entry(" ".join(content_lines[1:]))
            self.entries += [entry]
    
    def __repr__(self):
        repr = NFSv4_HEADER + "\n"
        for entry in self.entries:
            repr += write_nfsv4_spec(entry.spec) + "\n"
            repr += write_nfsv4_entry(entry.permissions) + "\n"
            repr += "\n"
        return repr
