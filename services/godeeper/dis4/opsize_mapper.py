import re


def CreateSizeMap(size_file):
    f=open(size_file)
    sizemap = {}
    commands=[]
    for line in f:
        line = line.replace(">>","")
        res1 = re.findall(r'^\s+(\d+)\s+([A-Z_]+)',line)
        if len(res1)>0:
            commands.append(res1[0])
        res1 = re.findall(r'^\s*\d+:\s+(\d+)\s+([A-Z_]+)', line)
        if len(res1) > 0:
            commands.append(res1[0])
    idx=0
    while idx < len(commands)-1:
        next = commands[idx+1]
        cur = commands[idx]
        if not cur[1] in sizemap and int(next[0]) - int(cur[0]) > 0:
            sizemap[cur[1]] = int(next[0]) - int(cur[0])
        idx+=1
    return sizemap

if __name__ == "__main__":
    res = CreateSizeMap("1_size.pyasm")
    print(res)
