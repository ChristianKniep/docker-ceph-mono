#!/bin/bash

if [ $(find /var/run/ceph/ -name "ceph-mon*asok" | wc -l) -ne 1 ];then
	echo "ERROR - zero or more then one ceph-mon socket? Dunno if this is right, would expect exactly one"
    echo '>> find /var/run/ceph/ -name "ceph-mon*asok"'
    find /var/run/ceph/ -name "ceph-mon*asok"
    exit 1
else
	ceph_socket=$(find /var/run/ceph/ -name "ceph-mon*asok")
fi

ceph --admin-daemon ${ceph_socket} mon_status |jq .state
