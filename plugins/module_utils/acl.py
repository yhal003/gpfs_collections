import re
import subprocess

class NFSv4_PermList:

    @staticmethod
    def yes_all():
        permissions = { permission: True  
                        for permission in 
                        NFSv4_PermList.PERMISSIONS }
        return NFSv4_PermList(permissions)

    @staticmethod
    def yes_except(permissions):
        result = NFSv4_PermList.yes_all()
        for p in permissions:
            result[p] = False
        return result

    @staticmethod
    def no_all():
        permissions = { permission: False  
                        for permission in 
                        NFSv4_PermList.PERMISSIONS }
        return NFSv4_PermList(permissions)

    @staticmethod
    def yes_only(permissions):
        result = NFSv4_PermList.no_all()
        for p in permissions:
            result[p] = True
        return result

    @staticmethod
    def no_except(permissions):
        return NFSv4_PermList.yes_only(permissions)

    @staticmethod
    def no_only(permissions):
        return NFSv4_PermList.yes_except(permissions)       

    @staticmethod
    def read(text):
        perms = text.split()
        result = NFSv4_PermList({})
        for p in perms:
            m = re.match(r"\((.)\)(.*)", p)
            allow = m.group(1)
            perm_name = m.group(2)
            if allow == "X":
                result[perm_name] = True           
            if allow == "-":
                result[perm_name] = False
        return result     

    PERMISSIONS=["READ/LIST", "WRITE/CREATE",
                 "APPEND/MKDIR", "SYNCHRONIZE",
                 "READ_ACL", "READ_ATTR", "READ_NAMED",
                 "DELETE", "DELETE_CHILD", "CHOWN",
                 "EXEC/SEARCH", "WRITE_ACL", "WRITE_ATTR",
                 "WRITE_NAMED"]
    
    def __init__(self, permissions):
        self.permissions = permissions

    def __getitem__(self, permission):
        if permission in NFSv4_PermList.PERMISSIONS:
            return self.permissions[permission]
        else:
            raise IndexError(f"Unknown permission {permission}")
    
    def __setitem__(self, permission, allow):
        if not isinstance(allow, bool):
            raise TypeError(f"permission {allow} must be True or False")
        if permission not in NFSv4_PermList.PERMISSIONS:
            raise IndexError(f"Unknown permission {permission}")
        self.permissions[permission] = allow

    def __repr__(self):
        result = " "
        for p in NFSv4_PermList.PERMISSIONS:
            value = "X" if self[p] else "-"
            result += f"({value}){p}"
            if p == "READ_NAMED":
                result += "\n "
            elif p != "WRITE_NAMED":
                result += " "
        return result

    def __eq__(self, value):
        for p in NFSv4_PermList.PERMISSIONS:
            if self[p] != value[p]:
                return False
        return True  
    
#group:agresearch_admins:rwxc:allow:Inherited
class NFSv4_PermSpec:

    AUD_TYPES = set(["special", "group", "user"])
    SPEC_TYPES = set(["allow", "deny"])
    FLAGS = set(["Inherited", "InheritOnly", "NoPropagateInherit",
             "FileInherit", "DirInherit"])

    @staticmethod
    def read(string_repr):
        values = string_repr.split(":")
        return NFSv4_PermSpec(
            aud_type = values[0],
            aud = values[1],
            unix_bits = values[2],
            spec_type = values[3],
            flags = set(values[4:])
        )

    def __init__(self,
                 aud_type,
                 aud,
                 unix_bits,
                 spec_type,
                 flags = set([])):
        if not flags.issubset(NFSv4_PermSpec.FLAGS):
            raise ValueError(f"flags must be any of {NFSv4_PermSpec.FLAGS}")
        if spec_type not in NFSv4_PermSpec.SPEC_TYPES:
            raise ValueError("spec_type must be allow or deny")
        if aud_type not in NFSv4_PermSpec.AUD_TYPES:
            raise ValueError(f"aud_type must be on of {NFSv4_PermSpec.AUD_TYPES}")
        if not re.match("[r-][w-][x-][c-]", unix_bits):
            raise ValueError(f"unix bits {unix_bits} are not valid")

        self.aud_type = aud_type
        self.aud = aud
        self.unix_bits = unix_bits
        self.spec_type = spec_type
        self.flags = flags

    def is_inherited(self):
        return "Inherited" in self.flags
    
    def __eq__(self, value):
        return (self.aud_type == value.aud_type and
                self.aud == value.aud and
                self.unix_bits == value.unix_bits and
                self.spec_type == value.spec_type and
                self.flags == value.flags)
    
    def __repr__(self):
        result = f"{self.aud_type}:{self.aud}:{self.unix_bits}:{self.spec_type}"
        if self.flags == set([]):
            return result
        else:
            flag_repr = ":".join(self.flags)
            return f"{result}:{flag_repr}"

class NFSv4_ACL:

    HEADER = "#NFSv4 ACL\n"

    @staticmethod
    def read(string_repr: str):
        result = NFSv4_ACL()
        for entry in string_repr.split("\n\n"):
            if entry.strip() == "":
                continue
            else:
                lines = entry.split("\n")
                content_lines = [l for l in lines 
                                 if not (l.startswith("#") or l == "")]
                spec = NFSv4_PermSpec.read(content_lines[0])
                perms = NFSv4_PermList.read(" ".join(content_lines[1:]))
                result.append(spec, perms)
        return result

    @staticmethod 
    def from_ansible(ansible_list):
        result = NFSv4_ACL()
        for entry in ansible_list:
            if ("spec" not in entry):
                raise ValueError("all ACL entries must include spec")
            spec = NFSv4_PermSpec.read(entry["spec"])
            allowed_perms = set(["yes_except", "yes_only",
                                "no_except", "no_only"])
            if len(allowed_perms - set(entry.keys())) != 3:
                raise ValueError(f"one and only one of {allowed_perms} is required")
            if ("yes_except" in entry):
                perm = NFSv4_PermList.yes_except(entry["yes_except"])
            if ("yes_only" in entry):
                perm = NFSv4_PermList.yes_only(entry["yes_only"])
            if ("no_except" in entry):
                perm = NFSv4_PermList.no_except(entry["no_except"])
            if ("no_only" in entry):
                perm = NFSv4_PermList.no_only(entry["no_only"])
            result.append(spec, perm)
        return result

    @staticmethod
    def mmgetacl(filename):
        acl_proc = subprocess.run(["/usr/lpp/mmfs/bin/mmgetacl",
                                   "-k", "nfs4", filename],
                                   check = True,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        return NFSv4_ACL.read(acl_proc.stdout.decode())

    @staticmethod
    def mmputacl(filename, acl):
        acl_proc = subprocess.run(["/usr/lpp/mmfs/bin/mmputacl",
                                    filename],
                                   check = False,
                                   input = repr(acl).encode(),
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        if acl_proc.returncode != 0:
            raise Exception(f"error: {acl_proc.stderr.decode()} status: {acl_proc.returncode}")
                     
    def __init__(self):
        self.acl_list = []
    
    def append(self, spec: NFSv4_PermSpec, perms: NFSv4_PermList):
        self.acl_list += [(spec, perms)]
    
    def __getitem__(self, index):
        return self.acl_list[index]

    def __len__(self):
        return len(self.acl_list)

    def __repr__(self):
        result = NFSv4_ACL.HEADER + "\n"
        for (spec,perms) in self:
            result += repr(spec) + "\n"
            result += repr(perms) + "\n"
            result += "\n"
        return result

    def diff(self, acl, ignore_inherited = True):
        diff = NFSv4_ACL()
        for (spec1, permlist1) in self:
            if ignore_inherited and spec1.is_inherited():
                continue
            found = False
            for (spec2, permlist2) in acl:
                if (spec1 == spec2 and permlist1 == permlist2):
                    found = True
            if (not found):
                diff.append(spec1, permlist1)
        return diff
