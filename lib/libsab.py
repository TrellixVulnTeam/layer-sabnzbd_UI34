from charmhelpers.core import hookenv, host

import configparser
import fileinput
import tarfile
import socket
import os


class SabInfo:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.user = self.charm_config['sabuser']
        self.home_dir = '/home/{}'.format(self.user)
        self.install_dir = self.home_dir + '/.sabnzbd'
        self.settings_file = self.install_dir + '/sabnzbd.ini'
        self.default_file = "/etc/default/sabnzbdplus"
        self.resource_name = 'sabconfig'
        self.resource_folder = hookenv.charm_dir() + '/resources'
        self.sab_config = configparser.ConfigParser(comment_prefixes=('#', ';', '__'))
        self.sab_config.read(self.settings_file)

    def reload_config(self):
        self.sab_config.read(self.settings_file)

    def save_config(self):
        with open(self.settings_file, 'w') as openFile:
            self.sab_config.write(openFile)

    def add_user(self):
        host.adduser(self.charm_config['sabuser'], password="", shell='/bin/False', home_dir=self.home_dir)

    def set_host(self):
        # use set_defaults it appears sab updates host automatically
        self.sab_config['misc']['host'] = self.host
        hookenv.log("Couchpotato hostname set to {}".format(self.host), "INFO")

    def set_port(self):
        # use set_defaults it appears sab updates port automatically
        self.sab_config['misc']['port'] = str(self.charm_config['port'])

    def set_defaults(self):
        for line in fileinput.input(self.default_file, inplace=True):
            if line.startswith("USER="):
                line = "USER={}\n".format(self.charm_config['sabuser'])
            if line.startswith("HOST="):
                line = "HOST={}\n".format(self.host)
            if line.startswith("PORT="):
                line = "PORT={}\n".format(self.charm_config['port'])
            print(line, end='')  # end statement to avoid inserting new lines at the end of the line

    def restore_config(self):
        try:
            os.mkdir(self.resource_folder)
        except OSError as e:
            if e.errno is 17:
                pass

        backupFile = hookenv.resource_get(self.resource_name)
        if backupFile:
            with tarfile.open(backupFile, 'r:gz') as inFile:
                inFile.extractall(self.home_dir)
            self.set_host() 
            self.set_port()
            self.save_config()
            host.chownr(self.install_dir, owner=self.charm_config['sabuser'], group=self.charm_config['sabuser'])
            return True
        else:
            hookenv.log("Add sabconfig resource, see juju attach or disable restore-config", 'ERROR')
            hookenv.status_set('blocked', 'Waiting on sabconfig resource')
            return False

    @property
    def apikey(self):
        return self.sab_config['misc']['api_key']
        # for line in fileinput.input(self.settings_file):
        #     if line.startswith("api_key"):
        #         apikey = line.split("=")[1].strip()
        # return apikey

    @property
    @hookenv.cached
    def host(self):
        return socket.getfqdn()
        # return socket.gethostname()
        # TODO: should this use socket.getfqdn instead of just gethostname?
