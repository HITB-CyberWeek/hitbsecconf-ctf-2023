def GetTOK():
    # TOK1 = Hash1(COMP1) + Hash2(secret+Hash1(COMP1))
    # __builtins__.__dict__['exec']("import inspect; aaa=inspect.currentframe().f_back.f_locals",)
    tmp1=""
    for c in [224, 228, 249, 230, 251, 253, 169, 224, 231, 250, 249, 236, 234, 253]:
        tmp1 += chr(c ^ 137)
    # print(tmp1)

    exec(tmp1,globals(),locals())
    # myCOMP1 = exec("aa.currentframe().f_back.f_locals['COMP1']",globals(),locals())

    for f1 in list(locals()[tmp1[7:]].__dict__):
     if len(f1)>2 and f1[1] == 'u' and f1[5] == 'n':
       res1=locals()[tmp1[7:]].__dict__[f1]()

    key=[]
    key.append(13)
    key.append(89)
    key.append(37)
    key.append(34)
    key.append(22)
    res2_e = [42, 26, 106, 111, 70, 60, 126, 5, 75, 120, 45, 43, 64, 81, 39, 35, 63, 122, 64, 119, 110, 50, 11, 68, 73, 97, 54, 70, 67, 122, 126]
    ii=0
    while ii < len(res2_e):
        res2_e[ii] = res2_e[ii] ^ key[ii % len(key)]
        ii+=1
    key=[]
    key.append(34)
    key.append(21)
    key.append(45)
    key.append(23)
    key.append(54)
    res2_ee = [80, 112, 94, 38, 24, 68, 74, 79, 118, 85, 73, 59, 75, 72, 90, 77, 118, 76, 123, 69, 121, 50, 110, 88, 123, 114, 36, 10, 74]
    i=0
    while i < len(res2_ee):
        res2_ee[i] = res2_ee[i] ^ key[i % len(key)]
        i+=1

    key=[]
    key.append(54)
    key.append(23)
    key.append(45)
    key.append(32)
    key.append(76)
    res3_e = [17, 101, 72, 81, 57, 83, 100, 89, 7, 108, 95, 121, 13, 82, 41, 69, 38, 3, 70, 19, 84, 118, 78, 75, 98, 80, 72, 74, 76, 35, 84, 118, 65, 83]
    iii=0
    while iii < len(res3_e):
        res3_e[iii] = res3_e[iii] ^ key[iii % len(key)]
        iii+=1

    res3_ee = [68, 114, 94, 17, 98, 80, 72, 79, 65, 47, 93, 57, 75, 127, 43, 90, 120, 79, 65, 32, 69, 76, 10, 82, 41, 71, 98, 72, 83, 56, 17, 74]
    iiii=0
    while iiii < len(res3_ee):
        res3_ee[iiii] = res3_ee[iiii] ^ key[iiii % len(key)]
        iiii+=1

    key=[]
    key.append(24)
    key.append(53)
    key.append(75)
    key.append(26)
    key.append(78)

    res4_e=[63, 96, 56, 127, 60, 53, 116, 44, 127, 32, 108, 18, 107, 115, 32, 56, 71, 46, 105, 125, 54, 93, 46, 123, 42, 125, 71, 56]
    for i in range(len(res4_e)):
        res4_e[i] = res4_e[i] ^ key[i % len(key)]
    # print(bytes(res4_e).decode())

    res4_ee=[106, 80, 56, 41, 96, 112, 80, 42, 126, 43, 106, 70, 101, 125, 43, 108, 29, 108, 79, 61, 125, 71, 102, 91, 41, 125, 91, 63, 61, 103]
    for i in range(len(res4_ee)):
        res4_ee[i] = res4_ee[i] ^ key[i % len(key)]

    res2=""
    if eval(bytes(res2_e).decode()):
        res2 = eval(bytes(res2_ee).decode())
    else:
        return None
    if eval(bytes(res3_e).decode()):
        res3 = eval(bytes(res3_ee).decode())
    else:
        return None

    if eval(bytes(res4_e).decode()):
        res3 = eval(bytes(res4_ee).decode())
    else:
        return None



    # res2=""
    # if eval("'COMP1' in res1.f_back.f_locals"):
    #     res2 = eval("res1.f_back.f_locals['COMP1']")
    # else:
    #     return None
    # if eval("'request' in res1.f_back.f_globals"):
    #     res3 = eval("res1.f_back.f_globals['request']")
    # else:
    #     return None
    # if eval("'User-Agent' in res3.headers"):
    #     res3 = eval("res3.headers.get('User-Agent')")
    # else:
    #     return None

    # print(res2,res3)
    myCOMP1 = res2 + res3

    # prin  t("Tohash",myCOMP1)
    tmp1=""
    for c in [126, 93, 89, 110, 1, 94, 81, 15, 121, 80, 75, 1, 113, 95, 80, 14]:
        tmp1 += chr(c ^ 137)
    secret = tmp1
    mybuff = myCOMP1[:].encode()
    myhash = 0x00000000
    while len(mybuff) > 0:
        cur_byte=mybuff[0]
        mybuff=mybuff[1:]
        for i in range(4):
            lowbits = cur_byte & 0b11
            cur_byte = cur_byte // 2
            if lowbits & 1 == 0:
                if lowbits & 2 == 0:
                    myhash=myhash ^ 0xAC1385A2
                    myhash = ((myhash >> 1) | (myhash << 31)) & 0xFFFFFFFF
                else:
                    myhash=myhash ^ 0x15A8C9DA
            else:
                if lowbits & 2 == 0:
                    myhash=myhash ^ 0x81A79231
                    myhash = ((myhash >> 1) | (myhash << 31))& 0xFFFFFFFF
                else:
                    myhash=myhash ^ 0xA31BA34C

    TOK1 = "%08X" % myhash
    tmp = secret + TOK1

    mybuff = tmp.encode()
    myhash = 0xABA21342  # начальное значение регистра
    for byte in mybuff:
        myhash ^= byte
        myhash = ((myhash >> 1) | (myhash << 31)) & 0xFFFFFFFF

    sign = "%08X" % myhash
    TOK1 = TOK1 + sign
    return TOK1

# class A2:
#     def __init__(self):
#         index=0
#         self.data=['User-Agent']
#     def get(self,a):
#         return "uauauauaua"
#
#     def __iter__(self):
#         self.index = 0
#         return self
#     def __next__(self):
#         if self.index >= len(self.data):
#             raise StopIteration
#         result = self.data[self.index]
#         self.index += 1
#         return result
#
# class A1:
#     def __init__(self):
#         self.headers = A2()
# request=A1()
# def main():
#     COMP1 = "qweqweqweeee"
#     print(GetTOK())
#
# main()
