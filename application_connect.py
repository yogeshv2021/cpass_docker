#!/usr/bin/python
import socket
import time

import paramiko

localip=socket.gethostbyname(socket.gethostname())


class ApplicationConnect():

    """ Constructor """
    def __init__(self,host,username,key,prompt):
        self.host=host
        self.key=key
        self.username=username
        self.prompt=prompt
        self.seq_scen_map={}


    def ApplicationServerConnect(self):
        try:
            self.alias=paramiko.SSHClient()
            self.alias.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
            self.alias.connect(self.host,username=self.username,key_filename=self.key)
            self.channel=self.alias.invoke_shell()
            self.stdin = self.channel.makefile('wb')
            self.stdout = self.channel.makefile('rb')
            return self

        except Exception as e:
            print("Exception : %s" %str(e))


    def ApplicationServerDisconnect(self):
        try:
            self.alias.close()
        except Exception as e:
            print(str(e))


    def RecvData(self,prompt):

        self.buffer=""
        self.flag=True

        try:

            while self.flag:
 
                if self.stdout.channel.recv_ready():
                    self.buffer+=self.stdout.channel.recv(9999).decode('utf-8')

                if len(self.buffer)>0 and self.buffer.strip().endswith(prompt):
                    self.flag=False

            return (self.buffer)

        except Exception as e:
            print(str(e))


    def SendData(self,data):
        try:
            self.stdin.channel.send(data)
            print("sent successfully")
        except Exception as e:
            print(str(e))

    def startApplication(self,cmd):
        self.cmd=cmd+"\n"
        print(self.cmd)
        self.SendData(self.cmd)
        return "started"

    def stopApplication(self,cmd):
        self.cmd=cmd+"\n"
        print(self.cmd)
        self.SendData(self.cmd)
        time.sleep(1)
        return "stopped"

    def processAliveCheck(self,cmd,prompt):
        self.cmd=cmd+"\n"
        self.prompt=prompt
        print(self.cmd)
        self.SendData(self.cmd)
        time.sleep(1)
        self.out=self.RecvData(self.prompt)
        return self.out


if __name__ == "__main__":
    scpng=ApplicationConnect("192.168.151.127","testteam","/root/.ssh/id_rsa.pub","$")
    scpng.ApplicationServerConnect()
    cmd="cd /opt/product/testteam/Products/SCPNG/FMVNO/release/release/bin;bash startNG1.sh &"
    out=scpng.startApplication(cmd)
    print(out)
    time.sleep(5)
    cmd="cd /opt/product/testteam/Products/SCPNG/FMVNO/release/release/bin;bash startNG2.sh &"
    out=scpng.startApplication(cmd)
    print(out)
    time.sleep(5)
    cmd="ps -ef | grep -w \"lFMVNO-INS1\" | grep -v \"grep\" | awk '{print $2}'"
    out=scpng.processAliveCheck(cmd)
    print("process id")
    print(out)
    time.sleep(10)
    scpng.ApplicationServerDisconnect()
