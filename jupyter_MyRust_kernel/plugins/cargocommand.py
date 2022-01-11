from typing import Dict, Tuple, Sequence,List
from plugins.ISpecialID import IStag,IDtag,IBtag,ITag
import os
import re
class MyCargocmd(IStag):
    kobj=None
    def getName(self) -> str:
        # self.kobj._write_to_stdout("setKernelobj setKernelobj setKernelobj\n")
        
        return 'MyCargocmd'
    def getAuthor(self) -> str:
        return 'Author'
    def getIntroduction(self) -> str:
        return 'MyCargocmd'
    def getPriority(self)->int:
        return 0
    def getExcludeID(self)->List[str]:
        return []
    def getIDSptag(self) -> List[str]:
        return ['cargo']
    def setKernelobj(self,obj):
        self.kobj=obj
        # self.kobj._write_to_stdout("setKernelobj setKernelobj setKernelobj\n")
        return
    def on_shutdown(self, restart):
        return
    def on_ISpCodescanning(self,key, value,magics,line) -> str:
        # self.kobj._write_to_stdout(line+" on_ISpCodescanning\n")
        self.kobj.addkey2dict(magics,'cargo')
        return self.commandhander(self,key, value,magics,line)
    ##在代码预处理前扫描代码时调用    
    def on_Codescanning(self,magics,code)->Tuple[bool,str]:
        pass
        return False,code
    ##生成文件时调用
    def on_before_buildfile(self,code,magics)->Tuple[bool,str]:
        return False,''
    def on_after_buildfile(self,returncode,srcfile,magics)->bool:
        return False
    def on_before_compile(self,code,magics)->Tuple[bool,str]:
        return False,''
    def on_after_compile(self,returncode,binfile,magics)->bool:
        return False
    def on_before_exec(self,code,magics)->Tuple[bool,str]:
        return False,''
    def on_after_exec(self,returncode,srcfile,magics)->bool:
        return False
    def on_after_completion(self,returncode,execfile,magics)->bool:
        return False
    def commandhander(self,key, value,magics,line):
        cmds=[]
        for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value.strip()):
            cmds += [argument.strip('"')]
        magics['cargo']=cmds
        if len(magics['cargo'])>0:
            self.do_cargo_command(self,magics['cargo'],magics=magics)
        return ''
    def do_cargo_command(self,commands=None,cwd=None,magics=None):
        try:
            # self.kobj._logln("do_npm_command......")
            npmcmd=['cargo']
            if(self.kobj.sys=="Windows"):
                npmcmd=['cmd','/c','cargo']
            p = self.kobj.create_jupyter_subprocess(npmcmd+commands,cwd=cwd,shell=False,magics=magics)
            self.kobj.g_rtsps[str(p.pid)]=p
            if magics!=None and len(self.kobj.addkey2dict(magics,'showpid'))>0:
                self.kobj._logln("The process PID:"+str(p.pid))
            returncode=p.wait_end(magics)
            del self.kobj.g_rtsps[str(p.pid)]
            if returncode != 0:
                self.kobj._logln("Executable exited with code {}".format(returncode),3)
            else:
                self.kobj._logln("Info:cargo command success.")
        except Exception as e:
            self.kobj._logln("do_cargo_command err:"+str(e))
            raise
        return
    
