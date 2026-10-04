#!/usr/bin/python

import subprocess
import csv  
import time
import datetime
import os
from datetime import datetime

pubkey = '/root/.ssh/id_rsa.pub'
date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
filepath = "/opt/product/testteam/LoadScript/MEMORY/"
filename = filepath + "DockerCpuMemStats_" + date_time +".csv"
print( filename)
Serverdata =["172.18.1.49","172.18.1.50","172.18.1.51"]
Usernamedata =["testteam","root","testteam"]



def memory_stats(Serverdata ):
    getdata=[]
    count=len(Serverdata)
    increment=0
    for i in range(len(Serverdata)):
        getstats = 'ssh ' + Usernamedata[i] + "@" + Serverdata[i] + " " + 'docker stats  -a --no-stream | egrep -i "cpa|kaf|log|image-opa|demo-keycloak|magical_haslett|sms|event|nginx|redis|elk"'
        findremotefile = os.popen(getstats)
        getlist = findremotefile.read()
        getlist.split("\n")
        writecsv(getlist,Serverdata[i],increment)

def writecsv(getlist,serverchk,increment):
    with open(filename, 'a+') as csvfile: 
         csvfile.write("====================Memory Stats=====================")
         csvfile.write("\n")
         csvfile.write("Server Instance for below stats data: %s" %serverchk)
         csvfile.write("\n")
         csvfile.writelines(getlist)
         csvfile.write("\n")
         csvfile.write(datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
         csvfile.write("\n")
         increment+=1
         if increment==3:
             csvfile.write("Sleeping for 120secs")
             time.sleep(120)
             increment=0

while True:
    memory_stats(Serverdata)

