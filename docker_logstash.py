import csv
import time
import datetime
import os
from datetime import datetime


pubkey = '/root/.ssh/id_rsa.pub'
date_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
filepath = "/opt/product/testteam/LoadScript/LOGSTASH_STATS/"
filename = filepath + "LogStashApiStats_" + date_time +".csv"
print( filename)
Serverdata =["172.18.1.53"]
Usernamedata =["testteam"]
types = ["flow","process","events","reloads","os","jvm"]



def memory_stats(Serverdata):
    getdata=[]
    count=len(Serverdata)
    increment=0
    typecnt=len(types)
    for i in range(len(Serverdata)):
        for idx,jtype in enumerate(types):
            getstats = "curl -XGET 172.18.1.53:9600/_node/stats/" + jtype 
            findremotefile = os.popen(getstats)
            getlist = findremotefile.read()
            getlist.split("\n")
            writecsv(getlist,Serverdata[i],increment,getstats,typecnt,idx)

def writecsv(getlist,serverchk,increment,getstats,typecnt,idx):
    with open(filename, 'a+') as csvfile:
         typecnt=len(types)
         csvfile.write("====================Memory Stats=====================")
         csvfile.write("\n")
         csvfile.write("Server Instance for below stats data: %s" %serverchk)
         csvfile.write("\n")
         csvfile.write("Logstat type to fetch the data: %s" %getstats)
         csvfile.write("\n")
         csvfile.writelines(getlist)
         csvfile.write("\n")
         csvfile.write(datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
         csvfile.write("\n")
         print(idx,typecnt,getstats)
         idx=idx+1
         time.sleep(2)
         if idx==typecnt:
             csvfile.write("====================Waiting for 120secs=====================")
             csvfile.write("\n")
             csvfile.write("\n")
             csvfile.write("\n")
             time.sleep(120)
             increment=0
while True:
    memory_stats(Serverdata)


