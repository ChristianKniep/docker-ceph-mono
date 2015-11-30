#!/bin/bash

if [ $(find /var/run/ceph/ -name "ceph-mds*asok" | wc -l) -ne 1 ];then
	echo "ERROR - zero or more then one ceph-mds socket? Dunno if this is right, would expect exactly one"
    echo '>> find /var/run/ceph/ -name "ceph-mds*asok"'
    find /var/run/ceph/ -name "ceph-mds*asok"
    exit 1
else
	ceph_socket=$(find /var/run/ceph/ -name "ceph-mds*asok")
fi

ceph --admin-daemon ${ceph_socket} config show |jq .name
