import glob
import os
import py_compile
import shutil

def copy_proj_tree(prefix):
    for f in glob.glob(f'./service/{prefix}/*.py'):
        fp = shutil.copy(f, f'./service_prod/{prefix}/')
        os.system(f'sed -i "/INTERNAL NOTE/d" {fp}')
    for rel_f in [f'{prefix}/requirements.txt', f'{prefix}/Dockerfile']:
        shutil.copy('./service/' + rel_f, './service_prod/' + rel_f)

shutil.rmtree('./service_prod', ignore_errors=True)
os.mkdir('./service_prod')
os.mkdir('./service_prod/webserver')
os.mkdir('./service_prod/monitor')
os.mkdir('./service_prod/files_private')
copy_proj_tree('webserver')
copy_proj_tree('monitor')
shutil.copytree('./service/webserver/static', './service_prod/webserver/static')
# We "lost" the source for monitor_internal, only have .pyc
py_compile.compile('./service_prod/monitor/monitor_internal.py',
                   cfile='./service_prod/monitor/monitor_internal.pyc')
os.remove('./service_prod/monitor/monitor_internal.py')

# Only one dir writeable by www-data
os.chmod('./service_prod/files_private', 0o777)

shutil.copy('./service/docker-compose.yml', './service_prod/docker-compose.yml')
