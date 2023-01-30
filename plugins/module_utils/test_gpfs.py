import pytest
from unittest.mock import ANY
import subprocess
from gpfs import text2table

# text2table tests 

def test_empty():
    i = ""
    o = text2table(i)
    assert o == {}

def test_empty_header():
    i = "command:header:HEADER:\n"
    o = text2table(i)
    assert o == {"header": []}

def test_simple_value():
    i = ("command:header:HEADER:key\n"
         "command:header::value")
    o = text2table(i)
    assert o == {"header": [{"key":"value"}]}

# gpfs puts one extra : at the end, we need to ignore that
def test_empty_header_value():
    i = ("command:header:HEADER:key:\n"
         "command:header::value:")
    o = text2table(i)
    assert o == {"header": [{"key":"value"}]}

def test_spaces_in_values():
    i = ("command:header:HEADER:key\n"
         "command:header::value with spaces")
    o = text2table(i)
    assert o == {"header": [{"key":"value with spaces"}]}

def test_ignore_endlines():
    i = ("command:header:HEADER:key\n"
         "command:header::value\n"
         "\n"
         "\n")
    o = text2table(i)
    assert o == {"header": [{"key":"value"}]}    

def test_two_rows():
    i = ("command:header:HEADER:key\n"
         "command:header::value1\n"
         "command:header::value2\n")
    o = text2table(i)
    assert o == {"header": [{"key": "value1"},
                            {"key": "value2"}]}

def test_two_empty_headers():
    i = ("command:header1:HEADER:k11\n"
         "command:header2:HEADER:k12\n")
    o = text2table(i)
    assert o == {"header1": [], "header2": [] }

def test_two_headers():
    i = ("command:header1:HEADER:k11\n"
         "command:header2:HEADER:k12\n"
         "command:header1::v11\n"
         "command:header2::v12\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11"}],
                 "header2": [{"k12": "v12"}] }

def test_two_headers_two_values():
    i = ("command:header1:HEADER:k11:k21\n"
         "command:header2:HEADER:k12:k22\n"
         "command:header1::v11:v21\n"
         "command:header2::v12:v22\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11", "k21": "v21"}],
                 "header2": [{"k12": "v12", "k22": "v22"}] } 

def test_two_headers_two_values_different_lengths():
    i = ("command:header1:HEADER:k11:k21\n"
         "command:header2:HEADER:k12\n"
         "command:header1::v11:v21\n"
         "command:header2::v12\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11", "k21": "v21"}],
                 "header2": [{"k12": "v12"}] }

def test_headers_without_names():
    i = ("command::HEADER:k1:k2:k3\n"
         "command:::v1:v2:v3\n")
    o = text2table(i)
    assert o == {"": [{"k1": "v1", "k2": "v2", "k3": "v3"}]}

# filesystem tests

from gpfs import FS

def test_fs_reserved_name():
    with pytest.raises(ValueError):
        FS("all")

MMLSFS_HEADER = \
"mmlsfs::HEADER:version:reserved:reserved:deviceName:fieldName:data:remarks:"

def test_fs_simple(mocker):
    mocker.patch("subprocess.run")
    #mocker.patch("subprocess.CompletedProcess")
    mmlsfs_data = ("mmlsfs::0:1:::fs1:minFragmentSize:8192::\n"
                   "mmlsfs::0:1:::fs1:inodeSize:4096::\n")
    subprocess.run.return_value.stdout = bytes(
                                               MMLSFS_HEADER + "\n" + mmlsfs_data,
                                               "utf-8")
    subprocess.run.return_value.returncode = 0
    fs = FS("fs1")
    args = subprocess.run.call_args[0]
    assert ["/usr/lpp/mmfs/bin/mmlsfs", "fs1", "-Y"] in args

    assert fs.inodeSize == 4096
    assert fs.minFragmentSize == 8192

def test_fs_dont_exist(mocker):
    mocker.patch("subprocess.run")
    subprocess.run.return_value.returncode = 1
    msg = ("mmlsfs: File system i_dont_exist is not known to the GPFS cluster.\n"
           "mmlsfs: Command failed. Examine previous error messages to determine cause.\n")
    subprocess.run.return_value.stderr = bytes(msg, "utf-8")

    with pytest.raises(IndexError):
        fs = FS("i_dont_exist")

from gpfs import Cluster


MMLSCLUSTER_HEADER = """mmlscluster:clusterSummary:HEADER:version:reserved:reserved:clusterName:clusterId:uidDomain:rshPath:rshSudoWrapper:rcpPath:rcpSudoWrapper:repositoryType:primaryServer:secondaryServer:
mmlscluster:clusterNode:HEADER:version:reserved:reserved:nodeNumber:daemonNodeName:ipAddress:adminNodeName:designation:otherNodeRoles:adminLoginName:otherNodeRolesAlias:
mmlscluster:cnfsSummary:HEADER:version:reserved:reserved:cnfsSharedRoot:cnfsMoundPort:cnfsNFSDprocs:cnfsReboot:cnfsMonitorEnabled:cnfsGanesha:
mmlscluster:cnfsNode:HEADER:version:reserved:reserved:nodeNumber:daemonNodeName:ipAddress:cnfsState:cnfsGroupId:cnfsIplist:
mmlscluster:cesSummary:HEADER:version:reserved:reserved:cesSharedRoot:EnabledServices:logLevel:addressPolicy:interfaceMode:
mmlscluster:cesNode:HEADER:version:reserved:reserved:nodeNumber:daemonNodeName:ipAddress:cesGroup:cesState:cesIpList:
mmlscluster:cloudGatewayNode:HEADER:version:reserved:reserved:nodeNumber:daemonNodeName:
mmlscluster:commentNode:HEADER:version:reserved:reserved:nodeNumber:daemonNodeName:comment_enc:
"""

def test_cluster(mocker):
    mocker.patch("subprocess.run")
    subprocess.run.return_value.returncode = 0
    mmlscluster_data = ("mmlscluster:clusterSummary:0:1:::name:123:domain:ssh:no:scp:no:CCR:s1:s2:\n"
     "mmlscluster:clusterNode:0:1:::4:a02hgf01:1.1.1.1:s1:quorumManager::::")
    subprocess.run.return_value.stdout = bytes(
                                               MMLSCLUSTER_HEADER + "\n" + mmlscluster_data,
                                               "utf-8")
    cluster = Cluster()
    assert cluster.name == "name"
    assert cluster.id == 123

    assert len(cluster.nodes) ==  1
    assert cluster.nodes[0].ipAddress == "1.1.1.1"
    assert cluster.nodes[0].designation == "quorumManager"

# test filesets

from gpfs import Fileset

MMLSFILESET_HEADER = """mmlsfileset::HEADER:version:reserved:reserved:filesystemName:filesetName:id:rootInode:status:path:parentId:created:inodes:dataInKB:comment:filesetMode:afmTarget:afmState:afmMode:afmFileLookupRefreshInterval:afmFileOpenRefreshInterval:afmDirLookupRefreshInterval:afmDirOpenRefreshInterval:afmAsyncDelay:afmNeedsRecovery:afmExpirationTimeout:afmRPO:afmLastPSnapId:inodeSpace:isInodeSpaceOwner:maxInodes:allocInodes:inodeSpaceMask:afmShowHomeSnapshots:afmNumReadThreads:reserved:afmReadBufferSize:afmWriteBufferSize:afmReadSparseThreshold:afmParallelReadChunkSize:afmParallelReadThreshold:snapId:afmNumFlushThreads:afmPrefetchThreshold:afmEnableAutoEviction:permChangeFlag:afmParallelWriteThreshold:freeInodes:afmNeedsResync:afmParallelWriteChunkSize:afmNumWriteThreads:afmPrimaryID:afmDRState:afmAssociatedPrimaryId:afmDIO:afmGatewayNode:afmIOFlags:afmVerifyDmapi:afmSkipHomeACL:afmSkipHomeMtimeNsec:afmForceCtimeChange:afmSkipResyncRecovery:afmSkipConflictQDrop:afmRefreshAsync:afmParallelMounts:afmRefreshOnce:afmSkipHomeCtimeNsec:afmReaddirOnce:afmResyncVer2:afmSnapUncachedRead:afmFastCreate:afmObjectXattr:afmObjectVHB:afmObjectNoDirectoryObj:afmSkipHomeRefresh:afmObjectGCS:afmObjectUserKeys:afmWriteOnClose:afmObjectSSL:afmObjectACL:afmMUPromoted:afmMUAutoRemove:afmObjFastReaddir:afmObjectBlkIO:preventSnapshotRestore:permInheritFlag:afmIOFlags2:afmRemoteUpdate:falStatus:"""

def test_fileset(mocker):
    mocker.patch("subprocess.run")
    subprocess.run.return_value.returncode = 0
    mmlsfileset_data = "mmlsfileset::0:1:::fs1:fileset_name:10:65828:Linked:%2Fa%5Fb%2Fc:0:Wed Dec 14 14%3A17%3A55 2022:-:-:fset_name:off:-:-:-:-:-:-:-:-:-:-:-:-:0:0:0:0:0:-:-:-:-:-:-:-:-:0:-:-:-:chmodAndUpdateAcl:-:0:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:-:no:inheritAclAndAddMode:-:-:default:"

    subprocess.run.return_value.stdout = bytes(
                                               MMLSFILESET_HEADER + "\n" + mmlsfileset_data,
                                               "utf-8")
    fileset = Fileset("fs","fileset_name")

    assert fileset.filesetName == "fileset_name" 

def test_nonexistent_fileset(mocker):
    mocker.patch("subprocess.run")  
    subprocess.run.return_value.returncode = 22
    subprocess.run.return_value.stderr = ("Fileset named fset does not exist.\n"
                                           "mmlsfileset: Command failed. Examine previous error messages to determine cause.\n").encode()
    with pytest.raises(IndexError):
        Fileset("fs","fset")
