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
import json
import sys
import time
from pprint import pprint

class RadosUser(object):
  """ Deal with rados users
  """
  def __init__(self, cfg):
    """ initialization  """
    self._cfg = cfg
    if self._cfg['--username'] is None:
      self._cfg['--username'] = self._cfg['<uid>']
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
    self.push_kv()

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




