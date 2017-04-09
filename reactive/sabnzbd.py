from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install, add_source
from charmhelpers.core.host import adduser, service_start, service_restart
from charmhelpers.core.hookenv import status_set, log
import random
import string
import fileinput
import socket

@when_not('sabnzbd.installed')
def install_sabnzbd():
    config = hookenv.config()
    status_set('maintenance','installing sabnzbd')
    add_source('multiverse')
    adduser(config['sabuser'],password=''.join([random.choice(string.printable) for _ in range(random.randint(8, 12))]),home_dir='/home/'+config['sabuser'])
    apt_install('python-openssl')
    apt_install('sabnzbdplus')
    status_set('active','')
    set_state('sabnzbd.installed')

@when_all('sabnzbd.installed','layer-hostname.installed')
@when_not('sabnzbd.configured')
def wrtie_congs():
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
    set_state('sabnzbd.ready')

# TODO add config restore from backup
# TODO add relations
