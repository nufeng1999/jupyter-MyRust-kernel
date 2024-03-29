##fnlist:CMak Mermaid
##########################
from math import exp
from queue import Queue
from threading import Thread
from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from jinja2 import Environment, PackageLoader, select_autoescape,Template
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Sequence
from shutil import copyfile
from plugins.ISpecialID import IStag,IDtag,IBtag,ITag
import pexpect
import signal
import typing 
import typing as t
import re
import signal
import subprocess
import tempfile
import os
import sys
import traceback
import os.path as path
import codecs
import time
import importlib
import importlib.util
import inspect
###############################
class Magics():
    plugins=None
    ISplugins=None
    IDplugins=None
    IBplugins=None
    kobj=None
    plugins=[ISplugins,IDplugins,IBplugins]
    def __init__(self,kobj,plugins:List,ICodePreprocs):
        self.kobj=kobj
        self.plugins=plugins
        self.ICodePreprocs=ICodePreprocs
        self.ISplugins=self.plugins[0]
        self.IDplugins=self.plugins[1]
        self.IBplugins=self.plugins[2]
        self.reset_filter()
        # self.magics = {
        #     ##%include:../src/magics_define.py
        #     }
        self.init_filter(self.magics)
    def _is_specialID(self,line):
        if line.strip().startswith('##%') or line.strip().startswith('//%'):
            return True
        return False
    def addkey2dict(self,magics:Dict,key:str):
        if not magics.__contains__(key):
            d={key:[]}
            magics.update(d)
        return magics[key]
    def get_outencode(self,magics):
        encodestr=self.get_magicsSvalue(magics,"outencode")
        if len(encodestr)<1:
            encodestr='UTF-8'
        return encodestr
    def get_magicsSvalue(self,magics:Dict,key:str):
        return self.addmagicsSkey(magics,key)
    def get_magicsBvalue(self,magics:Dict,key:str):
        return self.addmagicsBkey(magics,key)
    def get_magicsbykey(self,magics:Dict,key:str):
        return self.addkey2dict(magics,key)
    
    def addmagicsSLkey(self,magics:Dict,key:str,value=None,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_sline',func=func,value=value)
    def addmagicsSkey(self,magics:Dict,key:str,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_st',func=func)
    def addmagicsBkey(self,magics:Dict,key:str,value=None,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_bt',func=func,value=value)
    
    def addmagicskey2(self,magics:Dict,key:str,type:str,func=None,value=None):
        if not magics[type].__contains__(key):
            ##添加 key
            d={key:[]}
            if value!=None:
                d={key:value}
            magics[type].update(d)
        if not magics[type+'f'].__contains__(key):
            ##添加 key相关回调函数
            d={key:[]}
            magics[type+'f'].update(d)
        if func!=None:
            magics[type+'f'][key]+=[func]
        return magics[type][key]
    def addkey2dict(self,magics:Dict,key:str,type:str=None):
        if not magics.__contains__(key):
            d={key:[]}
            if type!=None and type=="dict":
                d={key:{}}
            magics.update(d)
        return magics[key]
    def getstartspace(self,line:str):
        pattern = re.compile(r'\S')
        spacechar=' '
        spacecount=0
        if len(line)>0 :
            m = pattern.search(line)
            if m!=None:
                spacecount=m.start(0)
            else:
                spacecount=len(line)
        if spacecount<1:return ''
        return spacechar*spacecount
    def slfn_include(self,key,magics,line):
        # self.kobj._logln("find "+key)
        li=line.find(key)
        if li<0:return ''
        filename=line[li+9:]
        # self.kobj._logln("_include filename "+filename)
        content=self.kobj.readcodefile(filename,spacecount=0)
        startspace=self.getstartspace(line)
        if len(startspace)>0:
            startspace=startspace[0]*2+startspace
        index=0
        newcontent=''
        contents=content.splitlines()
        ncontents=len(contents)
        for cline in contents:
            if index==0:
                newcontent+=cline+'\n'
                index+=1
            else:
                if index==ncontents-1:
                    newcontent+=startspace+cline
                else:
                    newcontent+=startspace+cline+'\n'
        newcontent=line[:li]+newcontent
        # qline=self.kobj.replacemany(line,'; ', ';')
        # qline=self.kobj.replacemany(qline,' ;', ';')
        # qline= qline[:len(qline)-1]
        # li=qline.strip().split()
        # if(len(li)>1):
        #     magics['_include'] = li[1].strip()
        # self.kobj._logln("newcontent---- \n"+newcontent)
        return newcontent
    def slfn_package(self,key,magics,line):
        qline=self.kobj.replacemany(line,'; ', ';')
        qline=self.kobj.replacemany(qline,' ;', ';')
        qline= qline[:len(qline)-1]
        li=qline.strip().split()
        if(len(li)>1):
            magics['package'] = li[1].strip()
        return ''
    def slfn_public(self,key,magics,line):
        qline = self.kobj.replacemany(line, 's  ', 's ')
        li = qline.strip().split()
        if(len(li) > 2 and li[1].strip().lower() == 'class'):
            magics[li[0].strip()] = li[1].strip()
            pubclass = li[2].strip()
            if pubclass.strip().endswith('{'):
                pubclass = pubclass[:len(pubclass)-1]
            magics['pubclass'] = pubclass
        return ''
    def kfn_strlable(self,key,value,magics,line):
        magics['_st'][key] = value.strip()
        return ''
    def kfn_listlable(self,key,value,magics,line):
        magics['_st'][key] +=[value.strip()]
        return ''
    def kfn_ldflags(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_cflags(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_switches(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_options(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_coptions(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_joptions(self,key,value,magics,line):
        for flag in value.split():
            magics['_st'][key] += [flag]
        return ''
    def kfn_runmode(self,key,value,magics,line):
        if len(value)>0:
            magics['_st'][key] = value[re.search(r'[^/]',value).start():]
        else:
            magics['_st'][key] ='real'
        return ''
    def kfn_replsetip(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_replchildpid(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_pidcmd(self,key,value,magics,line):
        magics['_st']['pidcmd'] = [value]
        if len(magics['_st']['pidcmd'])>0:
            findObj= value.split(",",1)
        if findObj and len(findObj)>1:
            pid=findObj[0]
            cmd=findObj[1]
            self.kobj.send_cmd(pid=pid,cmd=cmd)
        return ''
    def kfn_term(self,key,value,magics,line):
        magics['_st']['term']=[]
        for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
            magics['_st']['term'] += [argument.strip('"')]
        return ''
    def kfn_fifoname(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_fifofile(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_stdoutd(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_stdind(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_srvmode(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_srvurl(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_stoprpcsrv(self,key,value,magics,line):
        return self.kfn_listlable(key,value,magics,line)
    def kfn_sendrpcmsg(self,key,value,magics,line):
        magics['_st'][key] +=[value.strip()]
        msg=''
        rpcurl=''
        outencode='UTF-8'
        outencode=self.kobj.get_outencode(magics)
        if(outencode==None or len(outencode)<0):outencode='UTF-8'
        if len(value.strip())<1:return ''
        li=value.split(" ", 1)
        if len(li)<2:return ''
        rpcurl=li[0]
        msg=li[1]
        self.kobj.send_cmd(magics,rpcurl,msg)
        return ''
    def kfn_srmafterexec(self,key,value,magics,line):
        return self.kfn_listlable(key,value,magics,line)
    def kfn_smafterexec(self,key,value,magics,line):
        return self.kfn_listlable(key,value,magics,line)
    def kfn_prerunlist(self,key,value,magics,line):
        try:
            if len(value)>0:
                for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
                    magics['_st'][key] += [argument.strip('"')]
        except Exception as e:
            self.kobj._log(str(e),2)
        return ''
    def kfn_prerunforlist(self,key,value,magics,line):
        try:
            ##获取 list 值
            list=self.kobj.get_magicsSvalue(magics,'prerunlist')
            if len(list)<1:return ''
            newval=value
            magics['_st'][key]=[]
            for li in list:
                newval=value.replace('$runlist',li.strip()) 
                if len(newval)>0:
                    magics['_st'][key] += [newval[re.search(r'[^/]',newval).start():]]
        except Exception as e:
            self.kobj._logln(str(e),2)
        return ''       
    def kfn_runlist(self,key,value,magics,line):
        try:
            if len(value)>0:
                for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
                    magics['_st'][key] += [argument.strip('"')]
        except Exception as e:
            self.kobj._log(str(e),2)
        return ''
    def kfn_runforlist(self,key,value,magics,line):
        try:
            ##获取 list 值
            list=self.kobj.get_magicsSvalue(magics,'runlist')
            if len(list)<1:return ''
            newval=value
            magics['_st'][key]=[]
            for li in list:
                newval=value.replace('$runlist',li.strip()) 
                if len(newval)>0:
                    magics['_st'][key] += [newval[re.search(r'[^/]',newval).start():]]
        except Exception as e:
            self.kobj._logln(str(e),2)
        return ''
    def kfn_preassfile(self,key,value,magics,line):
        return self.kfn_listlable(key,value,magics,line)
    def kfn_assfile(self,key,value,magics,line):
        return self.kfn_listlable(key,value,magics,line)
    def kfn_fileencode(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_outencode(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_outputtype(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_cwd(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_log(self,key,value,magics,line):
        magics['_st']['log'] = value.strip()
        self.kobj.set_loglevel(value.strip())
        return ''
    def kfn_loadurl(self,key,value,magics,line):
        url=value
        if(len(url)>0):
            line=self.kobj.loadurl(url)
            return line
        return ''
    def kfn_runprg(self,key,value,magics,line):
        return self.kfn_strlable(key,value,magics,line)
    def kfn_runprgargs(self,key,value,magics,line):
        for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
            magics['_st']['runprgargs'] += [argument.strip('"')]
        return ''
    def kfn_args(self,key,value,magics,line):
        for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
            magics['_st']['args'] += [argument.strip('"')]
        return ''
    def init_filter(self,magics):
        self.addmagicsSLkey(magics,'_include:','1',self.slfn_include)
        self.addmagicsSLkey(magics,'package','0',self.slfn_package)
        self.addmagicsSLkey(magics,'public','0',self.slfn_public)
        self.addmagicsSkey(magics,'ldflags',self.kfn_ldflags)
        self.addmagicsSkey(magics,'cflags',self.kfn_cflags)
        self.addmagicsSkey(magics,'switches',self.kfn_switches)
        self.addmagicsSkey(magics,'options',self.kfn_options)
        self.addmagicsSkey(magics,'coptions',self.kfn_coptions)
        self.addmagicsSkey(magics,'joptions',self.kfn_joptions)
        self.addmagicsSkey(magics,'runmode',self.kfn_runmode)
        self.addmagicsSkey(magics,'replsetip',self.kfn_replsetip)
        self.addmagicsSkey(magics,'replchildpid',self.kfn_replchildpid)
        self.addmagicsSkey(magics,'pidcmd',self.kfn_pidcmd)
        self.addmagicsSkey(magics,'term',self.kfn_term)
        self.addmagicsSkey(magics,'srvmode',self.kfn_srvmode)
        self.addmagicsSkey(magics,'srvurl' ,self.kfn_srvurl)
        self.addmagicsSkey(magics,'fifoname',self.kfn_fifoname)
        self.addmagicsSkey(magics,'fifofile',self.kfn_fifofile)
        self.addmagicsSkey(magics,'stdout->',self.kfn_stdoutd)
        self.addmagicsSkey(magics,'stdin<-',self.kfn_stdind)
        self.addmagicsSkey(magics,'stoprpcsrv',self.kfn_stoprpcsrv)
        self.addmagicsSkey(magics,'sendrpcmsg',self.kfn_sendrpcmsg)
        self.addmagicsSkey(magics,'srmafterexec',self.kfn_srmafterexec)
        self.addmagicsSkey(magics,'smafterexec',self.kfn_smafterexec)
        self.addmagicsSkey(magics,'prerunforlist',self.kfn_prerunforlist)
        self.addmagicsSkey(magics,'prerunlist',self.kfn_prerunlist)
        self.addmagicsSkey(magics,'runforlist',self.kfn_runforlist)
        self.addmagicsSkey(magics,'runlist',self.kfn_runlist)
        self.addmagicsSkey(magics,'preassfile',self.kfn_preassfile)
        self.addmagicsSkey(magics,'assfile',self.kfn_assfile)
        self.addmagicsSkey(magics,'outputtype',self.kfn_outputtype)
        self.addmagicsSkey(magics,'fileencode',self.kfn_fileencode)
        self.addmagicsSkey(magics,'outencode',self.kfn_outencode)
        self.addmagicsSkey(magics,'cwd',self.kfn_cwd)
        self.addmagicsSkey(magics,'log',self.kfn_log)
        self.addmagicsSkey(magics,'loadurl',self.kfn_loadurl)
        self.addmagicsSkey(magics,'runprg',self.kfn_runprg)
        self.addmagicsSkey(magics,'runprgargs',self.kfn_runprgargs)
        self.addmagicsSkey(magics,'args',self.kfn_args)
    def reset_filter(self):
        self.magics = {
              ##
                '_mcmd':{
                    'cmd':[
                        'if',
                        'ifdef',
                        'ifndef',
                        'elif',
                        'else',
                        'endif',
                        'defined'
                    ],
                },
                '_sline':{
                    'package':'0',
                    'public':'0',
                    '_include:':'1'
                },
                '_slinef':{
                    'package':[],
                    'public':[],
                    '_include:':[]
                },
                '_bt':{
                    'cleartest':'',
                    'repllistpid':'',
                    'runinterm':'',
                    'replcmdmode':'',
                    'replprompt':'',
                    'rpcsrvfollowcode':'',
                    'stdout2fifo':'',
                    'fifo2stdin':'',
                    'discleannotes':''
                },
                '_st':{
                    'ldflags':[],
                    'cflags':[],
                    'switches':[],
                    'options':[],
                    'coptions':[],
                    'joptions':[],
                    'runmode':[],
                    'replsetip':[],
                    'replchildpid':"0",
                    'srvmode':"",
                    'srvurl':"",
                    'fifoname':"",
                    'fifofile':"",
                    'stdout->':'',
                    'stdin<-':'',
                    'stoprpcsrv':[],
                    'sendrpcmsg':[],
                    'srmafterexec':[],
                    'smafterexec':[],
                    'prerunforlist':'',
                    'prerunlist':[],
                    'runforlist':'',
                    'runlist':[],
                    'preassfile':[],
                    'assfile':[],
                    'pidcmd':[],
                    'term':[],
                    'fileencode':'UTF-8',
                    'outencode':'UTF-8',
                    'outputtype':'text/plain',
                    'cwd':'',
                    'log':[],
                    'loadurl':[],
                    'runprg':[],
                    'runprgargs':[],
                    'args':[]
                },
                '_dt':{},
                '_btf':{
                    'cleartest':[],
                    'repllistpid':[self.kobj.repl_listpid],
                    'runinterm':[],
                    'replcmdmode':[],
                    'replprompt':[],
                    'rpcsrvfollowcode':[],
                    'stdout2fifo':[],
                    'fifo2stdin':[],
                    'discleannotes':[]
                },
                '_stf':{
                    'ldflags':[],
                    'cflags':[],
                    'switches':[],
                    'options':[],
                    'coptions':[],
                    'joptions':[],
                    'runmode':[],
                    'replsetip':[],
                    'replchildpid':[],
                    'srvmode':[],
                    'srvurl':[],
                    'fifoname':[],
                    'fifofile':[],
                    'stdout->':[],
                    'stdin<-':[],
                    'stoprpcsrv':[],
                    'sendrpcmsg':[],
                    'srmafterexec':[],
                    'smafterexec':[],
                    'prerunforlist':[],
                    'prerunlist':[],
                    'runforlist':[],
                    'runlist':[],
                    'preassfile':[],
                    'assfile':[],
                    'pidcmd':[],
                    'term':[],
                    'fileencode':[],
                    'outencode':[],
                    'outputtype':[],
                    'cwd':[],
                    'log':[],
                    'loadurl':[],
                    'runprg':[],
                    'runprgargs':[],
                    'args':[]
                },
                '_dtf':{},
                'status':'',
                'codefilename':'',
                'classname':'',
                'dlrun': [],
                'package': '',
                'main': '',
                'pubclass': '',
                'pid': []
            }
    def call_slproc(self,magics,line)->Tuple[bool,str]:
        type='_sline'
        if len(magics[type])<1:return False,line
        newline=line
        ismatch=False
        try:
            for key,value in magics[type].items():
                if (len(value)>0 and value.strip()=='0' 
                    and (line.strip().startswith(key))
                    and len(magics[type+'f'][key])>0):
                    ismatch=True
                    for kfunc in magics[type+'f'][key]:
                        newline=kfunc(key,magics,newline)
                elif (len(value)>0 and value.strip()=='1' 
                    and (key in line.strip())
                    and len(magics[type+'f'][key])>0):
                    ismatch=True
                    for kfunc in magics[type+'f'][key]:
                        newline=kfunc(key,magics,newline)
                elif (len(value)>0 and value.strip()=='2' 
                    and (line.strip().endswith(key))
                    and len(magics[type+'f'][key])>0):
                    ismatch=True
                    for kfunc in magics[type+'f'][key]:
                        newline=kfunc(key,magics,newline)
                if ismatch:
                    return ismatch,newline
        except Exception as e:
            self.kobj._logln("call_slproc "+str(e),3)
        finally:pass
        return ismatch,newline
    def call_btproc(self,magics,line)->bool:
        type='_bt'
        if len(magics[type])<1:return False
        try:
            key= line.strip()[3:]
            if magics[type].__contains__(key):
                magics[type][key]='true'
                if len(magics[type+'f'][key])>0:
                    ##处理关键字相关的函数
                    for kfunc in magics[type+'f'][key]:
                        kfunc(line)
                return True
        except Exception as e:
            self.kobj._logln('call_btproc '+str(e),3)
        finally:pass
        return False
    def call_stproc(self,magics,line,key,value)->str:
        type='_st'
        if len(magics[type])<1:return line
        newline=line
        try:
            if magics[type].__contains__(key):
                if len(magics[type+'f'][key])>0:
                    for kfunc in magics[type+'f'][key]:
                        # self.kobj._logln("call--------"+key)
                        newline=kfunc(key,value,magics,newline)
                return newline
        except Exception as e:
            self.kobj._logln("call_stproc "+str(e),3)
        finally:pass
        return newline
    def raise_ICodescan(self,magics,code)->Tuple[bool,str]:
        bcancel_exec=False
        bretcancel_exec=False
        newcode=code
        # for pluginlist in self.plugins:
        for pkey,pvalue in self.ICodePreprocs.items():
            for pobj in pvalue:
                try:
                    bretcancel_exec,newcode=pobj.on_Codescanning(pobj,magics,newcode)
                    bcancel_exec=bretcancel_exec & bcancel_exec
                    if bcancel_exec:
                        return bcancel_exec,newcode
                except Exception as e:
                    self.kobj._logln(pobj.getName(pobj)+"---"+str(e))
                finally:pass
        return bcancel_exec,newcode
    def filter(self, code):
        actualCode = ''
        newactualCode = ''
        self.reset_filter()
        self.init_filter(self.magics)
        magics =self.magics
        for line in code.splitlines():
            orgline=line
            if line==None or line.strip()=='': 
                actualCode += line + '\n'
                continue
            ismatch,retstr=self.call_slproc(magics,line)
            if ismatch:
                if len(retstr)>0:
                    actualCode += retstr + '\n'
                else:
                    actualCode += line + '\n'
                continue
            if self._is_specialID(line):
                if self.call_btproc(magics,line):continue
                for pkey,pvalue in self.IBplugins.items():
                    for pobj in pvalue:
                        newline=''
                        try:
                            lin=pobj.getIDBptag(pobj)
                            if line.lower().strip()[3:] in lin:
                                newline=pobj.on_IBpCodescanning(pobj,magics,line)
                                if newline=='':continue
                        except Exception as e:
                            self._logln(str(e))
                        finally:pass
                ##
                findObj= re.search( r':(.*)',line)
                if not findObj or len(findObj.group(0))<2:
                    continue
                key, value = line.strip()[3:].split(":", 1)
                key = key.strip().lower()
                newline=self.call_stproc(magics,line,key,value)
                if newline!=line and len(newline)>0:
                    actualCode += newline + '\n'
                    continue
                for pkey,pvalue in self.ISplugins.items():
                    for pobj in pvalue:
                        newline=''
                        try:
                            li=pobj.getIDSptag(pobj)
                            if key.lower() in li:
                                newline=pobj.on_ISpCodescanning(pobj,li[0],value,magics,line)
                                if newline=='':continue
                        except Exception as e:
                            pass
                        finally:pass
                        if newline!=None and newline!='':
                            actualCode += newline + '\n'
            else:
                actualCode += line + '\n'
        newactualCode=actualCode
        bcancel_exec,newcode=self.raise_ICodescan(magics,newactualCode)
        if not bcancel_exec:
            newactualCode=newcode
        if len(self.get_magicsBvalue(magics,'cleartest'))>0 :
            actualCode=self.kobj.cleantestcodeA(actualCode)
        else:
            actualCode=self.kobj.cleantestcodeB(actualCode)
        newactualCode=''
        for line in actualCode.splitlines():
            try:
                if len(self.get_magicsBvalue(magics,'discleannotes'))>0 :continue
                if line=='':continue
                line=self.kobj.cleandqm(line)
                if line=='':continue
                line=self.kobj.cleansqm(line)
                if line=='':continue
                line=self.kobj.cleannotes(line)
                if line=='':continue
                line=self.kobj.callIDplugin(magics,line)
                if line=='':continue
                else:
                    newactualCode += line + '\n'
            except Exception as e:
                self.kobj._log(str(e),3)
        return magics, newactualCode
