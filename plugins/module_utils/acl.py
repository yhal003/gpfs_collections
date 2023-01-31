import re
from types import SimpleNamespace
import subprocess

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

NFSv4_PERMISSIONS=["READ/LIST", "WRITE/CREATE",
                   "APPEND/MKDIR", "SYNCHRONIZE",
                   "READ_ACL", "READ_ATTR", "READ_NAMED",
                   "DELETE", "DELETE_CHILD", "CHOWN",
                   "EXEC/SEARCH", "WRITE_ACL", "WRITE_ATTR",
                   "WRITE_NAMED"]

NFSv4_YES = { permission: True  for permission in NFSv4_PERMISSIONS }
NFSv4_NO  = { permission: False for permission in NFSv4_PERMISSIONS }

NFSv4_HEADER = "#NFSv4 ACL\n"

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

class NFSv4ACL:

    @staticmethod
    def getacl(filename):
        acl_proc = subprocess.run(["/usr/lpp/mmfs/bin/mmgetacl",
                                   "-k", "nfs4", filename],
                                   check = True,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        return NFSv4ACL(acl_proc.stdout.decode()) 

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
