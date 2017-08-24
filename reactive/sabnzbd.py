from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers import fetch
from charmhelpers.core import host
import fileinput

from libsab import SabInfo

sab = SabInfo()


@when_not('sabnzbd.installed')
def install_sabnzbd():
    hookenv.status_set('maintenance', 'installing sabnzbd')
    fetch.add_source('ppa:jcfp/nobetas')
    fetch.add_source('ppa:jcfp/sab-addons')
    fetch.apt_update()
    sab.add_user()
    fetch.apt_install('python-openssl')
    fetch.apt_install('par2-tbb')
    fetch.apt_install('python-sabyenc')
    fetch.apt_install('sabnzbdplus')
    hookenv.status_set('active', '')
    set_state('sabnzbd.installed')


@when_all('sabnzbd.installed', 'layer-hostname.installed')
@when_not('sabnzbd.restored')
def restore_user_conf():
    if sab.charm_config['restore-config']:
        if not sab.restore_config():
            return  # If restore failed exit with out setting the state
    set_state('sabnzbd.restored')
        

@when_all('sabnzbd.restored')
@when_not('sabnzbd.configured')
def write_configs():
    # config = hookenv.config()
    hookenv.status_set('maintenance', 'configuring sabnzbd')
    sab.set_defaults()
    hookenv.open_port(sab.charm_config['port'], 'TCP')
    host.service_restart('sabnzbdplus')
    hookenv.status_set('active', '')
    set_state('sabnzbd.configured')
    set_state('sabnzbd.ready')


@when('sabnzbd.installed')
@when_not('avahi.configured')
def configure_avahi():
    for line in fileinput.input('/etc/avahi/avahi-daemon.conf', inplace=True):
        if line.startswith("rlimit-nproc"):
            line = "#" + line
        print(line, end='')
    set_state('avahi.configured')


@when_not('usenet-downloader.configured')
@when_all('usenet-downloader.triggered', 'sabnzbd.configured')
def configure_interface(usenetdownloader):
    hostname = sab.host
    port = sab.charm_config['port']
    apikey = sab.apikey
    usenetdownloader.configure(hostname=hostname, port=port, apikey=apikey)
    hookenv.log('usenet download provider configured', 'INFO')


@when_all('reverseproxy.triggered', 'reverseproxy.ready')
@when_not('reverseproxy.configured', 'reverseproxy.departed')
def configure_reverseproxy(reverseproxy, *args):
    # TODO: retrigger if config changes?
    hookenv.log("Setting up reverseproxy", "INFO")
    proxy_info = {'urlbase': sab.charm_config['proxy-url'],
                  'subdomain': sab.charm_config['proxy-domain'],
                  'group_id': 'sabnzbd',
                  'external_port': sab.charm_config['proxy-port'],
                  'internal_host': sab.host,
                  'internal_port': sab.charm_config['port']
                  } 

    reverseproxy.configure(proxy_info)
    # cp.set_urlbase(proxy_info['urlbase'])
    # cp.restart()


@when_all('reverseproxy.triggered', 'reverseproxy.departed')
def remove_urlbase(reverseproxy, *args):
    hookenv.log("Removing reverseproxy configuration", "INFO")
    # cp.set_urlbase('')
    # cp.restart()


