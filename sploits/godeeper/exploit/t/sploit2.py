#!/usr/bin/env python3
import sys,string,random,re,logging
import token_generator

ua = "CTF"
class A2:
    def __init__(self):
        index=0
        self.data=['User-Agent']
    def get(self,a):
        global ua
        return ua

    def __iter__(self):
        self.index = 0
        return self
    def __next__(self):
        if self.index >= len(self.data):
            raise StopIteration
        result = self.data[self.index]
        self.index += 1
        return result

class A1:
    def __init__(self):
        self.headers = A2()
request=A1()

company = sys.argv[1]
token = token_generator.GetTOK()
print(token)
