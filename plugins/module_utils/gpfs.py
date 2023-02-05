import subprocess
from urllib.parse import unquote
from types import SimpleNamespace
from os.path import join

BINARY_PATH="/usr/lpp/mmfs/bin"

def text2table(text):

    headers = {}
    results = {}
    for l in text.split("\n"):
        values = l.split(":")
        if len(values) < 3:
            continue
        header_name = values[1]
        if values[2] == "HEADER":
            headers[header_name] = values[3:]
            results[header_name] = []
        else:
            current_header = headers[header_name]
            current_values = values[3:]
            new_row = dict(zip(current_header, current_values))
            if "" in new_row:
                del new_row[""] # we don't need empty keys
            results[header_name] += [new_row]

    return results

class Cluster:
    def __init__(self):
        mmlscluster = subprocess.run([join(BINARY_PATH,"mmlscluster"), "-Y"],
                                     check=True,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE)
        properties = text2table(mmlscluster.stdout.decode())
        self._properties = properties

    @property
    def name(self):
        return self._properties["clusterSummary"][0]["clusterName"]

    @property
    def nodes(self):
        return [SimpleNamespace(**n)
                for n in self._properties["clusterNode"]]

    @property
    def id(self):
        return int(self._properties["clusterSummary"][0]["clusterId"])


class FS:
    def __init__(self,name):
        if name == "all":
            raise ValueError(("'all' is a reserved word "
                              "and cannot be used as filesystem name"))
        self.name = name
        mmlsfs = subprocess.run([join(BINARY_PATH,"mmlsfs"),name,"-Y"],
                                check=False,
                                stdout = subprocess.PIPE,
                                stderr = subprocess.PIPE)

        if mmlsfs.returncode > 0:
            if "is not known to the GPFS cluster" in mmlsfs.stderr.decode():
                raise IndexError(f"{name} filesystem not found")
            else:
                raise Exception(mmlsfs.stderr.decode())
        properties = text2table(mmlsfs.stdout.decode())[""]
        for p in properties:
            key = p["fieldName"]
            try:
                value = int(p["data"])
            except ValueError:
                value = p["data"]
            setattr(self, key, value)

class FilesetQuota:

    @staticmethod
    def read(filesystem, fileset_name):
        mmlsquota = subprocess.run([join(BINARY_PATH,"mmlsquota"), "-Y", "-j",
                                    fileset_name, filesystem],
                                     check=True,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE)
        props = text2table(mmlsquota.stdout.decode())
        quota = FilesetQuota(filesystem, fileset_name)
        quota.block_soft = int(props["fileset"][0]["blockQuota"])
        quota.block_hard = int(props["fileset"][0]["blockLimit"])
        quota.file_soft = int(props["fileset"][0]["filesQuota"])
        quota.file_hard = int(props["fileset"][0]["filesLimit"])
        return quota


    def __init__(self, filesystem, fileset_name,
                 block_soft = 0, block_hard = 0,
                 file_soft = 0, file_hard = 0):
        self.filesystem = filesystem
        self.fileset_name = fileset_name
        self.block_soft = block_soft
        self.block_hard = block_hard
        self.file_soft = file_soft
        self.file_hard = file_hard

    def apply(self):
        subprocess.run([join(BINARY_PATH,"mmsetquota"),
                        f"{self.filesystem}:{self.fileset_name}",
                        "--block",
                        f"{self.block_soft}K:{self.block_hard}K",
                        "--files",
                        f"{self.file_soft}:{self.file_hard}"],
                        check=True,
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE)


class Fileset:

    @staticmethod
    def link(filesystem, name, path):
        subprocess.run([join(BINARY_PATH,"mmlinkfileset"),
                       filesystem, name, "-J", path],
                       check = True,
                       stdout = subprocess.PIPE,
                       stderr = subprocess.PIPE)
        return Fileset(filesystem, name)

    @staticmethod
    def unlink(filesystem, name):
        subprocess.run([join(BINARY_PATH, "mmunlinkfileset"),
                       filesystem, name],
                       check = True,
                       stdout = subprocess.PIPE,
                       stderr = subprocess.PIPE)
        return Fileset(filesystem, name)

    @staticmethod
    def delete(filesystem, name):
        cmd = subprocess.run([join(BINARY_PATH,"mmdelfileset"),
                              filesystem, name],
                             check = False,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)

        if cmd.returncode > 0:
            raise Exception(cmd.stderr.decode())
        return

    @staticmethod
    def _create_or_update(executable, filesystem, name,
        allow_permission_change = "chmodAndSetAcl",
        allow_permission_inherit = "inheritAclOnly",
        comment = None):

        command = [executable,
                    filesystem,
                    name,
                    "--allow-permission-change", allow_permission_change,
                    "--allow-permission-inherit", allow_permission_inherit]
        if comment is not None:
            command += ["-t", comment]

        cmd = subprocess.run(command,
                             check = False,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)

        if cmd.returncode > 0:
            raise Exception(cmd.stderr.decode())
        return Fileset(filesystem, name)


    @staticmethod
    def create(filesystem, name,
        allow_permission_change = "chmodAndSetAcl",
        allow_permission_inherit = "inheritAclOnly",
        comment = None):
        return Fileset._create_or_update(join(BINARY_PATH, "mmcrfileset"),
                                         filesystem, name,
                                         comment=comment,
                                         allow_permission_change=
                                          allow_permission_change,
                                         allow_permission_inherit=
                                          allow_permission_inherit)

    @staticmethod
    def update(filesystem, name,
        allow_permission_change = "chmodAndSetAcl",
        allow_permission_inherit = "inheritAclOnly",
        comment = None):
        return Fileset._create_or_update(join(BINARY_PATH, "mmchfileset"),
                                         filesystem, name,
                                         comment=comment,
                                         allow_permission_change=
                                          allow_permission_change,
                                         allow_permission_inherit=
                                          allow_permission_inherit)

    def __init__(self, filesystem, name):
        mmlsfileset = subprocess.run([join(BINARY_PATH, "mmlsfileset"),
                                      filesystem,name,"-Y"],
                                     check=False,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE)
        if mmlsfileset.returncode > 0:
            not_found = f"Fileset named {name} does not exist"
            if not_found in mmlsfileset.stderr.decode():
                raise IndexError(not_found)
            else:
                raise Exception(mmlsfileset.stderr.decode())
        properties = text2table(mmlsfileset.stdout.decode())[""][0]
        for (k,v) in properties.items():
            try:
                v = int(v)
            except ValueError:
                pass
            if k == "path":
                v = unquote(v)
            setattr(self,k,v)

