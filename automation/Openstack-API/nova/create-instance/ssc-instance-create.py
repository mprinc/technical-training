# https://support.ultimum.io/support/solutions/articles/1000125460-python-novaclient-neutronclient-glanceclient-swiftclient-heatclient
# http://docs.openstack.org/developer/python-novaclient/ref/v2/servers.html
import time, os, sys
import inspect
from os import environ as env

from  novaclient import client
import keystoneclient.v3.client as ksclient
from keystoneauth1 import loading
from keystoneauth1 import session

flavor = "ssc.small"
private_net = "SNIC 2017/13-51 Internal IPv4 Network"
floating_ip_pool_name = "Public External IPv4 Network"
floating_ip = None; # "130.239.81.115"
image_name = "Ubuntu 14.04 LTS (Trusty Tahr) - latest"
key_name = "mprinc-hpc2n-se"

loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(auth_url=env['OS_AUTH_URL'],
                                username=env['OS_USERNAME'],
                                password=env['OS_PASSWORD'],
                                project_name=env['OS_PROJECT_NAME'],
                                user_domain_name=env['OS_USER_DOMAIN_NAME'],
                                project_domain_name=env['OS_PROJECT_DOMAIN_NAME'])


sess = session.Session(auth=auth)
nova = client.Client('2.1', session=sess)
print "user authorization completed."

image = nova.images.find(name=image_name)
flavor = nova.flavors.find(name=flavor)

if private_net != None:
    net = nova.networks.find(label=private_net)
    nics = [{'net-id': net.id}]
else:
    sys.exit("private-net not defined.")

secgroup = nova.security_groups.find(name="default")
secgroups = [secgroup.id]
secgroup = nova.security_groups.find(name="sasha-ICMP-SSH-HTTP-security-group")
secgroups = [secgroup.id]

#floating_ip = nova.floating_ips.create(nova.floating_ip_pools.list()[0].name)

if floating_ip_pool_name != None:
    # check if there is non-associated IP address first
    floating_ip = None
    for ip in nova.floating_ips.list():
        if(not ip.instance_id):
            floating_ip = ip;
            break;
    if(not floating_ip):
        floating_ip = nova.floating_ips.create(floating_ip_pool_name)
else:
    sys.exit("public ip pool name not defined.")


print "Creating instance ... "
instance = nova.servers.create(name="vm1", image=image, flavor=flavor, nics=nics,security_groups=secgroups, key_name=key_name)
inst_status = instance.status
print "waiting for 10 seconds.. "
time.sleep(10)

while inst_status == 'BUILD':
    print "Instance: "+instance.name+" is in "+inst_status+" state, sleeping for 5 seconds more..."
    time.sleep(5)
    instance = nova.servers.get(instance.id)
    inst_status = instance.status

print "Instance: "+ instance.name +" is in " + inst_status + " state"

if floating_ip != None:
    instance.add_floating_ip(floating_ip)
    print "Instance booted! Name: " + instance.name + " Status: " +instance.status+ ", Floating IP: " + floating_ip.ip
else:
    print "Instance booted! Name: " + instance.name + " Status: " +instance.status+ ", No floating IP attached"
