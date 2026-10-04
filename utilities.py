#!/usr/bin/python

import datetime
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import numpy as np


class UtilityLib:
    """ Initialize configurtion and reading xml config file """

    def __init__(self, config_file):
        """ To store the default configuration value from config file before user decides """
        self.config_list = []
        self.docker_server_list =[]

        """ To store the default simulator configuration value from config file before user decides """
        self.sim_config_list = []

        self.app_server_map = {}
        self.sim_server_map = {}
        self.prod_instance_map = {}
        self.instance_configuration_map = {}

        self.scenario_configuration_map = {}
        self.sim_prod_instance_map = {}
        self.sim_instance_map = {}
        self.gui_config_list = []

        self.config_file = config_file

    """execute command in remote server and will return output"""

    def remoteCommand(self, ip, cmd, username):

        print("Start remoteCommand time:", datetime.datetime.now())
        self.HOST = username + "@" + ip
        self.COMMAND = cmd
        print(cmd)
        self.ssh = subprocess.Popen(["ssh", "%s" % self.HOST, self.COMMAND], shell=False, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        self.res = self.ssh.communicate()[0]
        self.res = self.res.decode("utf-8")
        self.res = self.res.split("\n")
        print(self.res)
        print("End remoteCommand time:", datetime.datetime.now())
        return (self)

    def remoteCopy(self, ip, username, rempath, locpath):

        print("Start remoteCommand time:", datetime.datetime.now())
        self.REMFILE = username + "@" + ip + ":" + rempath
        self.LOCFILE = locpath
        self.scp = subprocess.Popen(["scp", self.REMFILE, self.LOCFILE], shell=False, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        return (self)

    def remoteConnect(self, ip, cmd, username):
        self.tempfile = open("temp.txt", 'w')
        self.HOST = username + "@" + ip
        self.COMMAND = cmd
        self.ssh = subprocess.Popen(["ssh", "%s" % self.HOST, self.COMMAND], shell=False, stdout=self.tempfile,
                                    stderr=self.tempfile)
        time.sleep(2)
        self.ssh.kill()
        self.tempfile.close()
        return (self)

    """execute command in local server and will return output"""

    def localCommand(self, cmd):
        print("inside local command")
        print(cmd)
        self.ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.res = self.ps.communicate()[0]
        self.res = self.res.decode("utf-8")
        print("localCommand response")
        print(self.res)
        return (self.res)

    """execute command in local server and will return output"""

    def localCommandresp(self, cmd):
        print("inside local command")
        print(cmd)
        self.ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.res = self.ps.communicate()[0]
        self.res = self.res.decode("utf-8")
        print("localCommand response")
        print(self.res)
        return (self.res)

    """execute command in local server and will return output"""

    def listlocalCommand(self, cmd):
        print("inside local command")
        print(cmd)
        self.ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.res = self.ps.communicate()[0]
        self.res = self.res.decode("utf-8")
        self.res = self.res.split("\n")
        return (self)

    def create_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def command_output_space_processing(self, command):
        command = command.strip()
        command_list = command.split()
        return command_list

    def command_output_split_processing(self, command, delimiter):
        command = command.strip()
        command_list = command.split(delimiter)
        return command_list

    def compute_file_name(self, directory, template_name, product, t, file_type):
        file_name = directory + product + template_name + str(t.tm_year) + '_' + str(t.tm_mon).zfill(2) + '_' + str(
            t.tm_mday).zfill(2) + '_' + str(t.tm_hour).zfill(2) + '_' + str(t.tm_min).zfill(2) + '_' + str(
            t.tm_sec).zfill(2) + "." + file_type
        return file_name

    def product_command_framing(self, product_cmd):
        
#        instance_docker, instance, process_id, logger_path, server_type
         num_of_commands = 2
         cmd = ""
         instancelist=[]
         dockerinstancelist=[]
         processlist=[]
         loggerpathlist=[]
         servertypelist=[]
         instanceresultlist= []

         getdockernamecmd='docker ps --format "{{.Names}}"'

         if product_cmd[0][7] == "1":
             self.getdockername = self.remoteCommand(product_cmd[0][5],getdockernamecmd,product_cmd[0][6])

         for getinstance in product_cmd:
             if getinstance[0] == "1":
                 if getinstance[1] in self.getdockername.res[:-1]:
                     instanceresultlist.append(1)
                     instancelist.append(getinstance[1])
                     dockerinstancelist=",".join(instancelist).replace(",","|")
                 else:
                     instanceresultlist.append(0)

             if (getinstance[2] == 0 or not getinstance[2]):
                 processlist.append('0')

             loggerpathlist.append(getinstance[3])
             servertypelist.append(getinstance[4])

         if dockerinstancelist:
             prstat_cmd = 'docker container stats -a --no-stream | egrep -w \'' + dockerinstancelist+ '\''
             prstat_end_cmd = 'echo PRSTAT_END'
             cmd = prstat_cmd + ";" + prstat_end_cmd + ";"
             return (num_of_commands, cmd)


    def server_command_framing(self, server_type):

        num_of_commands = 6
        if server_type in "SOLARIS":
            date_cmd = 'date'
            sar_cmd = "sar -u 1 1 | awk 'NR==5' | tr -s"
            load_avg_cmd = "prstat 60 1 | grep -w 'load averages:' | awk '{print $2,$4,$8,$9,$10}' | tr -s"
            vmstat_cmd = "vmstat 1 2| awk 'NR==4,NR==$NR {print}'|tr -s"
            iostat_cmd = "iostat -XDMz 1 2| grep -v 'device' | awk 'BEGIN{ORS = \";\"}NR==2,NR==$NR{print $1,$4,$5,$8,$9,$10}';echo"
            netstat_cmd = "netstat -i | awk 'BEGIN{ORS = \";\"}NR==2,NR==$NR{print $1,$5,$6,$7,$8,$9}';echo"
        else:
            date_cmd = 'date'
            sar_cmd = "sar -u 1 1 | awk 'NR==4'| awk '{print $1,$4,$6,$7,$9}'"
            load_avg_cmd = "echo Linux Load Average not implemented"
            vmstat_cmd = "vmstat 1 2 | awk 'NR==4'"
#            iostat_cmd = "if grep -q '7.3' /etc/redhat-release ; then iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = ";"}NR==2,NR==$NR{print $1,$6,$7,$10,$13,$14}'; elseif grep '8.6' /etc/redhat-release ; iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = ";"}NR==2,NR==$NR{print $1,$6,$7,$10,$13,$14}';else iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = ";"}NR==2,NR==$NR{print $1,$6,$7,$10,$11,$12}'; fi;echo"
            #iostat_old = "iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = \";\"}NR==2,NR==$NR{print $1,$6,$7,$10,$13,$14}';echo"
            iostat_cmd = "if grep -q 'Linux' /etc/redhat-release ; then iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = \";\"}NR==2,NR==$NR{print $1,$6,$7,$10,$13,$14}'; else iostat -xzmd 1 2 | egrep -vi '^$|device'| awk 'BEGIN{ORS = \";\"}NR==2,NR==$NR{print $1,$6,$7,$10,$11,$12}'; fi;echo"
            netstat_cmd = "netstat -i | awk 'BEGIN{ORS = \";\"}NR==3,NR==$NR{print $1,$3,$4,$5,$6,$7,$8,$9,$10}';echo"

        cmd = date_cmd + ";" + sar_cmd + ";" + load_avg_cmd + ";" + vmstat_cmd + ";" + iostat_cmd + ";" + netstat_cmd + ";"

        return (num_of_commands, cmd)

    """ Parse through XML file and store all the values based on xml hierarchy in config_list list array """

    def config_read(self):

        """
            CONFIG LIST
           
            Index 0 - Server Name
            Index 1 - Product Name
            Index 2 - Instance Name
            Index 3 - Starter Script
            Index 4 - Server Type
            Index 5 - User Name of Server
            Index 6 - Wait time after starting product instance
            Index 7 - Time Interval between stats capturing
            Index 8 - Flag to check product instance alive or not
            Index 9 - Load Statistics Path
            Index 10 - Instance Logger Path
            Index 11 - Delete Mode
            Index 12 - File Count not to be deleted if delete mode active
            Index 13 - Log File Delete Frequency Interval
            Index 14 - Server ID
            Index 15 - Server Mode APPLICATION OR SIMULATOR
            Index 16 - Server Key
            Index 17 - Server Prompt
        """

        self.tree = ET.parse(self.config_file)
        self.root = self.tree.getroot()
        self.stats_dur_name = self.root.find('stats_duration').attrib['name']
        self.title_name = self.root.find('title').attrib['name']
        self.stats_path_name = self.root.find('stats_path').attrib['name']
        self.load_restart_count_name = self.root.find('load_restart_count').attrib['name']
        self.framework_logger_path_name = self.root.find('framework_logger_path').attrib['name']

        for self.server in self.root.findall('server'):
           
            print(self.server)

            self.server_name = self.server.attrib['name']

            self.server_id = self.server.attrib['id']

            self.server_min_sar_stat_file_name[self.server_id] = "0"

            self.server_type = self.server.find('server_type').attrib['name']

            self.server_user = self.server.find('server_user').attrib['name']

            self.server_key_path = self.server.find('server_key_path').attrib['name']

            self.server_prompt = self.server.find('server_prompt').attrib['name']

            self.log_delete_interval = self.server.find('log_delete_sleep_interval').attrib['name']

            self.server_mode = self.server.find('server_mode').attrib['name']

            self.server_docker = self.server.find('server_docker').attrib['name']

            if (self.server_mode == "APPLICATION"):

                print("Server : %s\tServer ID : %s\tServer Type : %s\tServer User Name : %s\tServer Mode : %s\tServer Docker : %s" % (
                self.server_name, self.server_id, self.server_type, self.server_user, self.server_mode,self.server_docker))

                for self.prod in self.server.findall('product'):
                    instances = []
                    self.prod_name = self.prod.attrib['name']
                    self.prod_sleep_time = self.prod.find('sleep_time').attrib['name']
                    print("\nProduct : %s" % self.prod_name)

                    for self.inst in self.prod.findall('instance'):
                        self.inst_name = self.inst.attrib['name']
                        instances.append(self.inst_name)

                        for self.inst_starter in self.inst.findall('instance_starter'):
                            self.inst_starter_name = self.inst_starter.attrib['name']

                        for self.inst_logger in self.inst.findall('instance_logger_path'):
                            self.inst_logger_name = self.inst_logger.attrib['name']

                        for self.inst_log_delete_mode in self.inst.findall('instance_logger_delete'):
                            self.inst_log_delete_name = self.inst_log_delete_mode.attrib['name']

                        for self.inst_log_keep_files in self.inst.findall('instance_log_files_to_remain'):
                            self.inst_log_keep_files_name = self.inst_log_keep_files.attrib['name']

                        for self.instance_docker in self.inst.findall('instance_docker'):
                            self.instance_docker_flag_name = self.instance_docker.attrib['name']

                        self.config_list.append(
                            [self.server_name, self.prod_name, self.inst_name, self.inst_starter_name, self.server_type,
                             self.server_user, self.prod_sleep_time, self.stats_dur_name, 0, self.stats_path_name,
                             self.inst_logger_name, self.inst_log_delete_name, self.inst_log_keep_files_name,
                             self.log_delete_interval, self.server_id, self.server_mode, self.server_key_path,
                             self.server_prompt,self.instance_docker_flag_name,self.server_docker])

                        print("Instance : %s , Starter Script :%s , Logger Path : %s\n,instance name : %s\n" % (
                        self.inst_name, self.inst_starter_name, self.inst_logger_name,self.instance_docker_flag_name))

                        """ Below variable is for GUI Purpose """
                        self.instance_configuration_map[self.server_id + ";" + self.prod_name + ";" + self.inst_name] = \
                        self.config_list[-1]

                    """ Below variable is for GUI Purpose """
                    self.prod_instance_map[self.server_id + ";" + self.prod_name] = instances
                    self.gui_config_list.append([self.server_id, self.prod_name])

                """ Below variable is for GUI Purpose """
                self.app_server_map[self.server_id] = [self.server_name, self.prod_name, self.server_type,
                                                       self.server_user, self.prod_sleep_time, self.stats_dur_name,
                                                       self.stats_path_name, self.server_id, self.server_mode,
                                                       self.log_delete_interval]

        return (self)

    """ Parse through XML file and store all the simulator configuration values based on xml hierarchy in config_list list array """

    def simulator_config_read(self) -> object:

        """
            SIMULATOR CONFIG LIST
           
            Index 0 - Server Name
            Index 1 - SIMULATOR Name
            Index 2 - Simulator Sleep Interval
            Index 3 - Simulator Library Path
            Index 4 - Scenario Name
            Index 5 - Scenario Starter
            Index 6 - Scenario Rate
            Index 7 - Server Type
            Index 8 - Server User
            Index 9 - Server ID
            Index 10 - Server Mode APPLICATION OR SIMULATOR
            Index 11 - Scenario URL for Seagull and Mandatory or Optional Scenario Configuration for MGTS
            Index 12 - Statistics Path
            Index 13 - Simulator vs Product Association
            Index 14 - MGTS Shelf Name
            Index 15 - MGTS Assignment Name
            Index 16 - MGTS Sequence Group Name
            Index 17 - Number of times to execute mandatory MGTS Scenarios in case of fail
            Index 18 - Command Prompt of the server
            Index 19 - Public Key of the server
            Index 20 - MGTS Node Name
            Index 21 - MGTS Association Scenario Timeout
            Index 22 - MGTS Sequence Group Backup Path
            Index 23 - Stateful or Stateless Scenario Mode
            Index 24 - Initial Count
            Index 25 - Update Count
            Index 26 - Terminate Count
            Index 27 - On-hold Time
            Index 28 - Scenario Stats
            Index 29 - Mgts Stats
            Index 30 - Mgts Stat flag

        """
        self.tree = ET.parse(self.config_file)
        self.root = self.tree.getroot()
        self.stats_dur_name = self.root.find('stats_duration').attrib['name']
        self.title_name = self.root.find('title').attrib['name']
        self.stats_path_name = self.root.find('stats_path').attrib['name']
        self.load_restart_count_name = self.root.find('load_restart_count').attrib['name']

        print("\nLoad Simulator Configuration\n")

        for self.server in self.root.findall('server'):
            self.server_name = self.server.attrib['name']

            self.server_id = self.server.attrib['id']

            self.server_type = self.server.find('server_type').attrib['name']

            self.server_user = self.server.find('server_user').attrib['name']

            self.server_key_path = self.server.find('server_key_path').attrib['name']

            self.server_prompt = self.server.find('server_prompt').attrib['name']

            self.log_delete_interval = self.server.find('log_delete_sleep_interval').attrib['name']

            self.server_mode = self.server.find('server_mode').attrib['name']

            self.server_docker = self.server.find('server_docker').attrib['name']


            simulators = []

            if (self.server_mode == "SIMULATOR"):

                print("Server : %s\tServer ID : %s\tServer Type : %s\tServer User Name : %s\tServer Mode : %s" % (
                self.server_name, self.server_id, self.server_type, self.server_user, self.server_mode))

                for self.sim in self.server.findall('simulator'):
                    self.sim_name = self.sim.attrib['name']
                    self.sim_sleep_time = self.sim.find('sleep_time').attrib['name']
                    self.sim_lib_path = self.sim.find('library_path').attrib['name']
                    print("Simulator : %s" % self.sim_name)
                    simulators.append(self.sim_name)

                    """ to add shelf name only for mgts """
                    if (self.sim_name == "MGTS"):
                        self.sim_shelf_name = self.sim.find('shelf').attrib['name']
                    else:
                        self.sim_shelf_name = "0"

                    """ to add node name only for mgts """
                    if (self.sim_name == "MGTS"):
                        self.sim_node_name = self.sim.find('node').attrib['name']
                    else:
                        self.sim_node_name = "0"

                    for self.sim_product in self.sim.findall('simulator_product'):

                        self.sim_product_name = self.sim_product.attrib['name']
                        scenarios = []

                        """ to add assignment name only for mgts """
                        if (self.sim_name == "MGTS"):
                            self.sim_assignment_name = self.sim_product.find('assignment').attrib['name']
                        else:
                            self.sim_assignment_name = "0"

                        """ to add sequence group name only for mgts """
                        if (self.sim_name == "MGTS"):
                            self.sim_seq_group_name = self.sim_product.find('sequence_group').attrib['name']
                        else:
                            self.sim_seq_group_name = "0"

                        """ to add stats name only for mgts """
                        if (self.sim_name == "MGTS"):
                            self.mgts_stats_name = self.sim_product.find('mgts_stats').attrib['name']
                            print("mgts stats name is %s\n" % self.mgts_stats_name)
                        else:
                            self.mgts_stats_name = "0"

                        """ to add stats name only for mgts """
                        if (self.sim_name == "MGTS"):
                            self.mgts_stat_flag = self.sim_product.find('mgts_stat_flag').attrib['name']
                            print("mgts_stat_flag is %s\n" % self.mgts_stat_flag)
                        else:
                            self.mgts_stat_flag = "0"

                        """ to add backup sequence group path only for mgts """
                        if (self.sim_name == "MGTS"):
                            self.sim_seq_group_backup_name = self.sim_product.find('sequence_group').attrib[
                                'backup_path']
                        else:
                            self.sim_seq_group_backup_name = "0"

                        for self.scenario in self.sim_product.findall('scenario'):
                            self.scenario_name = self.scenario.attrib['name']
                            print("scenario: %s" % self.scenario_name)
                            scenarios.append(self.scenario_name)

                            for self.scenario_starter in self.scenario.findall('scenario_starter'):
                                self.scenario_starter_name = self.scenario_starter.attrib['name']
                                print("Starter Script is %s\n" % self.scenario_starter_name)

                            for self.scenario_rate in self.scenario.findall('scenario_callrate'):
                                self.scenario_rate_name = self.scenario_rate.attrib['name']
                                print("Call Rate is %s\n" % self.scenario_rate_name)

                            if (self.sim_name == "SEAGULL" or self.sim_name == "SIPPY"):
                                for self.scenario_url in self.scenario.findall('scenario_url'):
                                    self.scenario_url_name = self.scenario_url.attrib['name']
                                    self.scenario_url_times = "0"
                                    self.scenario_url_timeout = "0"
                                    print("URL is %s\n" % self.scenario_url_name)

                            elif (self.sim_name == "MGTS"):
                                for self.scenario_url in self.scenario.findall('scenario_type'):
                                    self.scenario_url_name = self.scenario_url.attrib['name']
                                    self.scenario_url_times = self.scenario_url.attrib['times']
                                    self.scenario_url_timeout = self.scenario_url.attrib['timeout']
                                    print("URL is %s\n" % self.scenario_url_name)

                            if (self.sim_name == "SEAGULL" or self.sim_name == "SIPPY"):
                                for self.scenario_stats in self.scenario.findall('scenario_stats'):
                                    self.scenario_stats_name = self.scenario_stats.attrib['name']
                                    print("Stats is %s\n" % self.scenario_stats_name)
                            else:
                                self.scenario_stats_name = "0"

                            for self.scenario_mode in self.scenario.findall('scenario_mode'):
                                self.scenario_mode_name = self.scenario_mode.attrib['name']

                                if (self.scenario_mode_name == "STATEFULL"):
                                    self.initial_count = self.scenario_mode.find('initial_count').attrib['name']
                                    self.update_count = self.scenario_mode.find('update_count').attrib['name']
                                    self.terminate_count = self.scenario_mode.find('terminate_count').attrib['name']
                                    self.onhold_time = self.scenario_mode.find('onhold_time').attrib['name']
                                else:
                                    self.initial_count = 0
                                    self.update_count = 0
                                    self.terminate_count = 0
                                    self.onhold_time = 0



                            self.sim_config_list.append(
                                [self.server_name, self.sim_name, self.sim_sleep_time, self.sim_lib_path,
                                 self.scenario_name, self.scenario_starter_name, self.scenario_rate_name,
                                 self.server_type, self.server_user, self.server_id, self.server_mode,
                                 self.scenario_url_name, self.stats_path_name, self.sim_product_name,
                                 self.sim_shelf_name, self.sim_assignment_name, self.sim_seq_group_name,
                                 self.scenario_url_times, self.server_prompt, self.server_key_path, self.sim_node_name,
                                 self.scenario_url_timeout, self.sim_seq_group_backup_name, self.scenario_mode_name,
                                 self.initial_count, self.update_count, self.terminate_count, self.onhold_time,
                                 self.scenario_stats_name, self.mgts_stats_name, self.mgts_stat_flag])

                            print("Entered loop %s" %self.sim_config_list)

                            """ Below variable is for GUI Purpose """
                            self.scenario_configuration_map[
                                self.server_id + ";" + self.sim_name + ";" + self.sim_product_name + ";" + self.scenario_name] = \
                            self.sim_config_list[-1]

                        """ Below variable is for GUI Purpose """
                        self.sim_prod_instance_map[
                            self.server_id + ";" + self.sim_name + ";" + self.sim_product_name] = scenarios

                    self.sim_instance_map[self.server_id + ";" + self.sim_name] = simulators

                """ Below variable is for GUI Purpose """
                self.sim_server_map[self.server_id] = [self.server_name, self.sim_name, self.sim_product_name,
                                                       self.server_type, self.server_user, self.server_id,
                                                       self.sim_sleep_time, self.sim_lib_path, self.sim_shelf_name,
                                                       self.sim_assignment_name, self.sim_seq_group_name,
                                                       self.sim_node_name, self.sim_seq_group_backup_name,
                                                       self.scenario_mode_name, self.initial_count, self.update_count,
                                                       self.terminate_count, self.onhold_time]

        print(self.sim_config_list)
        print("self.scenario_configuration_map")
        print(self.scenario_configuration_map)

        return (self)

    """ Method to capture load stats like memory, IO and so on if instances are present in the respective load server

        per_instance_stat[0]                   - ps lyef command output
        per_instance_stat[1]                   - process id print command to check product live or not
        per_instance_stat[2]                   - prstat memory command
        per_instance_stat[3]                   - date command
        self.cumulative_instances_stat.res[-5] - sar output command
        self.cumulative_instances_stat.res[-4] - load average output command
        self.cumulative_instances_stat.res[-3] - vmstat output command
        self.cumulative_instances_stat.res[-2] - iostat output command
        self.cumulative_instances_stat.res[-1] - netstat output command """

    def instance_stats_processor(self, num_of_commands, serv_num_of_commands, item):

        print("Start instance_stats_processor time:", datetime.datetime.now())
        cumulative_stats = []
        start_index = 0
        server_count =1
        local_cumulative_instance_stats = self.cumulative_instances_stat.res[:]
        """ print(local_cumulative_instance_stats) """
        iostat_delimiter = ";"
        print("Number of commands %s" %num_of_commands)
        print(self.active_product_count,num_of_commands)

        try:

            GetDockerStatsLastIndex=local_cumulative_instance_stats.index('PRSTAT_END')
            GetDockerStatsList=local_cumulative_instance_stats[0:GetDockerStatsLastIndex]
            Dockerlistlength =len(GetDockerStatsList)

            for index in range(Dockerlistlength):
                result_list = self.command_output_space_processing(GetDockerStatsList[index])
                per_instance_stat = []
                per_instance_stat.insert(0,result_list[0])
                per_instance_stat.insert(1,result_list[5])
                per_instance_stat.insert(2,[])
                per_instance_stat[2].extend([result_list[3],result_list[2],result_list[6],result_list[7],result_list[9],result_list[10],result_list[12],result_list[13],1])

                per_instance_stat.append(item[0][14])
                per_instance_stat.append(self.active_product_count[index])

                print("per_instance_stat")
                print(per_instance_stat)
                self.cumulative_stats.append(per_instance_stat)
                start_index = start_index + num_of_commands

                """ To handle server specific commands alone """
                if (index == 0):
                    self.server_date[item[0][14]] = local_cumulative_instance_stats[-6]

                    local_cumulative_instance_stats[-5] = local_cumulative_instance_stats[-5] + " " + item[0][
                        14] + " " + item[0][4]
                    self.sar_server_stats.append(local_cumulative_instance_stats[-5])
                    """ print("local_cumulative_instance_stats[-5]")
                    print(local_cumulative_instance_stats[-5]) """

                    local_cumulative_instance_stats[-4] = local_cumulative_instance_stats[-4] + " " + item[0][
                        14] + " " + item[0][4]
                    self.load_avg_server_stats.append(local_cumulative_instance_stats[-4])
                    """ print("local_cumulative_instance_stats[-4]")
                    print(local_cumulative_instance_stats[-4]) """

                    local_cumulative_instance_stats[-3] = local_cumulative_instance_stats[-3] + " " + item[0][
                        14] + " " + item[0][4]
                    self.vmstat_server_stats.append(local_cumulative_instance_stats[-3])
                    """ print("local_cumulative_instance_stats[-3]")
                    print(local_cumulative_instance_stats[-3]) """

                    local_cumulative_instance_stats[-2] = local_cumulative_instance_stats[-2] + iostat_delimiter + \
                                                          item[0][14] + iostat_delimiter + item[0][4]
                    self.iostat_server_stats.append(local_cumulative_instance_stats[-2])
                    """ print("local_cumulative_instance_stats[-2]")
                    print(local_cumulative_instance_stats[-2]) """

                    local_cumulative_instance_stats[-1] = local_cumulative_instance_stats[-1] + iostat_delimiter + \
                                                          item[0][14] + iostat_delimiter + item[0][4]
                    self.netstat_server_stats.append(local_cumulative_instance_stats[-1])
                    """ print("local_cumulative_instance_stats[-1]")
                    print(local_cumulative_instance_stats[-1]) """


        except Exception as exceptionvalue:
            print(str(exceptionvalue))
            self.cumulative_stats.insert(0, False)

        print("End instance_stats_processor time:", datetime.datetime.now())
        return self

    """ Method to capture load stats like memory, IO and so on """

    def new_memory_stats(self):

        print("Start new_memory_stats time:", datetime.datetime.now())
        self.cumulative_stats = []
        self.sar_server_stats = []
        self.load_avg_server_stats = []
        self.vmstat_server_stats = []
        self.iostat_server_stats = []
        self.netstat_server_stats = []
        self.server_date = {}

        server_id_index = 14
        product_id_index = 1
        instance_id_index = 2

        """ Used to find the current product to capture product wise statistcis """
        self.active_product_count = {}

        cmd = ""

        product_array = np.array(self.new_config_list)
#        print("product_array: %s" %product_array)

        servers = list(set(product_array[:, server_id_index]))
        print("Servers are %s" %servers)

        for server in servers:

            server_specific_details = product_array[np.where(product_array[:, server_id_index] == server)]
            cmd = ""
            self.instance_count = 0

            print("serverdetails %s" %server_specific_details)

            product_cmd=[]

            for item in server_specific_details:
                getinstcmd=[]
                getinstcmd.extend([item[18],item[2],item[8],item[10],item[4],item[0],item[5],item[19]])
                product_cmd.append(getinstcmd)
                self.active_product_count[self.instance_count] = item[2]
                self.instance_count += 1
            (num_of_commands, temp_cmd) = self.product_command_framing(product_cmd)
            cmd = cmd + temp_cmd
            
            (serv_num_of_commands, temp_cmd) = self.server_command_framing(server_specific_details[0, 4])
            cmd = cmd + temp_cmd
            """ print(cmd) """

            self.cumulative_instances_stat = self.remoteCommand(server_specific_details[0, 0], cmd,
                                                                server_specific_details[0, 5])
            del self.cumulative_instances_stat.res[-1]

            self.instance_stats_processor(num_of_commands, serv_num_of_commands, server_specific_details)

        self.instance_count = 0
        cmd = ""
        print("End new_memory_stats time:", datetime.datetime.now())
        return (self)

    """ Method to periodically monitor log files count of each instance and delete it if exceeds threshold limit """

    def log_delete_rotate(self):

        while self.load_stop_call_log_deleter_flag != 1:

            for item in self.new_config_list:

                if item[11] == "1":
                    log_delete_command = "find " + item[10] + "/* | tail -r | tail +" + item[12] + " | xargs rm"
                    self.remoteCommand(item[0], log_delete_command, item[5])

            if self.load_stop_call_log_deleter_flag != 1:
                time.sleep(float(item[13]))

        print("%d load_stop_call_log_deleter_flag" % self.load_stop_call_log_deleter_flag)
        print("Exiting from log delete")

    """ Method to create stat files """

    def stat_file_create(self, directory, t, item, file_types):

        html_dir = directory + "/" + file_types[0] + "/"
        csv_dir = directory + "/" + file_types[1] + "/"

        prod_file_desc = item[2] + "_" + item[14]
        getdockerflag = item[18]

        self.product_min_stat_file_name[prod_file_desc] = [
            self.compute_file_name(html_dir, "_LOAD_MINUTES_MEM_STATS_", prod_file_desc, t, "html"),
            self.compute_file_name(csv_dir, "_LOAD_MINUTES_MEM_STATS_", prod_file_desc, t, "csv")]
        self.product_hour_stat_file_name[prod_file_desc] = [
            self.compute_file_name(html_dir, "_LOAD_HOUR_MEM_STATS_", prod_file_desc, t, "html"),
            self.compute_file_name(csv_dir, "_LOAD_HOUR_MEM_STATS_", prod_file_desc, t, "csv")]

        if (self.server_min_sar_stat_file_name[item[14]] == "0"):

            self.server_min_sar_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_MINUTES_SAR_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_MINUTES_SAR_STATS_", item[14], t, "csv")]
            self.server_load_avg_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_AVERAGE_MINUTES_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_AVERAGE_MINUTES_STATS_", item[14], t, "csv")]
            self.server_min_vmstat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_MINUTES_VMSTAT_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_MINUTES_VMSTAT_STATS_", item[14], t, "csv")]
            self.server_min_iostat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_MINUTES_IOSTAT_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_MINUTES_IOSTAT_STATS_", item[14], t, "csv")]
            self.server_min_netstat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_MINUTES_NET_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_MINUTES_NET_STATS_", item[14], t, "csv")]

            self.server_hour_sar_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_HOUR_SAR_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_HOUR_SAR_STATS_", item[14], t, "csv")]
            self.server_hour_load_avg_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_AVERAGE_HOUR_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_AVERAGE_HOUR_STATS_", item[14], t, "csv")]
            self.server_hour_vmstat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_HOUR_VMSTAT_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_HOUR_VMSTAT_STATS_", item[14], t, "csv")]
            self.server_hour_iostat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_HOUR_IOSTAT_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_HOUR_IOSTAT_STATS_", item[14], t, "csv")]
            self.server_hour_netstat_stat_file_name[item[14]] = [
                self.compute_file_name(html_dir, "_LOAD_HOUR_NET_STATS_", item[14], t, "html"),
                self.compute_file_name(csv_dir, "_LOAD_HOUR_NET_STATS_", item[14], t, "csv")]

            with open(self.server_min_sar_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                    14] + " Minutes SAR Stats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Server</th><th>Product Server Time</th><th>%Usr</th><th>%Sys</th><th>%Wio</th><th>%Idle</th></tr></thead><tbody>")

            with open(self.server_min_sar_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("Time,Server,Product Server Time,%Usr,%Sys,%Wio,%Idle\n")

            with open(self.server_hour_sar_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                    14] + " SAR Stats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Server</th><th>Product Server Time</th><th>%Usr</th><th>%Sys</th><th>%Wio</th><th>%Idle</th></tr></thead><tbody>")

            with open(self.server_hour_sar_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("Time,Server,Product Server Time,%Usr,%Sys,%Wio,%Idle\n")

            if (item[4] in "SOLARIS"):
                with open(self.server_load_avg_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "<html><head></head><body><h2>" + self.title_name + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Server</th><th>Total Number of Processes</th><th>Total Number of lwps</th><th>Load Averages</th></tr></thead><tbody>")

                with open(self.server_load_avg_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Server,Total Number of Processes,Total Number of lwps,Load Averages\n")

                with open(self.server_hour_load_avg_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "<html><head></head><body><h2>" + self.title_name + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Server</th><th>Total Number of Processes</th><th>Total Number of lwps</th><th>Load Averages</th></tr></thead><tbody>")

                with open(self.server_hour_load_avg_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Server,Total Number of Processes,Total Number of lwps,Load Averages\n")

            with open(self.server_min_vmstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                if (item[4] in "SOLARIS"):
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes VMStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th colspan='3'>KTHR</th><th colspan='2'>MEMORY</th><th colspan='7'>Page</th><th colspan='4'>Disk</th><th colspan='3'>Faults</th><th colspan='3'>CPU</th><th>Server</th><th>Server Type</th></tr></thead>")
                    self.stat_file_obj.write(
                        "<thead><tr><td></td><td>r</td><td>b</td><td>w</td><td>swap</td><td>free</td><td>re</td><td>mf</td><td>pi</td><td>po</td><td>fr</td><td>de</td><td>sr</td><td>disk1</td><td>disk2</td><td>disk3</td><td>disk4</td><td>in</td><td>sy</td><td>cs</td><td>us</td><td>sy</td><td>id</td><td></td><td></td></tr></thead><tbody>")
                else:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes VMStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th colspan='2'>PROCS</th><th colspan='4'>MEMORY</th><th colspan='2'>SWAP</th><th colspan='2'>IO</th><th colspan='2'>SYSTEM</th><th colspan='5'>CPU</th></tr></thead>")
                    self.stat_file_obj.write(
                        "<thead><tr><td></td><td>r</td><td>b</td><td>swpd</td><td>free</td><td>buff</td><td>cache</td><td>si</td><td>so</td><td>bi</td><td>bo</td><td>in</td><td>cs</td><td>us</td><td>sy</td><td>id</td><td>wa</td><td>st</td></tr></thead><tbody>")

            with open(self.server_min_vmstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                if (item[4] in "SOLARIS"):
                    self.stat_file_obj.write(
                        "Time,,,KTHR,,MEMORY,,,,,,,Page,,,,Disk,,,Faults,,,CPU,Server,Server Type\n")
                    self.stat_file_obj.write(
                        "r,b,w,swap,free,re,mf,pi,po,fr,de,sr,disk1,disk2,disk3,disk4,in,sy,cs,us,sy,id,,\n")
                else:
                    self.stat_file_obj.write("Time,,PROCS,,,,MEMORY,,SWAP,,IO,,SYSTEM,,,,,CPU\n")
                    self.stat_file_obj.write("r,b,swpd,free,buff,cache,si,so,bi,bo,in,cs,us,sy,id,wa,st\n")

            with open(self.server_hour_vmstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                if (item[4] in "SOLARIS"):
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " VMStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th colspan='3'>KTHR</th><th colspan='2'>MEMORY</th><th colspan='7'>Page</th><th colspan='4'>Disk</th><th colspan='3'>Faults</th><th colspan='3'>CPU</th><th>Server</th><th>Server Type</th></tr></thead>")
                    self.stat_file_obj.write(
                        "<thead><tr><td></td><td>r</td><td>b</td><td>w</td><td>swap</td><td>free</td><td>re</td><td>mf</td><td>pi</td><td>po</td><td>fr</td><td>de</td><td>sr</td><td>disk1</td><td>disk2</td><td>disk3</td><td>disk4</td><td>in</td><td>sy</td><td>cs</td><td>us</td><td>sy</td><td>id</td><td></td><td></td></tr></thead><tbody>")
                else:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " VMStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th colspan='2'>PROCS</th><th colspan='4'>MEMORY</th><th colspan='2'>SWAP</th><th colspan='2'>IO</th><th colspan='2'>SYSTEM</th><th colspan='5'>CPU</th></tr></thead>")
                    self.stat_file_obj.write(
                        "<thead><tr><td></td><td>r</td><td>b</td><td>swpd</td><td>free</td><td>buff</td><td>cache</td><td>si</td><td>so</td><td>bi</td><td>bo</td><td>in</td><td>cs</td><td>us</td><td>sy</td><td>id</td><td>wa</td><td>st</td></tr></thead><tbody>")

            with open(self.server_hour_vmstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                if (item[4] in "SOLARIS"):
                    self.stat_file_obj.write("Time,,,KTHR,,MEMORY,,,,,,,Page,,,,Disk,,,Faults,,,CPU,Server\n")
                    self.stat_file_obj.write(
                        "r,b,w,swap,free,re,mf,pi,po,fr,de,sr,disk1,disk2,disk3,disk4,in,sy,cs,us,sy,id\n")
                else:
                    self.stat_file_obj.write("Time,,PROCS,,,,MEMORY,,SWAP,,IO,,SYSTEM,,,,,CPU\n")
                    self.stat_file_obj.write("r,b,swpd,free,buff,cache,si,so,bi,bo,in,cs,us,sy,id,wa,st\n")

            if (item[4] in "SOLARIS"):
                with open(self.server_min_iostat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes IOStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Disk</th><th>Mr/s</th><th>Mw/s</th><th>Service Time</th><th>Wait %</th><th>Busy %</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_min_iostat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("Time,Disk,Mr/s,Mw/s,Service Time,Wait%,Busy%,Server\n")

                with open(self.server_hour_iostat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + "IOStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Disk</th><th>Mr/s</th><th>Mw/s</th><th>Service Time</th><th>Wait %</th><th>Busy %</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_hour_iostat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("Time,Disk,Mr/s,Mw/s,Service Time,Wait%,Busy%,Server\n")

            elif (item[4] in "LINUX"):
                with open(self.server_min_iostat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes IOStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Disk</th><th>Mr/s</th><th>Mw/s</th><th>await</th><th>svctm</th><th>%util</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_min_iostat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("Time,Disk,Mr/s,Mw/s,await,svctm,%util,Server\n")

                with open(self.server_hour_iostat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + "IOStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Disk</th><th>Mr/s</th><th>Mw/s</th><th>await</th><th>svctm</th><th>%util</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_hour_iostat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("Time,Disk,Mr/s,Mw/s,await,svctm,%util,Server\n")

            if (item[4] in "SOLARIS"):
                with open(self.server_min_netstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes NetStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Name</th><th>Input Packets</th><th>Input Errors</th><th>Output Packets</th><th>Output Errors</th><th>Collisions</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_min_netstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Name,Input Packets,Input Errors,Output Packets,Output Errors,Collisions,Server\n")

                with open(self.server_hour_netstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Hourly NetStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Name</th><th>Input Packets</th><th>Input Errors</th><th>Output Packets</th><th>Output Errors</th><th>Collisions</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_hour_netstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Name,Input Packets,Input Errors,Output Packets,Output Errors,Collisions,Server\n")

            elif (item[4] in "LINUX"):
                with open(self.server_min_netstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Minutes NetStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Name</th><th>Input Packets</th><th>Input Errors</th><th>Input DRP</th><th>Input Over</th><th>Output Packets</th><th>Output Errors</th><th>Output DRP</th><th>Output Over</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_min_netstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Name,Input Packets,Input Errors,Input DPR,Input Over,Output Packets,Output Errors,Output DPR,Output Over,Server\n")

                with open(self.server_hour_netstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("<html><head></head><body><h2>" + item[
                        14] + " Hourly NetStats" + "</h2></br><table border='1'><thead><tr><th>Time</th><th>Name</th><th>Input Packets</th><th>Input Errors</th><th>Input DRP</th><th>Input Over</th><th>Output Packets</th><th>Output Errors</th><th>Output DRP</th><th>Output Over</th><th>Server</th></tr></thead><tbody>")

                with open(self.server_hour_netstat_stat_file_name[item[14]][1], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write(
                        "Time,Name,Input Packets,Input Errors,Input DPR,Input Over,Output Packets,Output Errors,Output DPR,Output Over,Server\n")

        if getdockerflag == "1":
            with open(self.product_min_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                   self.stat_file_obj.write("<html><head></head><body><h2>" + item[1] + " " + item[
                    2] + " " + "Minutes CPU Memory Utilization" + "</h2></br><table border='1'><thead><tr><th>DUT_Server_Time</th><th>Product</th><th>Container ID</th><th>Container MemLimit</th><th>Container MemUsage</th><th>Container CpuPercent</th><th>Container MemPercent</th><th>Net I/0(RX)</th><th>Net I/0(TX)</th><th>Block I/0(Read)</th><th>Block I/0(Write)</th><th>PIDs</th></tr></thead><tbody>")

            with open(self.product_min_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write(
                    "Time,Product,Container ID,Product Server Time,Container MemLimit,Container MemUsage,Container CpuPercent,Container MemPercent,Net I/0(RX),Net I/0(TX),Block I/0(Read),Block I/0(Write),PIDs\n")

            with open(self.product_hour_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                   self.stat_file_obj.write("<html><head></head><body><h2>" + item[1] + " " + item[
                    2] + " " + "CPU & Memory Utilization" + "</h2></br><table border='1'><thead><tr><th>DUT_Server_Time</th><th>Product</th><th>Container ID</th><th>Container MemLimit</th><th>Container MemUsage</th><th>Container CpuPercent</th><th>Container MemPercent</th><th>Net I/0(RX)</th><th>Net I/0(TX)</th><th>Block I/0(Read)</th><th>Block I/0(Write)</th><th>PIDs</th></tr></thead><tbody>")

            with open(self.product_hour_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write(
                    "Time,Product,Container ID,Product Server Time,Container MemLimit,Container MemUsage,Container CpuPercent,Container MemPercent,Net I/0(RX),Net I/0(TX),Block I/0(Read),Block I/0(Write),PIDs\n")

        else:
            with open(self.product_min_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("<html><head></head><body><h2>" + item[1] + " " + item[
                    2] + " " + "Minutes CPU Memory Utilization" + "</h2></br><table border='1'><thead><tr><th>DUT_Server_Time</th><th>Product</th><th>Process ID</th><th>Memory Stats(RSS;SZ)</th><th>Memory(MB)</th><th>CPU%</th></tr></thead><tbody>")

            with open(self.product_min_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write(
                    "Time,Product,Process ID,Product Server Time,Memory Stats(RSS;SZ),Summarized Memory Stats(Size),CPU%\n")

            with open(self.product_hour_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("<html><head></head><body><h2>" + item[1] + " " + item[
                    2] + " " + "CPU & Memory Utilization" + "</h2></br><table border='1'><thead><tr><th>DUT_Server_Time</th><th>Product</th><th>Process ID</th><th>Memory Stats(RSS;SZ)</th><th>Memory(MB)</th><th>CPU%</th></tr></thead><tbody>")

            with open(self.product_hour_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                self.stat_file_obj.write(
                    "Time,Product,Process ID,Product Server Time,Memory Stats(RSS;SZ),Summarized Memory Stats(Size),CPU%\n")
