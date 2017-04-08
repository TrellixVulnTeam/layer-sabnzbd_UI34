from charms.reactive import when, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install, add_source
from charmhelpers.core.host import adduser
from charmhelpers.core.hookenv import status_set, log
from charmhelpers.core.services.base import service_restart
import random
import string

@when_not('sabnzbd.installed')
def install_layer_sabnzbd():
   config = hookenv.config()
   status_set('maintenance','installing sabnzbd')
   add_source('multiverse')
   adduser(config['sabuser'],password=''.join([random.choice(string.printable) for _ in range(random.randint(8, 12))]),home_dir='/home/'+config['sabuser'])
   apt_install('python-openssl')
   apt_install('sabnzbdplus')
   status_set('active','')
   set_state('sabnzbd.installed')
