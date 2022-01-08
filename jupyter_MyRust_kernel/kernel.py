###%file:rust_kernel.py
#
#   MyRust Jupyter Kernel
#   generated by MyPython
#
from math import exp
from queue import Queue
from threading import Thread
from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from jinja2 import Environment, PackageLoader, select_autoescape,Template
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Sequence
from shutil import copyfile,move
from urllib.request import urlopen
import socket
import copy
import mmap
import contextlib
import atexit
import platform
import atexit
import base64
import urllib.request
import urllib.parse
import pexpect
import signal
import typing 
import typing as t
import re
import signal
import subprocess
import tempfile
import os
import stat
import sys
import traceback
import os.path as path
import codecs
import time
import importlib
import importlib.util
import inspect
from . import ipynbfile
from plugins.ISpecialID import IStag,IDtag,IBtag,ITag,ICodePreproc
from plugins._filter2_magics import Magics
try:
    zerorpc=__import__("zerorpc")
    # import zerorpc
except:
    pass
fcntl = None
msvcrt = None
bLinux = True
if platform.system() != 'Windows':
    fcntl = __import__("fcntl")
    bLinux = True
else:
    msvcrt = __import__('msvcrt')
    bLinux = False
from .MyKernel import MyKernel
class RustKernel(MyKernel):
    kernel_info={
        'info':'[MyRust Kernel]',
        'extension':'.rs',
        'execsuffix':'.exe',
        'needmain':'true',
        'compiler':{
            'cmd':'rustc',
            'outfileflag':'-o',
            'clargs':[],
            'crargs':[],
        },
        'interpreter':{
            'cmd':'',
            'clargs':'',
            'crargs':'',
        },
    }
    implementation = 'jupyter_MyRust_kernel'
    implementation_version = '1.0'
    language = 'Rust'
    language_version = ''
    language_info = {'name': 'text/rust',
                     'mimetype': 'text/rust',
                     'file_extension': kernel_info['extension']}
    runfiletype='script'
    banner = "Rust kernel.\n" \
             "Uses Rust, compiles in rust, and creates source code files and executables in temporary folder.\n"
    main_head = "\n\nint main(List<String> arguments){\n"
    main_foot = "\nreturn 0;\n}"
    
    def __init__(self, *args, **kwargs):
        super(RustKernel, self).__init__(*args, **kwargs)
        self.runfiletype='script'
        self.kernelinfo="[MyRustKernel{0}]".format(time.strftime("%H%M%S", time.localtime()))
    def getCompout_filename(self,cflags,outfileflag,defoutfile):
        outfile=''
        binary_filename=defoutfile
        index=0
        for s in cflags:
            if s.startswith(outfileflag):
                if(len(s)>len(outfileflag)):
                    outfile=s[len(outfileflag):]
                    del cflags[index]
                else:
                    outfile=cflags[cflags.index(outfileflag)+1]
                    if outfile.startswith('-'):
                        outfile=binary_filename
                    del cflags[cflags.index(outfileflag)+1]
                    del cflags[cflags.index(outfileflag)]
            binary_filename=outfile
            index+=1
        return binary_filename
    def compile_with_sc(self, source_filename, binary_filename, cflags=None, ldflags=None,env=None,magics=None):
        outfile=binary_filename
        orig_cflags=cflags
        orig_ldflags=ldflags
        ccmd=[]
        clargs=[]
        crargs=[]
        outfileflag=[]
        oft=''
        if len(self.kernel_info['compiler']['outfileflag'])>0:
            oft=self.kernel_info['compiler']['outfileflag']
            outfileflag=[oft]
            binary_filename=self.getCompout_filename(cflags,oft,outfile)
        args=[]
        if magics!=None and len(self.mymagics.addkey2dict(magics,'ccompiler'))>0:
            args = magics['ccompiler'] + orig_cflags +[source_filename] + orig_ldflags
        else:
            if len(self.kernel_info['compiler']['cmd'])>0:
                ccmd+=[self.kernel_info['compiler']['cmd']]
            if len(self.kernel_info['compiler']['clargs'])>0:
                clargs+=self.kernel_info['compiler']['clargs']
            if len(self.kernel_info['compiler']['crargs'])>0:
                crargs+=self.kernel_info['compiler']['crargs']
            args = ccmd+cflags+[source_filename] +clargs+outfileflag+ [binary_filename]+crargs+ ldflags
        # self._log(''.join((' '+ str(s) for s in args))+"\n")
        return self.mymagics.create_jupyter_subprocess(args,env=env,magics=magics),binary_filename,args
    def _exec_sc_(self,source_filename,magics):
        self.mymagics._logln('Generating executable file')
        with self.mymagics.new_temp_file(suffix=self.kernel_info['execsuffix']) as binary_file:
            magics['status']='compiling'
            p,outfile,tsccmd = self.compile_with_sc(
                source_filename, 
                binary_file.name,
                self.mymagics.get_magicsSvalue(magics,'cflags'),
                self.mymagics.get_magicsSvalue(magics,'ldflags'),
                self.mymagics.get_magicsbykey(magics,'env'),
                magics=magics)
            returncode=p.wait_end(magics)
            p.write_contents()
            magics['status']=''
            binary_file.name=os.path.join(os.path.abspath(''),outfile)
            if returncode != 0:  
                self.mymagics._logln(' '.join((str(s) for s in tsccmd))+"\n",3)
                self.mymagics._logln("compiler exited with code {}, the executable will not be executed".format(returncode),3)
                os.remove(binary_file.name)
        return p.returncode,binary_file.name
    def do_runcode(self,return_code,fil_ename,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=return_code
        fil_ename=fil_ename
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        interpreter=[]
        if len(self.kernel_info['interpreter']['cmd'])>0:
            interpreter+=[self.kernel_info['interpreter']['cmd']]
            if len(self.kernel_info['interpreter']['clargs'])>0:
                interpreter+=self.kernel_info['interpreter']['clargs']
            interpreter+=[fil_ename]
            if len(self.kernel_info['interpreter']['crargs'])>0:
                interpreter+=self.kernel_info['interpreter']['crargs']
        cmd=[fil_ename]
        if len(interpreter)>0:
            cmd=interpreter
        p = self.mymagics.create_jupyter_subprocess(cmd+ magics['_st']['args'],cwd=None,shell=False,env=self.mymagics.addkey2dict(magics,'env'),magics=magics)
        self.mymagics.g_rtsps[str(p.pid)]=p
        return_code=p.returncode
         
        if magics!=None and len(self.mymagics.addkey2dict(magics,'showpid'))>0:
            self.mymagics._write_to_stdout("The process PID:"+str(p.pid)+"\n")
        return_code=p.wait_end(magics)
        if p.returncode != 0:
            self.mymagics._log("Executable exited with code {}".format(p.returncode),2)
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
    def do_compile_code(self,return_code,fil_ename,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        binary_filename=fil_ename
        if len(self.kernel_info['compiler']['cmd'])>0:
            returncode,binary_filename=self._exec_sc_(fil_ename,magics)
            if returncode!=0:return  True,retinfo, code,fil_ename,retstr
        return bcancel_exec,retinfo,magics, code,binary_filename,retstr
    def do_create_codefile(self,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        fil_ename=''
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        retstr=''
        
        source_file=self.mymagics.create_codetemp_file(magics,code,suffix=self.kernel_info['extension'])
        fil_ename=source_file.name
        
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
    def do_preexecute(self,code, magics,silent, store_history=True,
                user_expressions=None, allow_stdin=False):
        bcancel_exec=False
        retinfo=self.mymagics.get_retinfo()
        if (len(self.mymagics.addkey2dict(magics,'noruncode'))<1 
            and len(self.kernel_info['needmain'])>0 ):
            magics, code = self.mymagics._add_main(magics, code)
        return bcancel_exec,retinfo,magics, code
