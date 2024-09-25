from __future__ import print_function
from bcc import BPF
from sys import argv

import sys
import socket
import os
import time

interface="rfsim5g-public"
seid_mappings_path = "/home/gabriele/april/FULL_STACK/fifth/openairinterface5g/ci-scripts/yaml_files/5g_rfsimulator/seid_mappings.txt"
path = "/home/gabriele/april/FULL_STACK/fifth/openairinterface5g/ci-scripts/yaml_files/5g_rfsimulator/"

print ("binding socket to '%s'" % interface)

#initialize BPF object loading source code from pfcp-filter-simple.c
bpf = BPF(src_file = "pfcp-filter-simple.c",debug = 0)

#load eBPF function pfcp_filter(), type SOCKET_FILTER
function_pfcp_filter = bpf.load_func("pfcp_filter", BPF.SOCKET_FILTER)

#create raw socket, bind it to rfsim5g-public
#attach bpf program to socket created
BPF.attach_raw_socket(function_pfcp_filter, interface)

#get file descriptor of the socket previously created inside BPF.attach_raw_socket
socket_fd = function_pfcp_filter.sock

#python socket object, from the file descriptor
sock = socket.fromfd(socket_fd,socket.PF_PACKET,socket.SOCK_RAW,socket.IPPROTO_IP)
sock.setblocking(True)

print("STARTING TO READ FROM PUBLIC NET") 
count = 0

while 1:
  packet_str = os.read(socket_fd,2048)

  packet_hex = packet_str.hex()
  seid_sequence = packet_hex[92:108]
  seid = int(seid_sequence, 16)

  seid_ue_map = {}
  with open(seid_mappings_path, 'r') as file:
      lines = file.readlines()
  for line in lines:
      key, value = line.strip().split('\t')
      seid_ue_map[int(key)] = int(value)

  time.sleep(2)

  ue_index = seid_ue_map.get(seid)

  pwd = os.getcwd()
  os.chdir(path)

  #restart affected UE    
  bashCommand="docker compose restart oai-nr-ue"+str(ue_index)+""

  os.system(bashCommand)
  os.chdir(pwd)

  time.sleep(7)
