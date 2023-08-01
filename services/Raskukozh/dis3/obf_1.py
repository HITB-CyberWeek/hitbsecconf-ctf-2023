import re

class FuncLine:
    def __init__(self,line,labels=[]):
        self.line = line
        self.labels=labels
    def __str__(self):
        return ",".join(self.labels) + "|" + self.line
    def __repr__(self):
        return self.__str__()

class Function:
    def __init__(self,name):
        self.name = name
        self.constants = []
        self.names = []
        self.lines = []
        self.top = []
    def AddLine(self,line,labels):
        self.lines.append(FuncLine(line,labels))

class Block:
    def __init__(self):
        self.lines=[]
        self.is_conditional = False
        self.condition = None
        self.NextBlock = None
        self.NextTrue =  None
        self.NextFalse = None
        self.labels = []
        self.is_final = False

    def AddLine(self,line):
        self.lines.append(line)

class Obfuscator:
    def __init__(self,filename):
        self.filename = filename
        self.top = []
        self.functions = []
        self.fname2func = {}

    def ParseFile(self):
        fl = open(self.filename)
        state = 0
        cur_func = None
        cur_labels = []
        for line in fl:
            line = line.strip()
            if len(line) == 0:
                continue
            if state == 0:
                res1 = re.findall(r'^#\s*Method Name:\s*(\S+)\s*$',line)
                if len(res1)>0:
                    cur_func = Function(res1[0][0])
                    self.functions.append(cur_func)
                    self.fname2func[cur_func.name] = cur_func
                    cur_func.top.append(line)
                    state = 3
                    continue
                self.top.append(line)
            elif state == 3:
                res1 = re.findall(r'^#\s*Method Name:\s*(\S+)\s*$',line)
                if len(res1)>0:
                    cur_func = Function(res1[0][0])
                    self.functions.append(cur_func)
                    self.fname2func[cur_func.name] = cur_func
                    cur_func.top.append(line)
                    continue
                res1 = re.findall(r'^#\s*Constants:\s*$',line)
                if len(res1)>0:
                    state = 1
                    continue
                res1 = re.findall(r'^#\s*Names:\s*$', line)
                if len(res1) > 0:
                    state = 2
                    continue
                res1 = re.findall(r'^#.+', line)
                if len(res1) > 0:
                    cur_func.top.append(line)
                    continue
                # Getting code
                res1 = re.findall(r'^\s*(\S+):\s*(\S+)\s*$',line)
                if len(res1) >0:
                    label,code = res[0]
                    cur_labels.append(label)
                    cur_func.AddLine(code,cur_labels)
                    cur_labels = []
                    continue
                res1 = re.findall(r'^\s*(\S+):\s*$',line)
                if len(res1) >0:
                    cur_labels.append(res1[0])
                    continue
                cur_func.AddLine(line,cur_labels)
                cur_labels = []
            elif state == 1: # Getting constants
                res1 = re.findall(r'^#\s*Names:\s*$',line)
                if len(res1)>0:
                    state = 2
                    continue
                res1 = re.findall(r'^#\s*\d+\:.+$',line)
                if len(res1)>0:
                    cur_func.constants.append(line)
                    continue
                state = 3
                continue
            elif state == 2:  # Getting Names
                res1 = re.findall(r'^#\s*\d+\:.+$',line)
                if len(res1)>0:
                    cur_func.names.append(line)
                    continue
                state = 3
                continue
            else:
                raise ValueError("Unknown state")
    def ProduceFile(self,fname):
        f=open(fname,"w")
        f.write("\n".join(self.top) + "\n")
        for fn in self.functions:
            f.write("\n".join(fn.top)+"\n")
            if len(fn.constants)>0:
                f.write("# Constants:\n")
                f.write("\n".join(fn.constants)+"\n")
            if len(fn.names)>0:
                f.write("# Names:\n")
                f.write("\n".join(fn.names)+"\n")
            for ln in fn.lines:
                for lab in ln.labels:
                    f.write(lab+":\n")
                f.write(ln.line+"\n")

    def MakeBlocks(self):
        mylabels_num = 0
        for fn in self.functions:
            cur_block = None
            tmp_labels = []
            for line in fn.lines:
                labels = line.labels + tmp_labels
                code = line.line
                if len(labels)>0:
                    new_block = Block()
                    if cur_block != None:
                        if cur_block.is_conditional:
                            pass
                        else:
                            cur_block.NextBlock=new_block
                    new_block.labels = labels
                    tmp_labels = []
                    cur_block = new_block
                res1 = re.findall(r'^POP_JUMP_IF_FALSE\s+(\S+)',code)
                if len(res1)>0:
                    label_next = res1[0]
                    cur_block.is_conditional = True
                    self.NextFalse = label_next
                    next_true_label = "MyLabel_"+str(mylabels_num)
                    mylabels_num+=1
                    self.NextTrue = mylabels_num
                    tmp_labels.append(next_true_label)
                    continue
                res1 = re.findall(r'^COMPARE_OP\s+(\S+)',code)
                if len(res1)>0:
                    cur_block.condition = code
                    continue
                res1 = re.findall(r'^JUMP_FORWARD\s+(\S+)',code)
                if len(res1)>0:
                    label_next = res1[0]
                    cur_block.NextBlock = res1[0]
                res1 = re.findall(r'^JUMP_ABSOLUTE\s+(\S+)',code)
                if len(res1)>0:
                    label_next = res1[0]
                    cur_block.NextBlock = res1[0]
                res1 = re.findall(r'^RETURN_VALUE',code)
                if len(res1)>0:
                    cur_block.is_final =True
                    next_true_label = "MyLabel_"+str(mylabels_num)
                    mylabels_num+=1
                    tmp_labels.append(next_true_label)
                    continue

                cur_block.lines.append(line)





if __name__ == "__main__":
    obf = Obfuscator("1.pyasm")
    obf.ParseFile()
    print(obf)
    obf.ProduceFile("2.pyasm")
