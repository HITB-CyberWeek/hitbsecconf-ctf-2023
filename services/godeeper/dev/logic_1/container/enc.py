key=[]
key.append(13)
key.append(89)
key.append(37)
key.append(34)
key.append(22)
text = "'company' in res1.f_back.f_locals"
enc = []
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)

text = "res1.f_back.f_locals['company']"
enc = []
key=[]
key.append(34)
key.append(21)
key.append(45)
key.append(23)
key.append(54)
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)
text = "'request' in res1.f_back.f_globals"
enc = []
key=[]
key.append(54)
key.append(23)
key.append(45)
key.append(32)
key.append(76)
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)

text = "res1.f_back.f_globals['request']"
enc = []
key=[]
key.append(54)
key.append(23)
key.append(45)
key.append(32)
key.append(76)
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)


text = "'User-Agent' in res3.headers"
enc = []
key=[]
key.append(24)
key.append(53)
key.append(75)
key.append(26)
key.append(78)
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)


text = "res3.headers.get('User-Agent')"
enc = []
key=[]
key.append(24)
key.append(53)
key.append(75)
key.append(26)
key.append(78)
for i in range(len(text)):
    char = text[i]
    key_char = key[i % len(key)]
    enc.append(ord(char) ^ key_char)
print(enc)
