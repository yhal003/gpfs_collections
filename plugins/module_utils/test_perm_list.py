import pytest
from acl import NFSv4_PermList, NFSv4_PermSpec, NFSv4_ACL

def test_all_yes():
    perm_list = NFSv4_PermList.yes_all()
    assert perm_list["READ/LIST"] == True
    assert perm_list["CHOWN"] == True

def test_invalid_permission():
    perm_list = NFSv4_PermList.yes_all()
    with pytest.raises(IndexError):
        perm_list["UNKNOWN"]

ENTRY1 = """ (X)READ/LIST (X)WRITE/CREATE (X)APPEND/MKDIR (X)SYNCHRONIZE (X)READ_ACL  (X)READ_ATTR  (X)READ_NAMED
 (-)DELETE    (X)DELETE_CHILD (X)CHOWN        (X)EXEC/SEARCH (X)WRITE_ACL (X)WRITE_ATTR (X)WRITE_NAMED
"""
def test_read_entry():
    acl = NFSv4_PermList.read(ENTRY1)
    assert acl["READ/LIST"]
    assert acl["WRITE/CREATE"]
    assert acl["APPEND/MKDIR"]
    assert acl["SYNCHRONIZE"]
    assert acl["READ_ACL"]
    assert acl["READ_ATTR"]
    assert acl["READ_NAMED"]
    assert not acl["DELETE"]
    assert acl["DELETE_CHILD"]
    assert acl["CHOWN"]
    assert acl["EXEC/SEARCH"]
    assert acl["WRITE_ACL"]
    assert acl["WRITE_ATTR"]
    assert acl["WRITE_NAMED"]

def test_write_entry():
    acl = NFSv4_PermList.yes_all()
    acl["DELETE"] = False
    s = str(acl)
    normalized_s = " ".join(s.split())
    normalized_entry = " ".join(ENTRY1.split())
    assert normalized_s == normalized_entry

def test_equal():
    acl1 = NFSv4_PermList.yes_all()
    acl2 = NFSv4_PermList.yes_all()
    assert acl1 == acl2

def test_not_equal():
    acl1 = NFSv4_PermList.yes_all()
    acl2 = NFSv4_PermList.yes_all()
    acl2["EXEC/SEARCH"] = False
    assert acl1 != acl2

def test_yes_except_nothing():
    acl = NFSv4_PermList.yes_except([])
    expected = NFSv4_PermList.yes_all()
    assert acl == expected

def test_yes_except_read():
    acl = NFSv4_PermList.yes_except(["READ/LIST"])
    expected = NFSv4_PermList.yes_all()
    expected["READ/LIST"] = False
    assert acl == expected

def test_yes_except_two():
    acl = NFSv4_PermList.yes_except(["READ/LIST", "CHOWN"])
    expected = NFSv4_PermList.yes_all()
    expected["READ/LIST"] = False
    expected["CHOWN"] = False
    assert acl == expected

# testing permission specs

def test_read_perm_spec():
    spec = NFSv4_PermSpec.read("special:group@:rw--:allow")
    assert spec.aud_type  == "special"
    assert spec.aud       == "group@"
    assert spec.unix_bits == "rw--"
    assert spec.spec_type == "allow"
    assert spec.flags == set([])

def test_read_perm_spec_with_flags():
    spec = NFSv4_PermSpec.read("user:john:rwxc:deny:Inherited:InheritOnly")
    assert spec.flags == set(["Inherited", "InheritOnly"])

def test_write_perm_spec():
    spec = NFSv4_PermSpec("group", "admins", "rwxc", "allow", set([]))
    assert str(spec) == "group:admins:rwxc:allow"

def test_write_perm_spec_with_flag():
    spec = NFSv4_PermSpec("group", "admins", "rwxc", "allow", set(["InheritOnly"]))
    assert str(spec) == "group:admins:rwxc:allow:InheritOnly"

# test full ACLs

def test_empty_acl_len():
    acl = NFSv4_ACL()
    assert len(acl) == 0

def test_empty_acl_diff():
    acl1 = NFSv4_ACL()
    acl2 = NFSv4_ACL()
    diff = acl1.diff(acl2)
    assert len(diff) == 0

def test_empty_diff():
    acl1 = NFSv4_ACL()
    spec = NFSv4_PermSpec("group", "admins", "rwxc", "allow", set([]))
    plist = NFSv4_PermList.yes_all()
    acl1.append(spec, plist)

    acl2 = NFSv4_ACL()
    diff1 = acl1.diff(acl2)
    diff2 = acl2.diff(acl1)

    assert len(diff1) == 1
    assert len(diff2) == 0

def test_diff_order_doesnt_matter():
    spec1 = NFSv4_PermSpec("group", "admins", "rwxc", "allow", set([]))
    plist1 = NFSv4_PermList.yes_all()

    spec2 = NFSv4_PermSpec("user", "john", "rwxc", "allow", set([]))
    plist2 = NFSv4_PermList.no_all()

    acl1 = NFSv4_ACL()
    acl1.append(spec1, plist1)
    acl1.append(spec2, plist2)

    acl2 = NFSv4_ACL()
    acl2.append(spec2, plist2)
    acl2.append(spec1, plist1)

    diff1 = acl1.diff(acl2)
    diff2 = acl2.diff(acl1)

    assert len(diff1) == 0
    assert len(diff2) == 0

def test_diff_ignore_inherit():
    spec1 = NFSv4_PermSpec("group", "admins", "rwxc", "allow", set(["Inherited"]))
    plist1 = NFSv4_PermList.yes_all()

    spec2 = NFSv4_PermSpec("user", "john", "----", "allow", set([]))
    plist2 = NFSv4_PermList.no_all()

    spec3 = NFSv4_PermSpec("user", "mike", "----", "allow", set([]))
    plist3 = NFSv4_PermList.no_all()
    
    acl1 = NFSv4_ACL()
    acl1.append(spec1, plist1)
    acl1.append(spec2, plist2)
    acl1.append(spec3, plist3)

    acl2 = NFSv4_ACL()
    acl2.append(spec3, plist3)

    diff1 = acl1.diff(acl2)
    assert len(diff1) == 1

# test converting Ansible Module lists into ACLS

def test_ansible_empty():
    acl = NFSv4_ACL.from_ansible([])
    assert len(acl) == 0

def test_ansible_no_spec():
    with pytest.raises(ValueError):
        ansible_list = [
         {
            "yes_only": ["WRITE"]
         }   
        ]
        NFSv4_ACL.from_ansible(ansible_list)

def test_ansible_multiple_perms():
    with pytest.raises(ValueError):
        ansible_list = [
            {
                "yes_only": [],
                "no_except": [],
                "spec": "group:admins:rwxc:allow"
            }
        ]
        NFSv4_ACL.from_ansible(ansible_list)

def test_ansible_simple():
    ansible_list = [
        {
            "spec": "special:everyone@:rwxc:allow",
            "yes_except": []
        }
    ]
    acl = NFSv4_ACL.from_ansible(ansible_list)
    assert len(acl) == 1
    (spec, perms) = acl[0]
    assert perms == NFSv4_PermList.yes_all()
    assert spec.spec_type == "allow"

def test_ansible_two_entries():
    input = [
        {
            "spec": "special:everyone@:rwxc:allow",
            "yes_except": ["CHOWN"]       
        },
        {
            "spec": "special:group@:rwxc:allow",
            "yes_except": []
        }
    ]
    acl = NFSv4_ACL.from_ansible(input)
    assert len(acl) == 2

# test entire ACL

ACL1="""
#NFSv4 ACL
#owner:root
#group:root
special:owner@:rw-c:allow:FileInherit:DirInherit
 (X)READ/LIST (X)WRITE/CREATE (X)APPEND/MKDIR (X)SYNCHRONIZE (X)READ_ACL  (X)READ_ATTR  (X)READ_NAMED
 (-)DELETE    (X)DELETE_CHILD (X)CHOWN        (-)EXEC/SEARCH (X)WRITE_ACL (X)WRITE_ATTR (X)WRITE_NAMED
"""
def test_nfs_acl1():
    acl = NFSv4_ACL.read(ACL1)
    assert len(acl) == 1
    (spec, perms) = acl[0]
    assert spec.spec_type == "allow"
    assert perms["READ/LIST"]
    assert not perms["EXEC/SEARCH"]

ACL2="""
#NFSv4 ACL
#owner:root
#group:root
special:group@:r---:allow:FileInherit:DirInherit
 (X)READ/LIST (-)WRITE/CREATE (-)APPEND/MKDIR (X)SYNCHRONIZE (X)READ_ACL  (X)READ_ATTR  (X)READ_NAMED
 (-)DELETE    (-)DELETE_CHILD (-)CHOWN        (-)EXEC/SEARCH (-)WRITE_ACL (-)WRITE_ATTR (-)WRITE_NAMED

special:everyone@:r---:allow:FileInherit:DirInherit
 (X)READ/LIST (-)WRITE/CREATE (-)APPEND/MKDIR (X)SYNCHRONIZE (X)READ_ACL  (X)READ_ATTR  (X)READ_NAMED
 (-)DELETE    (-)DELETE_CHILD (-)CHOWN        (-)EXEC/SEARCH (-)WRITE_ACL (-)WRITE_ATTR (-)WRITE_NAMED

"""
def test_nfs_acl2():
    acl = NFSv4_ACL.read(ACL2)
    assert len(acl) == 2
    (spec2, perms2) = acl[1]
    assert spec2.flags == set(["FileInherit", "DirInherit"])
    assert perms2["READ/LIST"]
    assert not perms2["WRITE_ATTR"]