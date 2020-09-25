#!/usr/bin/env python3

from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump
from subprocess import run, DEVNULL, PIPE
import re

app = Flask(__name__)

health = HealthCheck()
envdump = EnvironmentDump()

# Is etcd healthy?
def etcd_healthy():
    env_parsed = {}

    env_regex = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')

    with open('/etc/etcd.env') as env:
        for line in env:
            match = env_regex.match(line)
            if match is not None:
                env_parsed[match.group(1)] = match.group(2)

        rc = run(['/usr/local/bin/etcdctl', 'cluster-health'], stdout=PIPE, stderr=PIPE, env=env_parsed)

        if rc.returncode == 0:
           return True, "etcd healthy"
        elif rc.returncode == 5:
           return True, "etcd degraded"
        else:
           return False, "etcd unhealthy"


health.add_check(etcd_healthy)

# add your own data to the environment dump
def application_data():
    return {"maintainer": "Chris McCoy",
            "git_repo": "https://github.com/chris-mccoy/k8s-healthcheck"}

envdump.add_section("application", application_data)

# Add a flask route to expose information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/environment", "environment", view_func=lambda: envdump.run())

app.run()
