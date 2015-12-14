#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""create_rados_user

wrapper to create RADOSgw user and push 'em into consul

Usage:
  create_rados_user.py [options] <uid>
  create_rados_user.py (-h | --help)
  create_rados_user.py --version

Options:
  -h --help             Show this screen.
  --version             Show version.
  --username <str>      Display Name of user

"""

# load librarys
from docopt import docopt
import envoy
import consul
import re
import json
import sys
import time
import requests

def check_service(name):
  """
  :param name: supervisord service to look for
  :return: True if service is up, False if not
  """
  url = "http://localhost:8500/v1/catalog/service/%s" % name
  try:
    req = requests.get(url)
  except requests.exceptions.ConnectionError:
    return False
  return req.status_code == 200

def wait_for_service(name, timeout=60):
  """ Waits for service, True if available and False it timeout is reached
  """
  srv = check_service(name)
  if srv:
    return True
  start = time.time()
  while (time.time() - start) < timeout:
    if check_service(name):
      return True
    else:
      time.sleep(1)
  return False

class RadosUser(object):
  """ Deal with rados users
  """
  def __init__(self, cfg):
    """ initialization  """
    self._cfg = cfg
    if self._cfg['--username'] is None:
      self._cfg['--username'] = self._cfg['<uid>']
    print "INFO - Wait for 'consul' service: ",
    if not wait_for_service("consul"):
      print " [ERROR]"
      raise IOError("Service consul not ready!")
    print " [OK]"
    self._con = consul.Consul()
    self._kv = self._con.kv

  def wait_for_srv(self, name, timeout=60):
    """ Waits for a service to become healthy
    :param name: Service name as register in consul
    :param timeout: Seconds until it raises an error
    """
    start = time.time()
    idx, res = self._con.catalog.service(name, wait=timeout)
    while len(res) == 0:
      time.sleep(1)
      if time.time() - start > timeout:
        return False
      idx, res = self._con.catalog.service(name, wait=timeout)
    return True

  def run(self):
    """ running block """
    if not self.wait_for_srv("ceph-radosgw"):
      print "ERROR - Service 'ceph-radosgw' did not come up within timeout"
      sys.exit(1)
    print "INFO - Service 'ceph-radosgw' did come up within timeout"
    self.create()
    self.push_conf()
    self.push_kv()

  def push_conf(self):
        """ Collects config to push them to KV """
        regex = re.compile("\s*key\s*=\s*(.*)")
        with open("/etc/ceph/ceph.client.admin.keyring", "r") as fd:
            lines = fd.readlines()
        for line in lines:
            line = line.strip()
            mat = re.match(regex, line)
            if mat:
                self._kv.put("ceph/ceph.client.admin.keyring", mat.group(1))
  def create(self):
    """ create the user via bash command
    """
    cmd = "radosgw-admin user create --uid=\"%(<uid>)s\" --display-name=\"%(--username)s\"" % self._cfg
    proc = envoy.run(cmd)
    if proc.status_code != 0:
      print proc.std_out, proc.std_err
      raise IOError()
    self._res = json.loads(proc.std_out)
    print "INFO - User '%(<uid>)s was created successfully" % self._cfg

  def push_kv(self):
    """ Push infos to KV store """
    def put(key, val):
      kvkey = "%s/%s" % (self._res['user_id'], key)
      idx, data = self._kv.get(kvkey)
      if data is None:
        print "INFO - >> '%s' not set (idx:%s)" % (kvkey, idx)
        self._kv.put(kvkey, val)
      elif data['Value'] == val:
        print "INFO - >> '%s' already set (idx:%s) to the same value" % (kvkey, idx)
      else:
        print "INFO - >> '%s' differs from what is in the KV (idx:%s), overwriting it..." % (kvkey, idx)
        self._kv.put(kvkey, val)
    put("user_id", self._res['user_id'])
    for item in self._res['keys']:
      put("keys/%s/access_key" % item['user'], item['access_key'])
      put("keys/%s/secret_key" % item['user'], item['secret_key'])
    for item in self._res['swift_keys']:
      put("swift/%s/access_key" % item['user'], item['access_key'])
      put("swift/%s/secret_key" % item['user'], item['secret_key'])
    print "INFO - Keys of user '%(<uid>)s were pushed to KV" % self._cfg

def main():
    """ main function """
    options = docopt(__doc__,  version='1.0.0')
    ruser = RadosUser(options)
    ruser.run()

if __name__ == "__main__":
    main()




