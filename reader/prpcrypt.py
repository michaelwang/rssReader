#!/usr/bin/env python
# -*- coding:utf-8 -*- 

'''
from Crypto.Cipher import DES
from Crypto import Random


class prpcrypt():
    def __init__(self,key):
        self.key = key
        self.mode = DES.MODE_ECB

    def encrypt(self,text):
        iv = Random.get_random_bytes(8)
        des = DES.new(self.key, DES.MODE_CFB, iv)
        return des.encrypt(text)
         
    def decrypt(self,text):
        iv = Random.get_random_bytes(8)
        des = DES.new(self.key, DES.MODE_CFB, iv)
        return des.decrypt(text)


if __name__ == '__main__':
     pc = prpcrypt('ad34567o') 
#     e = pc.encrypt(sys.argv[1]) 
     e = pc.encrypt('abcdefgh') 
     d = pc.decrypt(e)
     print ":",e
     print ":",d
'''
