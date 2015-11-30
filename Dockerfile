FROM qnib/ceph-base

RUN pip install envoy
ADD opt/qnib/ceph/bin/start.sh /opt/qnib/ceph/bin/
ADD etc/supervisord.d/ceph.ini /etc/supervisord.d/
ADD opt/qnib/ceph/mon/bin/isok.sh /opt/qnib/ceph/mon/bin/
ADD opt/qnib/ceph/mds/bin/isok.sh /opt/qnib/ceph/mds/bin/
ADD opt/qnib/ceph/osd/bin/isok.sh /opt/qnib/ceph/osd/bin/
ADD opt/qnib/ceph/radosgw/bin/isok.sh /opt/qnib/ceph/radosgw/bin/
ADD etc/consul.d/*.json /etc/consul.d/
ADD etc/supervisord.d/rados-add-user.ini /etc/supervisord.d/
ADD opt/qnib/ceph/bin/create_rados_user.py /opt/qnib/ceph/bin/
