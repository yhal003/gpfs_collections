import pytest
from acl import NFSv4_YES, NFSv4_NO
from acl import read_nfsv4_entry, yes_except, yes_only, no_except, no_only
from acl import read_nfsv4_spec
from acl import NFSv4ACL

ENTRY1 = """ (X)READ/LIST (X)WRITE/CREATE (X)APPEND/MKDIR (X)SYNCHRONIZE (X)READ_ACL  (X)READ_ATTR  (X)READ_NAMED
 (-)DELETE    (X)DELETE_CHILD (X)CHOWN        (X)EXEC/SEARCH (X)WRITE_ACL (X)WRITE_ATTR (X)WRITE_NAMED
"""
def test_read_entry():
    acl = read_nfsv4_entry(ENTRY1)
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

def test_yes_except_nothing():
    acl = yes_except([])
    assert acl == NFSv4_YES

def test_yes_except_read():
    acl = yes_except(["READ/LIST"])
    expected_acl = NFSv4_YES.copy()
    expected_acl["READ/LIST"] = False
    assert acl == expected_acl 

def test_yes_except_two():
    acl = yes_except(["READ/LIST", "CHOWN"])
    expected_acl = NFSv4_YES.copy()
    expected_acl["READ/LIST"] = False
    expected_acl["CHOWN"] = False
    assert acl == expected_acl 

# test spec
def test_simple_spec():
    spec_string = "group:staff:r-x-:allow"
    spec = read_nfsv4_spec(spec_string)

    assert spec.type == "allow"
    assert spec.audience_type == "group"
    assert spec.audience == "staff"
    assert spec.unix == "r-x-"
    assert spec.flags == set()

def test_spec_with_flags():
    spec_string = "user:john:r-x-:allow:DirInherit:InheritOnly"
    spec = read_nfsv4_spec(spec_string)
    assert spec.flags == set(["InheritOnly", "DirInherit"])
     
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
    acl = NFSv4ACL(ACL1)
    assert len(acl.entries) == 1
    entry1 = acl.entries[0]
    assert entry1.spec.type == "allow"
    assert entry1.permissions["READ/LIST"]
    assert not entry1.permissions["EXEC/SEARCH"]

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
    acl = NFSv4ACL(ACL2)
    assert len(acl.entries) == 2

def test_empty_acl():
    acl = NFSv4ACL("")
    assert len(acl.entries) == 0