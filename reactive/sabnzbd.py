from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install, add_source, apt_update
from charmhelpers.core.host import adduser, service_start, service_restart, chownr
from charmhelpers.core.hookenv import status_set, log, resource_get
import os
import random
import string
import fileinput
import socket
import tarfile

@when_not('sabnzbd.installed')
def install_sabnzbd():
    config = hookenv.config()
    status_set('maintenance','installing sabnzbd')
    add_source('ppa:jcfp/nobetas')
    add_source('ppa:jcfp/sab-addons')
    apt_update()
    adduser(config['sabuser'],password=r''''''.join([random.choice(string.printable) for _ in range(random.randint(8, 12))]),home_dir='/home/'+config['sabuser'])
    apt_install('python-openssl')
    apt_install('par2-tbb')
    apt_install('python-sabyenc')
    apt_install('sabnzbdplus')
    status_set('active','')
    set_state('sabnzbd.installed')

@when_all('sabnzbd.installed','layer-hostname.installed')
@when_not('sabnzbd.restored')
def restore_user_conf():
    config = hookenv.config()
    backups = './backups'
    if config['restore-config']:
        try:
            os.mkdir(backups)
        except OSError as e:
            if e.errno is 17:
              pass
        backupFile = resource_get('sabconfig')
        if backupFile:
            with tarfile.open(backupFile,'r:gz') as inFile:
                inFile.extractall('/home/{}'.format(config['sabuser']))
            for line in fileinput.input('/home/{}/.sabnzbd/sabnzbd.ini'.format(config['sabuser']), inplace=True):
                if line.startswith("host="):
                    line = "host={}\n".format(socket.gethostname())
                print(line,end='') # end statement to avoid inserting new lines at the end of the line
            log("Changing configuration for new host but not ports. The backup configuration will override charm port settings!",'WARNING')
            chownr('/home/{}/.sabnzbd'.format(config['sabuser']),owner=config['sabuser'],group=config['sabuser'])
        else:
            log("Add sabconfig resource, see juju attach or disable restore-config",'ERROR')
            raise ValueError('Sabconfig resource missing, see juju attach or disable restore-config')
    set_state('sabnzbd.restored')
        

@when_all('sabnzbd.restored')
@when_not('sabnzbd.configured')
def write_configs():
    config = hookenv.config()
    status_set('maintenance','configuring sabnzbd')
    address = socket.gethostname()
    for line in fileinput.input('/etc/default/sabnzbdplus', inplace=True):
        if line.startswith("USER="):
            line = "USER={}\n".format(config['sabuser'])
        if line.startswith("HOST="):
            line = "HOST={}\n".format(address)
        if line.startswith("PORT=\n"):
            line = "PORT={}".format(config['port'])
        print(line,end='') # end statement to avoid inserting new lines at the end of the line
    hookenv.open_port(config['port'],'TCP')
    service_restart('sabnzbdplus')
    status_set('active','')
    set_state('sabnzbd.configured')
    set_state('sabnzbd.ready')

# TODO add relations
