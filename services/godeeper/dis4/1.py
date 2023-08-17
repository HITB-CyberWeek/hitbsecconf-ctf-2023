def GetTOK():
    # TOK1 = Hash1(COMP1) + Hash2(secret+Hash1(COMP1))
    # __builtins__.__dict__['exec']("import inspect; aaa=inspect.currentframe().f_back.f_locals",)
    tmp1=""
    for c in [224, 228, 249, 230, 251, 253, 169, 224, 231, 250, 249, 236, 234, 253]:
        tmp1 += chr(c ^ 137)
    print(tmp1)

    exec("import inspect",globals())
    myCOMP1 = inspect.currentframe().f_back.f_locals["COMP1"]

    secret = "FeaV9fi7Ahs9Igh6"
    # print(secret)
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

def main():
    COMP1 = "qweqweqweeee"
    print(GetTOK())

main()

# a="import inspect";   [224, 228, 249, 230, 251, 253, 169, 224, 231, 250, 249, 236, 234, 253]
# ''.join(chr(ord(x) ^ 137) for x in "import inspect")
# ''.join(chr(x ^ 137) for x in [202, 198, 196, 217, 184])
#

# for i in range(len(dir(__builtins__))): print(i,dir(__builtins__)[i])
#
# def BBB(a,s,b):
#     a=10
#     a=a-5
#     a=a*5
#     print(a)
#
#     a = 1
#     c = 3
#     for i in range(10):
#         print(1)
#         a+=i
#
#     while b < 100:
#         print(2)
#         b+=1
#         a+=b
#     if a>=0 and c==3:
#         print(3)
#         b=a
#         return
#     else:
#         print(4)
#         b=-a
#     quit()
#     return
#
# BBB(1,2,3)#
# Constants:
#    0: None
#    1: (224, 228, 249, 230, 251, 253, 169, 224, 231, 250, 249, 236, 234, 253)
#    2: 137
#    3: ''
# Names:
#    0: append
#    1: chr
#    2: join
#    3: print
# Varnames:
#	b, x, aa
# Local variables:
#    0: b
#    1: x
#    2: aa
#   9:
#
#             BUILD_LIST           0
#             STORE_FAST           0 (b)
#             LOAD_CONST           1 ((224, 228, 249, 230, 251, 253, 169, 224, 231, 250, 249, 236, 234, 253))
#             GET_ITER
# L8:
#             FOR_ITER             L32 (to 32)
#             STORE_FAST           1 (x)
#
#  11:
#             LOAD_FAST            0 (b)
#             LOAD_METHOD          0 (append)
#             LOAD_GLOBAL          1 (chr)
#             LOAD_FAST            1 (x)
#             LOAD_CONST           2 (137)
#             BINARY_XOR
#             CALL_FUNCTION        1
#             CALL_METHOD          1
#             POP_TOP
#             JUMP_ABSOLUTE        L8 (to 8)
#
# L32:
#   12:
#             LOAD_CONST           3 ('')
#             LOAD_METHOD          2 (join)
#             LOAD_FAST            0 (b)
#             CALL_METHOD          1
#             STORE_FAST           2 (aa)
