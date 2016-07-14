#http://www.youtube.com/watch?v=F_Xu0t8I3lw


import re, os, sys, pdb

try:type(BaseException) #2.6 and later has this name
except: #2.4 and older
  class BaseException(object):pass
class gen_exception(BaseException):
  def __init__(self, info=""):
    self.info = info
  def __str__(self):
    print self.info
try:
  import _winreg as wr #if windows registry
except:
  wr = None #if windows is _winreg module

def maya_path():
  global wr
  if wr:
    return maya_path_windows()
  else:
    return maya_path_nix()  

def maya_path_nix():
  """TODO:add real code to find maya at nix systems"""
  return "error_cant_find_maya"

def maya_path_windows():
  """find maya install path in windows registry"""
  #WARNING:return path to latest installed 
  exp = re.compile("^([123456789]\d*)(\.\d*)*$")
  try:
    key = wr.OpenKey(wr.HKEY_LOCAL_MACHINE,r"SOFTWARE\Autodesk\Maya")
  except:
    return "error_cant_find_maya"
  index = 0
  enums = []
  MAYA_INSTALL_LOCATIONS=[]
  try:
    while(1):
      enums.append(wr.EnumKey(key,index))
      index +=1
  except:
    pass
  possible=[]
  for sub in enums:
    if exp.match(sub):
      possible.append(
        [sub,r'SOFTWARE\Autodesk\Maya'+'\\'+sub+r'\Setup\InstallPath']
      )
  for i in possible:
    try:
      i[0]=float(i[0])
      key = wr.OpenKey(wr.HKEY_LOCAL_MACHINE,i[1])
      val = wr.QueryValueEx(key,"MAYA_INSTALL_LOCATION")[0]
      i.append( os.path.normpath( val ) )
    except:
      i.append( None )
      pass
  possible.sort()
  possible.reverse()
  for i in possible:
    if i[2]:
      if os.path.exists(i[2]):
        return i[2]
  return "error_cant_find_maya" #path to latest installed maya 

PYTHON_INSTALL_PATH=os.path.abspath(os.path.join(os.path.split(
   os.__file__)[0],".."))
if not 'PYTHON_INCLUDE' in os.environ.keys():
    os.environ["PYTHON_INCLUDE"] = os.path.join(
       PYTHON_INSTALL_PATH,"include").replace('\\','/')
if not 'PYTHON_LIB' in os.environ.keys():
    os.environ["PYTHON_LIB"    ] = os.path.join(
       PYTHON_INSTALL_PATH,"libs").replace('\\','/')
if not 'QT_SRC_DIR' in os.environ.keys():
    os.environ["QT_SRC_DIR"    ] = os.path.abspath(os.path.join(
       os.environ["QTDIR"],"src")).replace('\\','/')
if not 'MAYA_INSTALL_LOCATION' in os.environ.keys():
    os.environ["MAYA_INSTALL_LOCATION"] = maya_path()
os.environ["MAYA_LOCATION"] = os.environ["MAYA_INSTALL_LOCATION"]

     # IF ARGUMENT PRESENT, WRITE IN STDOUT ENVIRONMENT VARIABLE'S VALUE OR NONE, AND EXIT
     #
if len(sys.argv)>1:
  try:
    key=sys.argv[1]
    if "QMAKESPEC_NAME"==key:
        out=os.environ["QMAKESPEC"]
        sys.stdout.write(out.replace('+','p'))
    else:
        out=os.environ[key]
        sys.stdout.write(out)
  except:
    sys.exit()
  sys.exit()

     # IF NO ARGUMENTS, GENERATE IN TEMPORARY FOLDER MAKE FILE, FOR ALL PROJECT'S PARTS
     #
import shutil, re
from distutils.dir_util import mkpath
from popen2 import popen3

     # SETUP ENVIRONMENT VARIABLES.
     #
arg0 = os.path.abspath(sys.argv[0])            # full path to started file - here must be proj created
cwd0 = os.path.abspath(os.getcwd())            # from where started this script, restore on exit
work = arg0[:arg0.rfind(os.sep)]               # ./                 [dir] | startup working folder
                                               # ./bin              [dir] | executables and dlls output directory
                                               # ./sdk/include      [dir] | additional include path
                                               # ./sdk/lib          [dir] | library path
                                               # ./src              [dir] | c sources path
                                               # ./tmp              [dir] | temporary directory 
                                               # ./gen.%QMAKESPECS% [dir] | generated projects directory 
temp = os.path.join( work, "tmp" )             # temporary directory
sdir = os.path.join( work, "src" )             # sources dir
if not os.path.exists(sdir): raise "Can't find sources '%s'"%sdir
ssrc = os.path.join( work, "src", "script" )   # path to scripts source
path = os.path.join( temp, "script" )          #
path = os.path.normpath(path)                  #

comment_exp = re.compile("^(.*)#.*$")
sources_exp = re.compile("^\s*SUBDIRS\s*\+=\s*(.*)")
def scan_src_pro(path):
  res=list()
  buf=file(os.path.join(path,"src.pro"),"r")
  buf=buf.readlines()
  for i in buf:
    m=comment_exp.match(i)
    if m:j=comment_exp.match(i).groups()[0]
    else:j=i
    m=sources_exp.match(j)
    if m:
      lst = m.groups()[0].split()
      for l in lst:
        res.append(l)
  return res

proj = list()
     # COLLECT ALL *.pro FILES IN SOURCE FOLDER
     #
def collect_pro(path,root=None):
  global proj
  names = []
  if root:
    names.append("src.pro")
    selected = scan_src_pro(path)
    possible = os.listdir(path)
    for i in selected:
     if i in possible:names.append(i)
  else:
    names = os.listdir(path)
  #complete check names in source folder
  for name in names:
    fnam = os.path.join(path,name)
    if os.path.isdir(fnam):
      collect_pro(fnam) 
    if os.path.isfile(fnam):
      if is_pro.match(name):
        proj.append(fnam)

     # REGULAR EXPRESSIONS FOR EXTRACT VARIABLES VALUES
     #
is_template   = re.compile(r"^Project MESSAGE:\s*?TEMPLATE\s*?=(.*)")
is_target_ext = re.compile(r"^Project MESSAGE:\s*?TARGET_EXT\s*?=(.*)")
is_pro        = re.compile(r"^(\S.*).pro$")

     # GENERATE MAKE-FILE FROM .pro IN SOURCE FOLDER, TO TEMPORARY FOLDER
     #
pro_dict = {}
def generate_make(path):
  global temp, work, sdir, pro_dict
  full=path
  path,name=os.path.split(path)
  print "<make>[%s]"%full
  os.chdir(path)                                                # set current working directory
  outd = temp+path[len(sdir):]                                  # extract output folder
  outf = os.path.join(outd,"Makefile")                          # create output file name
  mkpath(outd)                                                  # create output folder
  buff = file(full,"r").read()                                  # read project file
  os.rename( full, full+".bak" )                                # rename project file to ".bak" 
  extf = file(full,"w")
  print >> extf, buff                                           #
  print >> extf, """message('TEMPLATE    ='$$TEMPLATE    )"""
  print >> extf, """message('DEFINES     ='$$DEFINES     )"""
  print >> extf, """message('INCLUDEPATH ='$$INCLUDEPATH )"""
  print >> extf, """message('LIBS        ='$$LIBS        )"""
  extf.close()                                                  # close changed 'pro' file
  o,i,e = popen3("qmake %s -o %s"%(full,outf))                  # use qmake, to generate Makefile
  eout  = e.read()                                              # read qmake messages print eout
  TEMPLATE   = None                                             #
  TARGET_EXT = None                                             #
  for line in eout.split("\n"):                                 # from each line in messages, extract known variables:
    if is_template.match(line):
      TEMPLATE=is_template.match(line).groups()[0]
      continue
    if is_target_ext.match(line):
      TARGET_EXT=is_target_ext.match(line).groups()[0]
      continue
  #print "+"*80
  print eout
  #print "-"*80
  pro_dict[full] = {                                            # store extracted variable names and values:
    "TEMPLATE"   :TEMPLATE,                                     #
    "TARGET_EXT" :TARGET_EXT,                                   #
  }                                                             #
  #print "      [%s]="%full, pro_dict[full]
  for i in pro_dict[full].keys():
    if pro_dict[full][i]=='':continue;
    print "      %s="%i, pro_dict[full][i]
  file(full,"w")
  os.remove(os.path.normpath(full))                             # remove temporary file
  os.rename( full+".bak", full )                                # rename project file to ".bak" 

     # GENERATE VISUAL STUDIO PROJECT FILES FROM .pro IN SOURCE FOLDER, TO $$QMAKECPECS FOLDER
     #
msvc_project_files=list()
def generate_msvc_vcproj(path):
  print "<msvc><pro> '%s'"%path
  global temp, work, sdir, pro_dict
  full=path
  path,name=os.path.split(path)
  proj=is_pro.match(name).groups()[0]+'.vcproj'
  os.chdir(path)                                                # set current working directory
  gend = 'gen.'+os.environ["QMAKESPEC"]                         # output folder name
  outd = os.path.join(work,gend+path[len(sdir):])               # extract output folder
  outf = os.path.join(outd,proj)                                # create output file name
  outp = os.path.join(outd,name)
  #print "  * here = '%s'"%os.getcwd()
  #print "  * work = '%s'"%str((work,gend,path[len(sdir):]))
  #print "  * outd = '%s'"%outd
  #print "  * outf = '%s'"%outf
  msvc_project_files.append(outf)
  #print "  * qmsp = '%s'"%os.environ["QMAKESPEC"]
  mkpath(outd)                                                  # create output folder
  file(outp,"w")                                                # create empty project file
  if pro_dict[full]["TEMPLATE"]=='app':
    o,i,e = popen3("qmake %s -t vcapp -o %s"%(full,outf))       # use qmake, to generate application vcproj
  elif pro_dict[full]["TEMPLATE"]=='lib':
    o,i,e = popen3("qmake %s -t vclib -o %s"%(full,outf))       # use qmake, to generate library vcproj
  else:
    raise gen_exception("unsupported TEMPLATE='%s'"%str(
         pro_dict[full]["TEMPLATE"]))

def generate_msvc_solution(path):
  print "<msvc><sln> '%s'"%path
  global temp, work, sdir, pro_dict
  full=path
  path,name=os.path.split(path)
  proj=is_pro.match(name).groups()[0]+'.sln'
  gend = 'gen.'+os.environ["QMAKESPEC"]                         # output folder name
  outd = os.path.join(work,gend+path[len(sdir):])               # extract output folder
  #outf = os.path.join(outd,proj)                               # create output file name
  outp = os.path.join(outd,name)
  #print "   here = '%s'"%os.getcwd()
  #print "   work = '%s'"%str((work,gend,path[len(sdir):]))
  #print "   outd = '%s'"%outd
  #print "   outf = '%s'"%outf
  #print "   outp = '%s'"%outp
  mkpath(outd)                                                  # create output folder, if not exists
  file(outp,"w").write(file(full,"r").read())                   # copy original project
  os.chdir(outd)                                                # set current working directory
  #print "qmake %s -tp vc -o %s"%(name,proj)
  o,i,e = popen3("qmake %s -tp vc -o %s"%(name,proj))           # use qmake, to generate solution

  #Microsoft's idiotics warnings = re.compile('(-w34100|-w34189|-Zm200)(\s|$|\")')
warnings = re.compile('(-w34100|-w34189)(\s|$|\")')
def replacer(match):
  return match.group(2)
def remove_some_idiotic_microsoft_warnings_from_project_file(fname):
  print fname
  buff=file(fname,"r").read()
  f=file(fname,"w")
  buff=warnings.sub(replacer,buff)
  f.write(buff)
  f.close()

#scriptmodules = os.path.join(wdir,"src")
print "argv[0]                     = ", arg0
print "current working directory   = ", cwd0
print "real proj working directory = ", work
print "souces directory            = ", sdir
print "temp folder                 = ", temp
print "QMAKESPEC=",os.environ["QMAKESPEC"]
print "-"*80

     # COLLECT ALL *.pro FILES IN SOURCE FOLDER
     #
collect_pro(sdir,1)

     # GENERATE MAKE-FILE FOR EACH *.pro IN SOURCE FOLDER, TO TEMPORARY FOLDER
     #
for i in proj:
  generate_make(i)

     # IF some MSVC in QMAKESPEC, GENERATE VISUAL STUDIO SOLUTION FROM ALL pro FILES
     #
if "msvc" in os.environ["QMAKESPEC"]:
  for i in pro_dict.keys():
    if pro_dict[i]["TEMPLATE"] != 'subdirs':
      generate_msvc_vcproj(i)
  for i in pro_dict.keys():
    if pro_dict[i]["TEMPLATE"] == 'subdirs':
      generate_msvc_solution(i)
  for i in msvc_project_files:
  	remove_some_idiotic_microsoft_warnings_from_project_file(i)

print "Ok."   
#import gen
#gen.root(wdir)
#os.path.exists(wdir)
# work - contain gx_project_root
# try to execute post gen routines
post_gen_routines=[]
for i in pro_dict.keys():
  routine_name=i.rsplit('pro')[0]+'gen.py'
  if os.path.isfile(routine_name):
     post_gen_routines.append(routine_name)
for i in post_gen_routines:
  print "EXEC:",i
  execfile(i,{"GEN_WORK":work,"GEN_HERE":i} )
  print
