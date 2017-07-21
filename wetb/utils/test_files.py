'''
Created on 20. jul. 2017

@author: mmpe
'''
import os
import wetb
import urllib.request
from fileinput import filename
import inspect
wetb_rep_path = os.path.join(os.path.dirname(wetb.__file__), "../")                                   
default_TestFile_rep_path=os.path.join(os.path.dirname(wetb.__file__) + "/../../TestFiles/")

def get_test_file(filename):
    if not os.path.isabs(filename):
        index = [os.path.realpath(s[1]) for s in inspect.stack()].index(__file__) + 1
        tfp = os.path.dirname(inspect.stack()[index][1]) + "/test_files/"
        filename = tfp + filename
    
    if os.path.exists(filename):
        return filename
    else:
        wetb_rep_path = os.path.join(os.path.dirname(wetb.__file__), "../")
        return os.path.join(wetb_rep_path, 'TestFiles', os.path.relpath(filename, wetb_rep_path))
        



def move2test_files(filename,TestFile_rep_path=default_TestFile_rep_path):
    wetb_rep_path = os.path.join(os.path.dirname(wetb.__file__), "../")
    dst_filename = os.path.join(wetb_rep_path, 'TestFiles', os.path.relpath(filename, wetb_rep_path))
    folder = os.path.dirname(dst_filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
    os.rename(filename, dst_filename)
    
    
    
    
    