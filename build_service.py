import glob
import os
import py_compile
import shutil

shutil.rmtree('./service_prod', ignore_errors=True)
os.mkdir('./service_prod')
os.mkdir('./service_prod/private')
for f in glob.glob('./service/*.py'):
    shutil.copy(f, './service_prod')
shutil.copytree('./service/static', './service_prod/static')
# We "lost" the source for monitor_internal, only have .pyc
py_compile.compile('./service_prod/monitor_internal.py', cfile='./service_prod/monitor_internal.pyc')
os.remove('./service_prod/monitor_internal.py')

