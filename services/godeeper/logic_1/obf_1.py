import re,random

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
        self.varnames = []
        self.posargs = []
        self.localvars = []
        self.lines = []
        self.top = []
        self.blocks=[]
    def AddLine(self,line,labels):
        self.lines.append(FuncLine(line,labels))
    def __str__(self):
        return "Func("+self.name+")"
    def __repr__(self):
        return self.__str__()

class Block:
    def __init__(self,num):
        self.lines=[]
        self.num=num
        self.is_conditional = False
        self.condition = None
        self.NextBlock = None
        self.NextTrue =  None
        self.NextFalse = None
        self.labels = []
        self.is_final = False

    def AddLine(self,line):
        self.lines.append(line)
    def __str__(self):
        nx=""
        if self.NextTrue:
            nx+= " NT:"+str(self.NextTrue.num)
        if self.NextFalse:
            nx+= " NF:"+str(self.NextFalse.num)
        if self.NextBlock:
            nx+= " N:"+str(self.NextBlock.num)
        return str(self.num)+")"+",".join(self.labels) + " " +self.lines[0].line + " " + nx
    def __repr__(self):
        return self.__str__()
class Obfuscator:
    def __init__(self,filename):
        self.filename = filename
        self.top = []
        self.functions = []
        self.fname2func = {}
        self.block_num = 1

    def ParseFile2(self):
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
                    cur_func = Function(res1[0])
                    self.functions.append(cur_func)
                    self.fname2func[cur_func.name] = cur_func
                    cur_func.top.append(line)
                    state = 3
                    continue
                self.top.append(line)
            elif state == 3:
                res1 = re.findall(r'^#\s*Method Name:\s*(\S+)\s*$',line)
                if len(res1)>0:
                    cur_func = Function(res1[0])
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
                res1 = re.findall(r'^#\s*Varnames:\s*$', line)
                if len(res1) > 0:
                    state = 4
                    continue
                res1 = re.findall(r'^#\s*Positional arguments:\s*$', line)
                if len(res1) > 0:
                    state = 5
                    continue
                res1 = re.findall(r'^#\s*Local variables:\s*$', line)
                if len(res1) > 0:
                    state = 6
                    continue
                res1 = re.findall(r'^#.+', line)
                if len(res1) > 0:
                    cur_func.top.append(line)
                    continue
                # Getting code
                res1 = re.findall(r'^\s*(\S+):\s*(\S+)\s*$',line)
                if len(res1) >0:
                    label,code = res1[0]
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
                res1 = re.findall(r'^#\s*([0-9A-Za-z ]+):\s*$',line)
                if len(res1)>0:
                    if res1[0] == 'Names':
                        state = 2
                    elif res1[0] == 'Varnames':
                        state = 4
                    elif res1[0] == 'Positional arguments':
                        state = 5
                    elif res1[0] == 'Local variables':
                        state = 6
                    continue
                res1 = re.findall(r'^#\s*\d+\:.+$',line)
                if len(res1)>0:
                    cur_func.constants.append(line)
                    continue
                # Getting code
                res1 = re.findall(r'^\s*(\S+):\s*(\S+)\s*$', line)
                if len(res1) > 0:
                    state = 3
                    label, code = res1[0]
                    cur_labels.append(label)
                    cur_func.AddLine(code, cur_labels)
                    cur_labels = []
                    continue
                res1 = re.findall(r'^\s*(\S+):\s*$', line)
                if len(res1) > 0:
                    state = 3
                    cur_labels.append(res1[0])
                    continue
                state = 3
                continue
            elif state == 2:  # Getting Names
                res1 = re.findall(r'^#\s*([0-9A-Za-z ]+):\s*$',line)
                if len(res1)>0:
                    if res1[0] == 'Names':
                        state = 2
                    elif res1[0] == 'Varnames':
                        state = 4
                    elif res1[0] == 'Positional arguments':
                        state = 5
                    elif res1[0] == 'Local variables':
                        state = 6
                    continue
                res1 = re.findall(r'^#\s*\d+\:.+$',line)
                if len(res1)>0:
                    cur_func.names.append(line)
                    continue
                # Getting code
                res1 = re.findall(r'^\s*(\S+):\s*(\S+)\s*$', line)
                if len(res1) > 0:
                    state = 3
                    label, code = res1[0]
                    cur_labels.append(label)
                    cur_func.AddLine(code, cur_labels)
                    cur_labels = []
                    continue
                res1 = re.findall(r'^\s*(\S+):\s*$', line)
                if len(res1) > 0:
                    state = 3
                    cur_labels.append(res1[0])
                    continue
                continue
            elif state == 4:  # Getting Varnames
                res1 = re.findall(r'^#\s*([0-9A-Za-z ]+):\s*$',line)
                if len(res1)>0:
                    if res1[0] == 'Names':
                        state = 2
                    elif res1[0] == 'Varnames':
                        state = 4
                    elif res1[0] == 'Positional arguments':
                        state = 5
                    elif res1[0] == 'Local variables':
                        state = 6
                    continue
                res1 = re.findall(r'^#\s*(.+)',line)
                if len(res1)>0:
                    res2 = res1[0].split(",")
                    cur_func.varnames = list(res2)
                    state = 3
                    continue
                raise ValueError("Cannot parse",line)
            elif state == 5:  # Getting Positional arguments
                res1 = re.findall(r'^#\s*([0-9A-Za-z ]+):\s*$',line)
                if len(res1)>0:
                    if res1[0] == 'Names':
                        state = 2
                    elif res1[0] == 'Varnames':
                        state = 4
                    elif res1[0] == 'Positional arguments':
                        state = 5
                    elif res1[0] == 'Local variables':
                        state = 6
                    continue
                res1 = re.findall(r'^#\s*(.+)',line)
                if len(res1)>0:
                    res2 = res1[0].split(",")
                    cur_func.posargs = list(res2)
                    state = 3
                    continue
                raise ValueError("Cannot parse",line)
            elif state == 6:  # Local variables
                res1 = re.findall(r'^#\s*([0-9A-Za-z ]+):\s*$',line)
                if len(res1)>0:
                    if res1[0] == 'Names':
                        state = 2
                    elif res1[0] == 'Varnames':
                        state = 4
                    elif res1[0] == 'Positional arguments':
                        state = 5
                    elif res1[0] == 'Local variables':
                        state = 6
                    continue
                res1 = re.findall(r'^#\s*\d+\:.+$',line)
                if len(res1)>0:
                    cur_func.localvars.append(line)
                    continue
                # Getting code
                res1 = re.findall(r'^\s*(\S+):\s*(\S+)\s*$', line)
                if len(res1) > 0:
                    state = 3
                    label, code = res1[0]
                    cur_labels.append(label)
                    cur_func.AddLine(code, cur_labels)
                    cur_labels = []
                    continue
                res1 = re.findall(r'^\s*(\S+):\s*$', line)
                if len(res1) > 0:
                    state = 3
                    cur_labels.append(res1[0])
                    continue
                continue
            else:
                raise ValueError("Unknown state")

    def ProduceFile2(self,fname):
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
            if len(fn.varnames)>0:
                f.write("# Varnames:\n")
                f.write("#\t"+",".join(fn.varnames)+"\n")
            if len(fn.posargs) > 0:
                f.write("# Positional arguments:\n")
                f.write("#\t"+",".join(fn.posargs) + "\n")
            if len(fn.localvars) > 0:
                f.write("# Local variables:\n")
                f.write("\n".join(fn.localvars) + "\n")
            start_offset = self.label2block[fn.start_label].position
            b0 = start_offset % 255
            b1 = start_offset // 255
            if b1 != 0:
                f.write("EXTENDED_ARG %d" % b1 + "\n")
                f.write("JUMP_ABSOLUTE " + str(b0) + " # %s\n" % fn.start_label)
            else:
                f.write("NOP" + "\n")
                f.write("JUMP_ABSOLUTE " + str(b0) + " # %s\n" % fn.start_label)
            OFF = 4
            for block in fn.blocks[::1]:
                for lab in block.labels:
                    f.write(lab+":\n")
                for line in block.lines:
                    f.write("\t"+line.line + "\t\t\t# " + str(OFF)+"\n")
                    OFF+=2
        f.close()

    def SplitBlock(self,fn,block_idx):
        cur_block = fn.blocks[block_idx]
        if len(cur_block.lines) <= 6:
            return False
        idx_split = len(cur_block.lines)//2
        last_in_b = cur_block.lines[idx_split-1].line
        if "EXTENDED_ARG" in last_in_b:
            idx_split+=1
        new_block = Block(self.block_num)
        self.block_num += 1
        new_block.lines = cur_block.lines[idx_split:]
        new_block.labels = ["L_" + str(self.mylabels_num)]
        self.label2block[new_block.labels[0]] = new_block
        self.mylabels_num += 1
        cur_block.lines = cur_block.lines[:idx_split]
        fn.blocks = fn.blocks[:block_idx+1] + [new_block] + fn.blocks[block_idx+1:]
        cur_block.lines.append(FuncLine("\tNOP"))
        cur_block.lines.append(FuncLine("\tJUMP_ABSOLUTE %s\n" % (new_block.labels[0])))
        new_block.type = cur_block.type
        cur_block.type = "JUMP_ABSOLUTE"
        new_block.NextBlock = cur_block.NextBlock
        new_block.NextTrue = cur_block.NextTrue
        new_block.NextFalse = cur_block.NextFalse
        cur_block.NextBlock = new_block
        return True

    def HideConstantStr(self,fn,const_num):
        a=fn.constants[const_num]

    def MakeBlocks(self):
        self.mylabels_num = 0
        for fn in self.functions:
            fn.valid_labels = []
            for line in fn.lines:
                cur_code = line.line
                res1 = re.findall(r'^POP_JUMP_IF_FALSE\s+(\S+)', cur_code)
                if len(res1) > 0:
                    fn.valid_labels.append(res1[0])
                res1 = re.findall(r'^JUMP_FORWARD\s+(\S+)', cur_code)
                if len(res1) > 0:
                    fn.valid_labels.append(res1[0])
                res1 = re.findall(r'^JUMP_ABSOLUTE\s+(\S+)', cur_code)
                if len(res1) > 0:
                    fn.valid_labels.append(res1[0])
                res1 = re.findall(r'^FOR_ITER\s+(\S+)', cur_code)
                if len(res1) > 0:
                    fn.valid_labels.append(res1[0])
        self.label2block = {}
        for fn in self.functions:
            cur_block = Block(self.block_num)
            self.block_num += 1
            fn.blocks.append(cur_block)
            for line in fn.lines:
                labels = line.labels
                true_labels = []
                for lab in labels:
                    if lab in fn.valid_labels:
                        true_labels.append(lab)
                if len(true_labels) > 0:
                    if len(cur_block.lines) > 0:
                        new_block = Block(self.block_num)
                        for ll in true_labels:
                            self.label2block[ll] = new_block
                        new_block.labels = true_labels
                        fn.blocks.append(new_block)
                        self.block_num += 1
                        cur_block = new_block
                    else:
                        cur_block.labels += true_labels
                        for ll in true_labels:
                            self.label2block[ll] = cur_block
                else:
                    if len(cur_block.labels) == 0:
                        cur_block.labels = ["L_" + str(self.mylabels_num)]
                        self.label2block[cur_block.labels[0]] = cur_block
                        self.mylabels_num += 1

                cur_block.lines.append(line)
                if "RETURN_VALUE" in line.line:
                    cur_block.is_final = True
                if "POP_JUMP_IF_FALSE" in line.line or \
                    "JUMP_FORWARD" in line.line or \
                    "JUMP_ABSOLUTE" in line.line or \
                    "FOR_ITER" in line.line :
                    cur_block = Block(self.block_num)
                    if len(true_labels) == 0:
                        cur_block.labels = ["L_"+str(self.mylabels_num)]
                        self.label2block[cur_block.labels[0]] = cur_block
                        self.mylabels_num+=1
                    fn.blocks.append(cur_block)
                    self.block_num += 1

        for fn in self.functions:
            idx = 0
            while idx < len(fn.blocks):
                block = fn.blocks[idx]
                cur_code = block.lines[-1].line
                res1 = re.findall(r'^POP_JUMP_IF_FALSE\s+(\S+)', cur_code)
                if len(res1) > 0:
                    block.NextTrue = fn.blocks[idx+1]
                    block.NextFalse = self.label2block[res1[0]]
                    next_label = fn.blocks[idx+1].labels[0]
                    if 'EXTENDED_ARG' in block.lines[-2].line:
                        block.lines = block.lines[:-2] + [block.lines[-1]]
                    block.lines = block.lines[:-1] + [FuncLine("\tNOP")] + [block.lines[-1]]
                    block.lines.append(FuncLine("\tNOP"))
                    block.lines.append(FuncLine("\tJUMP_ABSOLUTE\t"+ next_label  ))
                    block.is_conditional = True
                    block.type= "POP_JUMP_IF_FALSE"
                    idx +=1
                    continue
                res1 = re.findall(r'^JUMP_FORWARD\s+(\S+)', cur_code)
                if len(res1) > 0:
                    block.NextBlock =  self.label2block[res1[0]]
                    if 'EXTENDED_ARG' in block.lines[-2].line:
                        block.lines = block.lines[:-2] + [block.lines[-1]]

                    block.lines = block.lines[:-1] + [FuncLine("\tNOP")] + \
                                  [FuncLine("\tJUMP_ABSOLUTE\t" + res1[0])]
                    block.type = "JUMP_ABSOLUTE"
                    idx += 1
                    continue
                res1 = re.findall(r'^JUMP_ABSOLUTE\s+(\S+)', cur_code)
                if len(res1) > 0:
                    block.NextBlock =  self.label2block[res1[0]]
                    if len(block.lines)>=2 and 'EXTENDED_ARG' in block.lines[-2].line:
                        block.lines = block.lines[:-2] + [block.lines[-1]]
                    block.lines = block.lines[:-1] + [FuncLine("\tNOP")] +[block.lines[-1]]
                    block.type = "JUMP_ABSOLUTE"
                    idx += 1
                    continue
                res1 = re.findall(r'^FOR_ITER\s+(\S+)', cur_code)
                if len(res1) > 0:
                    block.NextTrue = fn.blocks[idx + 1]
                    block.NextFalse = self.label2block[res1[0]]
                    next_label = fn.blocks[idx + 1].labels[0]
                    block.lines.append(FuncLine("\tNOP"))
                    block.lines.append(FuncLine("\tJUMP_ABSOLUTE\t" + next_label))
                    block.lines.append(FuncLine("\tNOP"))
                    block.lines.append(FuncLine("\tJUMP_ABSOLUTE\t" + res1[0]))
                    block.is_conditional = True
                    block.type = "FOR_ITER"
                    idx += 1
                    continue
                if not block.is_final:
                    block.NextBlock = fn.blocks[idx+1]
                    next_label = fn.blocks[idx + 1].labels[0]
                    block.lines.append(FuncLine("\tNOP"))
                    block.lines.append(FuncLine("\tJUMP_ABSOLUTE\t" + next_label))
                    block.type = "JUMP_ABSOLUTE"
                else:
                    block.type = "RETURN"

                idx += 1
            fn.start_label = fn.blocks[0].labels[0]
    def SwapBlocks(self):
        for fn in self.functions:
            #
            self.HideConstantStr(fn,1)

            # ------------------------------------------

            idx=0
            try_block = 0
            while idx < 100:
                res = self.SplitBlock(fn, try_block)
                if res:
                    idx+=1
                else:
                    try_block +=1
                if try_block >= len(fn.blocks):
                    break

            #fn.blocks = fn.blocks[::-1]
            random.shuffle(fn.blocks)

            # ------------------------------------------
            position = 4 # Для начального джампа
            for block in fn.blocks:
                block.cmd_size = 2*len(block.lines)
                if position % 255 == 0:
                    position +=2
                    block.lines = [FuncLine("NOP")] + block.lines
                block.position = position
                position += block.cmd_size
            cur_idx = 0
            while cur_idx <  len(fn.blocks):
                block = fn.blocks[cur_idx]
                if block.type == "JUMP_ABSOLUTE":
                    res1 = re.findall(r'^\s*(\S+)\s+(\S+)', block.lines[-1].line)
                    command = res1[0][0]
                    jump_dest = res1[0][1]
                    block_dest = self.label2block[jump_dest]
                    abs_addr = block_dest.position
                    b0 = abs_addr % 255
                    b1 = abs_addr // 255
                    if b1 != 0:
                        block.lines = block.lines[:-2]
                        block.lines.append(FuncLine("EXTENDED_ARG %d" % b1))
                        block.lines.append(FuncLine("%s %d # %s" % (command, b0, res1[0][1])))
                    else:
                        block.lines = block.lines[:-1]
                        block.lines.append(FuncLine("%s %d  # %s" % (command, b0, res1[0][1])))
                elif block.type == "POP_JUMP_IF_FALSE":
                    res1 = re.findall(r'^\s*(\S+)\s+(\S+)', block.lines[-3].line)
                    command = res1[0][0]
                    jump_dest = res1[0][1]
                    block_dest = self.label2block[jump_dest]
                    abs_addr = block_dest.position
                    b0 = abs_addr % 255
                    b1 = abs_addr // 255
                    #   NOP                     -4
                    #   POP_JUMP_IF_FALSE       -3
                    #   NOP                     -2
                    #   JMP                     -1
                    if b1 != 0:
                        block.lines[-4] = FuncLine("EXTENDED_ARG %d" % b1)
                    block.lines[-3] = FuncLine("%s %d # %s" % (command, b0, res1[0][1]))

                    res1 = re.findall(r'^\s*(\S+)\s+(\S+)', block.lines[-1].line)
                    command = res1[0][0]
                    jump_dest = res1[0][1]
                    block_dest = self.label2block[jump_dest]
                    abs_addr = block_dest.position
                    b0 = abs_addr % 255
                    b1 = abs_addr // 255
                    if b1 != 0:
                        block.lines[-2] = FuncLine("EXTENDED_ARG %d" % b1)
                    block.lines[-1] = FuncLine("%s %d # %s" % (command, b0, res1[0][1]))
                elif block.type == "FOR_ITER":
                    #   FOR_ITER  LLL           -5
                    #   EXTENDED_ARG            -4
                    #   JMP if no               -3
                    #   LLL:    EXTENDED_ARG    -2
                    #           JMP if yes      -1
                    # block.lines[-5] = FuncLine("\tFOR_ITER %d" % (block.position + block.cmd_size-4))
                    block.lines[-5] = FuncLine("\tFOR_ITER 4")
                    res1 = re.findall(r'^\s*([A-Z_]+)\s+(\S+)', block.lines[-3].line)
                    if len(res1)>0:
                        label = res1[0][1]
                        abs_addr = self.label2block[label].position
                        b0 = abs_addr % 255
                        b1 = abs_addr // 255
                        if b1 != 0:
                            block.lines[-4] = FuncLine("EXTENDED_ARG %d" % b1)
                            block.lines[-3] = FuncLine("JUMP_ABSOLUTE %d # %s" % (b0, label ))
                        else:
                            block.lines[-3] = FuncLine("JUMP_ABSOLUTE %d # %s" % (b0, label ))
                    res1 = re.findall(r'^\s*([A-Z_]+)\s+(\S+)', block.lines[-1].line)
                    if len(res1) > 0:
                        label = res1[0][1]
                        abs_addr = self.label2block[label].position
                        b0 = abs_addr % 255
                        b1 = abs_addr // 255
                        if b1 != 0:
                            block.lines[-2] = FuncLine("EXTENDED_ARG %d" % b1)
                            block.lines[-1] = FuncLine("JUMP_ABSOLUTE %d # %s" % (b0, label))
                        else:
                            block.lines[-1] = FuncLine("JUMP_ABSOLUTE %d # %s" % (b0, label))
                cur_idx+=1


if __name__ == "__main__":
    obf = Obfuscator("1.pyasm")
    obf.ParseFile2()
    obf.MakeBlocks()
    obf.SwapBlocks()
    print(obf)
    obf.ProduceFile2("2.pyasm")
