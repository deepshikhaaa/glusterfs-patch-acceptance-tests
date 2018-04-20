#!/usr/bin/env python
'''
A script to create and delete the number of servers on Rackspace
'''

import pyrax
import time
import re
import os
import argparse
from Crypto.PublicKey import RSA

def create_key():
    key = RSA.generate(1024)
    f = open("private.pem", "wb")
    f.write(key.exportKey('PEM'))
    f.close()

    pubkey = key.publickey()
    f = open("public.pem", "wb")
    f.write(pubkey.exportKey('OpenSSH'))
    f.close()


def create_node(nova, counts):
    flavor = nova.flavors.find(name='2 GB General Purpose v1')
    image = nova.images.find(name='centos7-test')
    create_key()
    pubkey = open('public.pem', 'r').read()
    nova.keypairs.create('distkey', pubkey)
    for count in range(int(counts)):
        name = 'distributed-testing.'+str(count+1)
        node = nova.servers.create(name=name, flavor=flavor.id,
                                   image=image.id, key_name='distkey')

        while node.status == 'BUILD':
            time.sleep(5)
            node = nova.servers.get(node.id)

        ip_address = None
        for network in node.networks['public']:
            if re.match('\d+\.\d+\.\d+\.\d+', network):
                ip_address = network
                break
        if ip_address is None:
            print 'No IP address assigned!'
            sys.exit(1)
        print 'The server {0} is waiting at IP address {1}.'.format(count, ip_address)


def delete_node(nova, counts):
    for count in range(int(counts)):
        # find the server by name
        machine_name = 'distributed-testing.'+str((count+1))
        server = nova.servers.find(name=machine_name)
        server.delete()
        print 'Deleting {0}, please wait...'.format(machine_name)

        # delete the public key on Rackspace as well as locally
        nova.keypairs.delete('distkey')
        os.remove('public.pem')
        os.remove('private.pem')


def main():
    #mport pdb; pdb.set_trace()
    pyrax.set_setting('identity_type', 'rackspace')
    pyrax.set_default_region('ORD')
    pyrax.set_credential_file("/home/dkhandel/.rackspace_cloud_credentials")
    #pyrax.set_credentials(os.environ.get('USERNAME'),os.environ.get('PASSWORD'))
    nova_obj = pyrax.cloudservers

    parser = argparse.ArgumentParser(description="Rackspace server creation/deletion")
    parser.add_argument("action", choices=['create', 'delete'], help='Action to be perfromed')
    parser.add_argument("-n", "--count", help='Number of machines')
    args = parser.parse_args()
    count = args.count
    if (args.action == 'create'):
        create_node(nova_obj, count)
    elif (args.action == 'delete'):
        delete_node(nova_obj, count)

main()
