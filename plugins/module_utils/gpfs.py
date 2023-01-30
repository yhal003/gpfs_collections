import subprocess
from types import SimpleNamespace

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
        mmlscluster = subprocess.run(["/usr/lpp/mmfs/bin/mmlscluster", "-Y"],
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
        mmlsfs = subprocess.run(["/usr/lpp/mmfs/bin/mmlsfs",name,"-Y"],
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

class Fileset:

    @staticmethod
    def create(cls, filesystem, name, 
        allow_permission_change = "chmodAndSetAcl",
        allow_permission_inherit = "inheritAclOnly",
        comment = None):

        command = ["/usr/lpp/mmfs/bin/mmcrfileset", 
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

    def __init__(self, filesystem, name):
        mmlsfileset = subprocess.run(["/usr/lpp/mmfs/bin/mmlsfileset",
                                 filesystem,name,"-Y"],
                                check=False,
                                stdout = subprocess.PIPE,
                                stderr = subprocess.PIPE)
        if mmlsfileset.returncode > 0:
            not_found = f"Fileset named {name} does not exist"
            if not_found in mmlsfileset.stderr.decode():
                raise IndexError(not_found)
        properties = text2table(mmlsfileset.stdout.decode())[""][0]
        for (k,v) in properties.items():
            try:
                v = int(v)
            except ValueError:
                pass
            setattr(self,k,v)

