import subprocess

def text2table(text):

    headers = {}
    results = {}
    for l in text.split():
        values = l.split(":")
        header_name = values[1]
        if values[2] == "HEADER":
            headers[header_name] = values[3:]
            results[header_name] = []
        else:
            current_header = headers[header_name]
            current_values = values[3:]
            new_row = dict(zip(current_header, current_values))
            results[header_name] += [new_row]

    return results

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
