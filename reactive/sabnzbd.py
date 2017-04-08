from charms.reactive import when, when_not, set_state
from charmhelpers.fetch import apt_install add_source

@when_not('sabnzbd.installed')
def install_layer_sabnzbd():
   status_set('maintenance','installing sabnzbd')
   add_source('multiverse')
   apt_install('sabnzbdplus')
   set_state('sabnzbd.installed')
