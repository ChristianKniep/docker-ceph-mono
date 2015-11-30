#!/bin/bash

SRV=osd

if [ $(find /var/run/ceph/ -name "ceph-${SRV}*asok" | wc -l) -ne 1 ];then
	echo "ERROR - zero or more then one ceph-${SRV} socket? Dunno if this is right, would expect exactly one"
    echo '>> find /var/run/ceph/ -name "ceph-${SRV}*asok"'
    find /var/run/ceph/ -name "ceph-${SRV}*asok"
    exit 1
else
	ceph_socket=$(find /var/run/ceph/ -name "ceph-${SRV}*asok")
fi

ceph --admin-daemon ${ceph_socket} status |jq .state | grep active
