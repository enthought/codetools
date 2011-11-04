'''
Created on Nov 4, 2011

@author: sean
'''
import sys

py3 = sys.version_info.major >= 3

class Python2(object):
    @staticmethod
    def py2op(func):
        return func

def py3op(func):
    if py3:
        
        func.py2op = lambda _:func
        return func
    else:
        return Python2

class Python3(object):
    @staticmethod
    def py3op(func):
        return func

def py2op(func):
    if not py3:
        func.py3op = lambda _:func
        return func
    else:
        return Python3
