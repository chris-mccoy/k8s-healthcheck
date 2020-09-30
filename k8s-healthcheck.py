#!/usr/bin/env ipython3

# apt-get install python3-systemd libsystemd-dev python3-dev pkg-config

from IPython import embed
from healthcheck import HealthCheck
from subprocess import run, DEVNULL, PIPE
from sys import exit
from time import sleep
from pystemd.systemd1 import Unit
import errno
import systemd.daemon
import systemd.journal
import logging
import re
import netifaces
import requests


health = HealthCheck(success_ttl = 10, failed_ttl = 2)

def is_etcd_healthy():
    env_parsed = {}

    env_regex = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')

    with open('/etc/etcd.env') as env:
        for line in env:
            match = env_regex.match(line)
            if match is not None:
                env_parsed[match.group(1)] = match.group(2)

        rc = run(['/usr/local/bin/etcdctl', 'cluster-health'], stdout=PIPE, env=env_parsed)

        logging.debug(rc.stdout)

        etcd_status = rc.stdout.splitlines()[-1]
        if rc.returncode == 0 and etcd_status == b'cluster is healthy':
           return True, "etcd cluster healthy"
        elif rc.returncode == 5 and etcd_status == b'cluster is degraded':
           return True, "etcd cluster degraded"
        else:
           return False, "etcd cluster unavailable"

health.add_check(is_etcd_healthy)

def private_ip_address(private_interface_name='vlan6'):
    return netifaces.ifaddresses(private_interface_name)[netifaces.AF_INET][0]['addr']

def kube_ca_cert():
    return "/etc/kubernetes/ssl/ca.crt"

def is_kube_apiserver_healthy():
    kube_url = "https://{}:6443/healthz".format(private_ip_address())
    logging.debug("kube_url is {}".format(kube_url))
    req = requests.get(kube_url, verify=kube_ca_cert())
    logging.debug(req)
    if req.status_code == 200 and req.text == "ok":
        return True, "kube apiserver healthy"
    else:
        return False, "kube apiserver is unhealthy"

health.add_check(is_kube_apiserver_healthy)

def is_bird_active():
    with Unit(b'bird.service') as bird_unit:
        bird_unit.load()
        if bird_unit.Unit.ActiveState == b'active':
            return True, "bird is active"
        else:
            return False, "bird is not active"

health.add_check(is_bird_active)
 
def main():
    #embed()

    logging.root.addHandler(systemd.journal.JournalHandler())
    #logging.root.setLevel(logging.DEBUG)
    logging.root.setLevel(logging.INFO)

    unhealthy = True
    retries = 0

    while True:
        logging.debug("Starting health check")

        (_, health_status, _) = health.run()

        if health_status == 200:
            if unhealthy:
                logging.info("All health checks passed")
                retries = 0
                unhealthy = False
                systemd.daemon.notify('READY=1')
                systemd.daemon.notify('ERRNO=0')

        elif health_status != 200:
            retries += 1
            if not unhealthy:
                logging.error("Health checks failed")
                systemd.daemon.notify('ERRNO={}'.format(errno.EIO))
                unhealthy = True
            if retries > 3:
                systemd.daemon.notify('RELOADING=1')
                exit(-1)

        sleep(5)
        systemd.daemon.notify('WATCHDOG=1')

if __name__ == "__main__":
    main()

