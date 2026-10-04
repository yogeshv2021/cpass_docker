#!/usr/bin/python

from flaskr.application_connect import *
from flaskr.load_reporter import *
from flaskr.simulator import *

config_file = "/opt/product/LOAD/config/rrbs_config.xml"

""" Class defined to implement behaviours with respect to reading config file, getting user input, connecting to remote server and start remote applications """


class ApplicationStarter(UtilityLib, threading.Thread):
    """ Initialize configurtion and reading xml config file """

    def __init__(self, config_file):
        threading.Thread.__init__(self)
        UtilityLib.__init__(self, config_file)

        self.lock = threading.Lock()

        """ To store the optimized configuration value based on user decision """
        self.new_config_list = []

        """ Flag to indicate the load stop status. Used to kill all dedicated threads """
        self.load_stop_is_application_alive_flag = 0
        self.load_stop_call_log_deleter_flag = 0
        self.load_stop_memory_stats_flag = 0

        self.is_alive_interval = 60

        """ Dictionary to create dynamic product wise memory cpu stat file """
        self.product_min_stat_file_name = {}
        self.product_hour_stat_file_name = {}
        self.server_min_sar_stat_file_name = {}
        self.server_load_avg_stat_file_name = {}
        self.server_min_vmstat_stat_file_name = {}
        self.server_min_iostat_stat_file_name = {}
        self.server_min_netstat_stat_file_name = {}

        self.server_hour_sar_stat_file_name = {}
        self.server_hour_load_avg_stat_file_name = {}
        self.server_hour_vmstat_stat_file_name = {}
        self.server_hour_iostat_stat_file_name = {}
        self.server_hour_netstat_stat_file_name = {}

        self.start_time = time.localtime(time.time())
        self.new_config_list = []
        self.unique_server_map = {}
        self.server_name_in_prod_stats = {}

    """ Based on user decision, create a new list to store which products and instances needs to be executed currently in the load """

    def dynamic_config_decision(self):
        self.server_temp = ""
        self.prod_temp = ""
        self.new_config_list = []

        print("Do you want to proceed with above load configuration? Press y/n\n")
        self.choice = input()
        self.choice = self.choice.lower()

        if self.choice not in "y":

            print("cnglist %s" %self.config_list)

            for self.item_index in range(len(self.config_list)):

                if self.server_temp != "" and self.server_temp == self.config_list[self.item_index][0]:
                    pass

                else:
                    print("Do you want to run load in the server %s? y/n" % self.config_list[self.item_index][0])
                    self.server_choice = input()
                    self.server_choice = self.server_choice.lower()

                if (self.server_choice in "y"):

                    if self.prod_temp != "" and self.prod_temp == self.config_list[self.item_index][1]:
                        pass
                    else:
                        print(
                            "Do you want to execute load with this product %s? y/n" % self.config_list[self.item_index][
                                1])
                        self.prod_choice = input()
                        self.prod_choice = self.prod_choice.lower()

                    if self.prod_choice in "y":
                        print("Do you want to execute load with instance %s of product %s? y/n" % (
                            self.config_list[self.item_index][2], self.config_list[self.item_index][1]))
                        self.inst_choice = input()
                        self.inst_choice = self.inst_choice.lower()

                        if self.inst_choice in "y":
                            print("Instance %s selected to be executed in load" % self.config_list[self.item_index][2])
                            self.new_config_list.append(self.config_list[self.item_index])

                    self.prod_temp = self.config_list[self.item_index][1]

                self.server_temp = self.config_list[self.item_index][0]

        else:
            self.new_config_list = self.config_list

        self.config_list = []

        print("configuration loaded successfully")

        return (self)

    """ Method to kill all remote applications """

    def stop_load(self):
        for item in self.new_config_list:
            cmd = 'ps -ef | grep ' + item[2] + ' | grep -v "grep" | awk \'{print $2}\' | xargs kill -9'
            # out=self.remoteCommand(item[0],cmd,item[5])
            if item[14] in self.unique_server_map:
                self.unique_server_map[item[14]].stopApplication(cmd)
            else:
                out = self.remoteCommand(item[0], cmd, item[5])

    """ Method to close all remote connections """

    def close_ssh_connection(self):
        if len(self.unique_server_map.keys()) > 0:
            for key in self.unique_server_map.keys():
                self.unique_server_map[key].ApplicationServerDisconnect()
            self.unique_server_map = {}

    """ Method to start the load """

    def start_load(self):

        self.directory = self.stats_path_name + '/' + str(self.start_time.tm_year) + '_' + str(
            self.start_time.tm_mon).zfill(2) + '_' + str(self.start_time.tm_mday).zfill(2) + '_' + str(
            self.start_time.tm_hour).zfill(2) + '_' + str(self.start_time.tm_min).zfill(2) + '_' + str(
            self.start_time.tm_sec).zfill(2) + '/'
        self.create_directory(self.directory)
        self.create_directory(self.directory + "/html")
        self.create_directory(self.directory + "/csv")
        self.create_directory(self.directory + "/graph")
        self.create_directory(self.directory + "/seagull")
        self.create_directory(self.directory + "/sipp")
        self.create_directory(self.directory + "/mgts")
        self.create_directory(self.directory + "/appstats")
        self.create_directory(self.directory + "/loadstats")

        self.inst_restart_stat_file_name = self.directory + "/html/LOAD_INSTANCE_RESTART_" + str(
            self.start_time.tm_year) + '_' + str(self.start_time.tm_mon).zfill(2) + '_' + str(
            self.start_time.tm_mday).zfill(2) + '_' + str(self.start_time.tm_hour).zfill(2) + '_' + str(
            self.start_time.tm_min).zfill(2) + '_' + str(self.start_time.tm_sec).zfill(2) + ".html"

        with open(self.inst_restart_stat_file_name, 'a') as self.stat_file_obj:
            self.stat_file_obj.write("Instances Restarted in Load will be captured Here")

        self.hourly_mem_counter = 0

        for item in self.new_config_list:
            self.stat_file_create(self.directory, self.start_time, item, ("html", "csv"))

            item[8] = 1

            if item[14] not in self.unique_server_map:
                self.unique_server_map[item[14]] = ApplicationConnect(item[0], item[5], item[16], item[17])
                self.unique_server_map[item[14]].ApplicationServerConnect()

            cmd = item[3] + " > /dev/null 2>&1 &\n"
            self.unique_server_map[item[14]].startApplication(cmd)
            time.sleep(float(item[6]))

    """ Method to start the load """

    def monitor_load(self):

        self.directory = self.stats_path_name + '/' + str(self.start_time.tm_year) + '_' + str(
            self.start_time.tm_mon).zfill(2) + '_' + str(self.start_time.tm_mday).zfill(2) + '_' + str(
            self.start_time.tm_hour).zfill(2) + '_' + str(self.start_time.tm_min).zfill(2) + '_' + str(
            self.start_time.tm_sec).zfill(2) + '/'
        self.create_directory(self.directory)
        self.create_directory(self.directory + "/html")
        self.create_directory(self.directory + "/csv")
        self.create_directory(self.directory + "/graph")
        self.create_directory(self.directory + "/seagull")
        self.create_directory(self.directory + "/sipp")
        self.create_directory(self.directory + "/mgts")
        self.create_directory(self.directory + "/appstats")
        self.create_directory(self.directory + "/loadstats")

        self.inst_restart_stat_file_name = self.directory + "/html/LOAD_INSTANCE_RESTART_" + str(
            self.start_time.tm_year) + '_' + str(self.start_time.tm_mon).zfill(2) + '_' + str(
            self.start_time.tm_mday).zfill(2) + '_' + str(self.start_time.tm_hour).zfill(2) + '_' + str(
            self.start_time.tm_min).zfill(2) + '_' + str(self.start_time.tm_sec).zfill(2) + ".html"

        with open(self.inst_restart_stat_file_name, 'a') as self.stat_file_obj:
            self.stat_file_obj.write("Instances Restarted in Load will be captured Here")

        self.hourly_mem_counter = 0

        print(self.new_config_list)
        for item in self.new_config_list:
            self.stat_file_create(self.directory, self.start_time, item, ("html", "csv"))

            item[8] = 1

    def solaris_linux_iostat_processing(self, currtime, item):

        htm = ""
        csv = ""

        for disklist in item.split(";"):
            disklist = disklist.strip()
            if disklist and item.split(";")[-2] not in disklist and item.split(";")[-1] not in disklist:
                diskitem = disklist.split()
                diskitem.append(item.split(";")[-2])
                htm += "<tr><td>" + currtime + "</td><td>"
                csv += currtime + ","
                htm += "</td><td>".join(diskitem)
                htm += "</td></tr>"
                csv += ",".join(diskitem)
                csv += "\n"

        return (htm, csv)

    def solaris_linux_netstat_processing(self, currtime, item):

        htm = ""
        csv = ""

        for netlist in item.split(";"):
            netlist = netlist.strip()
            if netlist and item.split(";")[-2] not in netlist and item.split(";")[-1] not in netlist:
                netitem = netlist.split()
                netitem.append(item.split(";")[-2])
                htm += "<tr><td>" + currtime + "</td><td>"
                csv += currtime + ","
                htm += "</td><td>".join(netitem)
                htm += "</td></tr>"
                csv += ",".join(netitem)
                csv += "\n"

        return (htm, csv)

    """ Method to capture output of all stats like memory and server stats into respective stat output file  """

    def dynamic_stats_file_copy(self, stats_capture_obj, curr_time):

        print("Start dynamic_stats_file_copy time:", datetime.datetime.now())

        if (stats_capture_obj.cumulative_stats):

            if (stats_capture_obj.cumulative_stats[0] != False):

                try:

                    for item in stats_capture_obj.cumulative_stats:
                        prod_file_desc = item[-1] + "_" + item[-2]
                        current_server_date = stats_capture_obj.server_date[item[-2]]
                        with open(self.product_min_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                            if item[0] == "NA":
                                item[1] = item[1].replace("NA NA", "0m 0.0")
                                item[1] = item[1].replace("NA", "0m")
                                item[2] = item[2].replace("NA", "0.0")
                                self.stat_file_obj.write(
                                    "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[
                                        0] + "</td><td>" + item[0] + "</td><td>" + item[1] + "</td><td>" +
                                    item[2] + "</td></tr>")
                            else:
                                if item[2][8]==1:
                                    item[1] = item[1].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                    item[2][0] = item[2][0].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                    self.stat_file_obj.write(
                                        "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[
                                            0] + "</td><td>" + item[1] + "</td><td>" + item[2][0] + "</td><td>" 
                                         + item[2][1] + "</td><td>"  + item[2][2] + "</td><td>" + item[2][3] + "</td><td>" 
                                         + item[2][4] + "</td><td>"  +  item[2][5] + "</td><td>"  +  item[2][6] + "</td><td>" 
                                         + item[2][7] + "</td></tr>") 
                                else:
                                    self.stat_file_obj.write(
                                        "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[
                                            0] + "</td><td>" + item[1] + "</td><td>" + item[2].split()[0] + "</td><td>" +
                                        item[2].split()[1] + "</td></tr>") 


                        with open(self.product_min_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                            if item[0] == "NA":
                                item[1] = item[1].replace("NA NA", "0m 0.0")
                                item[1] = item[1].replace("NA", "0m")
                                item[2] = item[2].replace("NA", "0.0")
                                self.stat_file_obj.write(
                                    curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                        0] + "," + item[1] + "," + item[2] + "\n")
                            else:
                                if item[2][8]==1:
                                    item[1] = item[1].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                    item[2][0] = item[2][0].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                    self.stat_file_obj.write(
                                        curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                        1] + "," + item[2][0] + "," + item[2][1] + "," + item[2][2] + "," +  item[2][3] + "," +   
                                        item[2][4] + "," + item[2][5] + ","  + item[2][6] + ","  + item[2][7] +  "\n")

                                else:
                                    self.stat_file_obj.write(
                                        curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                        1] + "," + item[2].split()[0] + "," + item[2].split()[1] + "\n")


                except Exception as e:
                    print("Exception iss %s" %(str(e)))

                try:

                    for item in stats_capture_obj.sar_server_stats:
                        result_list = self.command_output_space_processing(item)

                        with open(self.server_min_sar_stat_file_name[result_list[-2]][0], 'a') as self.stat_file_obj:
                            if (result_list[-1] in "SOLARIS"):
                                self.stat_file_obj.write(
                                    "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                        0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "</td><td>" +
                                    result_list[3] + "</td><td>" + result_list[4] + "</td></tr>")
                            else:
                                self.stat_file_obj.write(
                                    "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                        0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "</td><td>" +
                                    result_list[3] + "</td><td>" + result_list[4] + "</td></tr>")

                        with open(self.server_min_sar_stat_file_name[result_list[-2]][1], 'a') as self.stat_file_obj:
                            if (result_list[-1] in "SOLARIS"):
                                self.stat_file_obj.write(
                                    curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[
                                        1] + "," + result_list[2] + "," + result_list[3] + "," + result_list[4] + "\n")
                            else:
                                self.stat_file_obj.write(
                                    curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[
                                        1] + "," + result_list[2] + "," + result_list[3] + "," + result_list[4] + "\n")

                except Exception as e:
                    print(str(e))

                try:

                    for item in stats_capture_obj.load_avg_server_stats:
                        result_list = self.command_output_space_processing(item)

                        with open(self.server_load_avg_stat_file_name[result_list[-2]][0], 'a') as self.stat_file_obj:
                            if (result_list[-1] in "SOLARIS"):
                                self.stat_file_obj.write(
                                    "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                        0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "," +
                                    result_list[3] + "," + result_list[4] + "</td></tr>")

                        with open(self.server_load_avg_stat_file_name[result_list[-2]][1], 'a') as self.stat_file_obj:
                            if (result_list[-1] in "SOLARIS"):
                                self.stat_file_obj.write(
                                    curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[
                                        1] + "," + result_list[2] + ";" + result_list[3] + ";" + result_list[4] + "\n")

                except Exception as e:
                    print(str(e))


                try:

                    for item in stats_capture_obj.vmstat_server_stats:
                        result_list = self.command_output_space_processing(item)

                        with open(self.server_min_vmstat_stat_file_name[result_list[-2]][0], 'a') as self.stat_file_obj:
                            self.stat_file_obj.write("<tr><td>" + curr_time + "</td>")
                            for result_item in result_list:
                                self.stat_file_obj.write("<td>" + result_item + "</td>")
                            self.stat_file_obj.write("</tr>")

                        with open(self.server_min_vmstat_stat_file_name[result_list[-2]][1], 'a') as self.stat_file_obj:
                            self.stat_file_obj.write(curr_time + ",")
                            for result_item in result_list:
                                self.stat_file_obj.write(result_item + ",")
                            self.stat_file_obj.write("\n")

                except Exception as e:
                    print(str(e))

                try:

                    for item in stats_capture_obj.iostat_server_stats:
                        result_list = self.command_output_split_processing(item, ";")

                        if (result_list[-1] in "SOLARIS"):

                            (htm, csv) = self.solaris_linux_iostat_processing(curr_time, item)

                            with open(self.server_min_iostat_stat_file_name[result_list[-2]][0],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(htm)

                            with open(self.server_min_iostat_stat_file_name[result_list[-2]][1],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(csv)

                        else:
                            (htm, csv) = self.solaris_linux_iostat_processing(curr_time, item)
                            with open(self.server_min_iostat_stat_file_name[result_list[-2]][0],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(htm)

                            with open(self.server_min_iostat_stat_file_name[result_list[-2]][1],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(csv)

                except Exception as e:
                    print("Exception issd %s" %(str(e)))

                try:

                    for item in stats_capture_obj.netstat_server_stats:
                        result_list = self.command_output_split_processing(item, ";")

                        if (result_list[-1] in "SOLARIS"):

                            (htm, csv) = self.solaris_linux_netstat_processing(curr_time, item)

                            with open(self.server_min_netstat_stat_file_name[result_list[-2]][0],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(htm)

                            with open(self.server_min_netstat_stat_file_name[result_list[-2]][1],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(csv)

                        else:
                            (htm, csv) = self.solaris_linux_netstat_processing(curr_time, item)

                            with open(self.server_min_netstat_stat_file_name[result_list[-2]][0],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(htm)

                            with open(self.server_min_netstat_stat_file_name[result_list[-2]][1],
                                      'a') as self.stat_file_obj:
                                self.stat_file_obj.write(csv)

                except Exception as e:
                    print(str(e))

        print("End dynamic_stats_file_copy time:", datetime.datetime.now())

    """  Method to capture hourly output of all stats like memory and server stats into respective stat output file """

    def hourly_dynamic_stats_file_copy(self, stats_capture_obj, curr_time):

        print("Start hourly_dynamic_stats_file_copy time:", datetime.datetime.now())
        if (stats_capture_obj.cumulative_stats):

            if (stats_capture_obj.cumulative_stats[0] != False):

                for item in stats_capture_obj.cumulative_stats:

                    prod_file_desc = item[-1] + "_" + item[-2]
                    current_server_date = stats_capture_obj.server_date[item[-2]]

                    with open(self.product_hour_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                        if item[-1] not in self.server_name_in_prod_stats:
                            self.server_name_in_prod_stats[item[-1]] = 1
                            self.stat_file_obj.write("<tr><td>" + item[-2] + " Stats" + "</td></tr>")

                        if item[0] == "NA":
                            item[1] = item[1].replace("NA NA", "0m 0.0")
                            item[1] = item[1].replace("NA", "0m")
                            item[2] = item[2].replace("NA", "0.0")

                            self.stat_file_obj.write(
                                "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[
                                    0] + "</td><td>" + item[0] + "</td><td>" + item[1] + "</td><td>" +
                                item[2] + "</td></tr>")
                        else:
                            if item[2][8]==1:
                                item[1] = item[1].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                item[2][0] = item[2][0].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                self.stat_file_obj.write(
                                    "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[0]
                                         + "</td><td>" + item[1] + "</td><td>" + item[2][0] + "</td><td>" 
                                         + item[2][1] + "</td><td>"  + item[2][2] + "</td><td>" + item[2][3] + "</td><td>" 
                                         + item[2][4] + "</td><td>"  +  item[2][5] + "</td><td>"  +  item[2][6] + "</td><td>" 
                                         + item[2][7] + "</td></tr>") 
                            else:
                                self.stat_file_obj.write(
                                    "<tr><td>" + current_server_date + "</td><td>" + item[-1] + "</td><td>" + item[
                                    0] + "</td><td>" + item[1] + "</td><td>" + item[2].split()[0] + "</td><td>" +
                                    item[2].split()[1] + "</td></tr>")


                    with open(self.product_hour_stat_file_name[prod_file_desc][1], 'a') as self.stat_file_obj:
                        if item[0] == "NA":
                            item[1] = item[1].replace("NA NA", "0m 0.0")
                            item[1] = item[1].replace("NA", "0m")
                            item[2] = item[2].replace("NA", "0.0")
                            self.stat_file_obj.write(
                                curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                    0] + "," + item[1] + "," + item[2] + "\n")
                        else:
                            if item[2][8]==1:
                                item[1] = item[1].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                item[2][0] = item[2][0].replace("KiB","k").replace("MiB","m").replace("GiB","g").replace("B","b")
                                self.stat_file_obj.write(
                                    curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                    1] + "," + item[2][0] + "," + item[2][1] + "," + item[2][2] + "," +  item[2][3] + ","  
                                    + item[2][4] + "," + item[2][5] + ","  + item[2][6] + ","  + item[2][7] + "\n")

                            else:
                                self.stat_file_obj.write(
                                    curr_time + "," + item[-1] + "," + item[0] + "," + current_server_date + "," + item[
                                    1] + "," + item[2].split()[0] + "," + item[2].split()[1] + "\n")


                for item in stats_capture_obj.sar_server_stats:
                    result_list = self.command_output_space_processing(item)

                    with open(self.server_hour_sar_stat_file_name[result_list[-2]][0], 'a') as self.stat_file_obj:
                        if (result_list[-1] in "SOLARIS"):
                            self.stat_file_obj.write(
                                "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                    0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "</td><td>" +
                                result_list[3] + "</td><td>" + result_list[4] + "</td></tr>")
                        else:
                            self.stat_file_obj.write(
                                "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                    0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "</td><td>" +
                                result_list[3] + "</td><td>" + result_list[4] + "</td></tr>")

                    with open(self.server_hour_sar_stat_file_name[result_list[-2]][1], 'a') as self.stat_file_obj:
                        if (result_list[-1] in "SOLARIS"):
                            self.stat_file_obj.write(
                                curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[1] + "," +
                                result_list[2] + "," + result_list[3] + "," + result_list[4] + "\n")
                        else:
                            self.stat_file_obj.write(
                                curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[1] + "," +
                                result_list[2] + "," + result_list[3] + "," + result_list[4] + "\n")

                for item in stats_capture_obj.load_avg_server_stats:
                    result_list = self.command_output_space_processing(item)

                    if (result_list[-1] in "SOLARIS"):
                        with open(self.server_hour_load_avg_stat_file_name[result_list[-2]][0],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(
                                "<tr><td>" + curr_time + "</td><td>" + result_list[-2] + "</td><td>" + result_list[
                                    0] + "</td><td>" + result_list[1] + "</td><td>" + result_list[2] + "," +
                                result_list[3] + "," + result_list[4] + "</td></tr>")

                        with open(self.server_hour_load_avg_stat_file_name[result_list[-2]][1],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(
                                curr_time + "," + result_list[-2] + "," + result_list[0] + "," + result_list[1] + "," +
                                result_list[2] + ";" + result_list[3] + ";" + result_list[4] + "\n")

                for item in stats_capture_obj.vmstat_server_stats:
                    result_list = self.command_output_space_processing(item)

                    with open(self.server_hour_vmstat_stat_file_name[result_list[-2]][0], 'a') as self.stat_file_obj:
                        self.stat_file_obj.write("<tr><td>" + curr_time + "</td>")
                        for result_item in result_list:
                            self.stat_file_obj.write("<td>" + result_item + "</td>")
                        self.stat_file_obj.write("</tr>")

                    with open(self.server_hour_vmstat_stat_file_name[result_list[-2]][1], 'a') as self.stat_file_obj:
                        self.stat_file_obj.write(curr_time + ",")
                        for result_item in result_list:
                            self.stat_file_obj.write(result_item + ",")
                        self.stat_file_obj.write("\n")

                for item in stats_capture_obj.iostat_server_stats:
                    result_list = self.command_output_split_processing(item, ";")

                    if (result_list[-1] in "SOLARIS"):

                        (htm, csv) = self.solaris_linux_iostat_processing(curr_time, item)

                        with open(self.server_hour_iostat_stat_file_name[result_list[-2]][0],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(htm)

                        with open(self.server_hour_iostat_stat_file_name[result_list[-2]][1],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(csv)

                    else:
                        (htm, csv) = self.solaris_linux_iostat_processing(curr_time, item)
                        with open(self.server_hour_iostat_stat_file_name[result_list[-2]][0],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(htm)

                        with open(self.server_hour_iostat_stat_file_name[result_list[-2]][1],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(csv)

                for item in stats_capture_obj.netstat_server_stats:
                    result_list = self.command_output_split_processing(item, ";")

                    if (result_list[-1] in "SOLARIS"):

                        (htm, csv) = self.solaris_linux_netstat_processing(curr_time, item)

                        with open(self.server_hour_netstat_stat_file_name[result_list[-2]][0],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(htm)

                        with open(self.server_hour_netstat_stat_file_name[result_list[-2]][1],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(csv)

                    else:
                        (htm, csv) = self.solaris_linux_netstat_processing(curr_time, item)

                        with open(self.server_hour_netstat_stat_file_name[result_list[-2]][0],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(htm)

                        with open(self.server_hour_netstat_stat_file_name[result_list[-2]][1],
                                  'a') as self.stat_file_obj:
                            self.stat_file_obj.write(csv)
        print("End hourly_dynamic_stats_file_copy time:", datetime.datetime.now())

    """ Method to check whether application is live or not """

    def is_application_alive(self, curr_time):
        self.prod_live_statuses = []

        for item in self.new_config_list:
            cmd = 'ps -ef | grep -w ' + item[2] + ' | grep -v "grep" | awk \'{print $2}\''
            app_status = self.remoteCommand(item[0], cmd, item[5])
            if app_status.res[0]:
                item[8] = app_status.res[0]
            else:
                item[8] = 0
                with open(self.inst_restart_stat_file_name, 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("\nInstance %s Restarted in Load at %s\n" % (item[2], curr_time))

                if (self.load_current_restart_count <= int(self.load_restart_count_name)):

                    if item[14] in self.unique_server_map:
                        cmd = item[3] + " &"
                        self.unique_server_map[item[14]].startApplication(cmd)

                    """ self.remoteConnect(item[0],item[3],item[5]) """
                    time.sleep(float(item[6]))
                    self.load_current_restart_count += 1

        return (self)

    """ Method to check whether application is live or not """

    def new_is_application_alive(self, curr_time):

        print("Start new_is_application_alive time:", datetime.datetime.now())
        server_id_index = 14
        product_id_index = 1
        instance_id_index = 2

        """ Used to find the current product to capture product wise statistcis """
        self.active_product_count = {}

        cmd = ""
        getcmdout = ""
        app_status = ""

        product_array = np.array(self.new_config_list)

        servers = list(set(product_array[:, server_id_index]))

        for server in servers:

            server_specific_details = product_array[np.where(product_array[:, server_id_index] == server)]

            product_indices = np.where(product_array[:, server_id_index] == server)
            cmd = ""
            count = 0

            for item in server_specific_details:
                # cmd=cmd+'ps -ef | grep -w '+item[2]+' | grep -v "grep" | awk \'{print $2}\';echo END;'
                if item[18]=="1":
                    cmd = cmd + 'docker ps | grep ' + item[2]+ ' | head -1 ;echo END;'
                else:
                    cmd = cmd + 'pgrep ' + item[2] + '| head -1;echo END;'

            """ print(cmd) """

            app_status = self.remoteCommand(server_specific_details[0, 0], cmd, server_specific_details[0, 5])

            print("app_indices %s" %app_status.res)

            del app_status.res[-1]

            """ print(app_status.res) """

            if (app_status.res):

                for i in range(len(app_status.res)):

                    if (i == 0):

                        if app_status.res[i] != "END":
                            self.new_config_list[product_indices[0][count]][8] = app_status.res[i]
                            count += 1

                        elif app_status.res[i] == "END":
                            print("issue at index %d" % i)
                            count = self.restart_process(product_indices, count, curr_time)

                    else:

                        if app_status.res[i - 1] == "END" and app_status.res[i] != "END":
                            self.new_config_list[product_indices[0][count]][8] = app_status.res[i]
                            count += 1

                        elif app_status.res[i - 1] == "END" and app_status.res[i] == "END":
                            print("issue at index %d" % i)
                            count = self.restart_process(product_indices, count, curr_time)

                        elif app_status.res[i - 1] != "END" and app_status.res[i] == "END":
#                            print("issue at index %d" % i)
#                            count = self.restart_process(product_indices, count, curr_time)
                            pass


        cmd = ""
        print("End new_is_application_alive time:", datetime.datetime.now())
        return (self)

    def restart_process(self, product_indices, count, curr_time):

        self.new_config_list[product_indices[0][count]][8] = '0'
        with open(self.inst_restart_stat_file_name, 'a') as self.stat_file_obj:
            self.stat_file_obj.write("\nInstance %s Restarted in Load at %s\n" % (
                self.new_config_list[product_indices[0][count]][2], curr_time))

        if (self.load_current_restart_count <= int(self.load_restart_count_name)):

            if self.new_config_list[product_indices[0][count]][14] in self.unique_server_map:
                cmd = self.new_config_list[product_indices[0][count]][3] + " &"
                self.unique_server_map[self.new_config_list[product_indices[0][count]][14]].startApplication(cmd)

        time.sleep(float(self.new_config_list[product_indices[0][count]][6]))
        self.load_current_restart_count += 1
        count += 1

        return (count)

    def active_processes(self):

        resp = ""
        for item in self.new_config_list:
            resp += "Process ID of instance <b>" + item[2] + "</b> running in Server <b>" + item[14] + "</b> is <b>" + \
                    item[8] + "</b></br>"
        return (resp)

    """ Thread function to execute threading related activities Is Application Alive Check and Memory Capture Stats. 
        Function will throw exception if product name is not at the last index of item list array """

    def run(self):

        self.step_count = 0
        self.zero_hour_count = 0
        self.stats_start_time = datetime.datetime.now()
        self.stats_end_time = datetime.datetime.now()
        self.stats_time_diff = 0
        self.statsfromfile = 1

        """ Execute this thread Until Load is Stopped """
        while self.load_stop_memory_stats_flag != 1:

            time.sleep(float(self.stats_dur_name))
            self.stats_end_time = datetime.datetime.now()
            print("Start Capture after timeout time:", datetime.datetime.now())
            print("hourly_counter:", self.hourly_mem_counter)

            if self.load_stop_memory_stats_flag != 1:

                """ Time to capture current time in stats """
                t = time.localtime(time.time())
                curr_time = str(t.tm_year) + '/' + str(t.tm_mon).zfill(2) + '/' + str(t.tm_mday).zfill(2) + ' ' + str(
                    t.tm_hour).zfill(2) + ':' + str(t.tm_min).zfill(2) + ':' + str(t.tm_sec).zfill(2)

                print("Start Remote stats capture called on time:", datetime.datetime.now())
                stats_capture_obj = self.new_memory_stats()
                print("test1 %s" %stats_capture_obj.cumulative_stats)
                if stats_capture_obj.cumulative_stats != []:
                    if (stats_capture_obj.cumulative_stats[0] == False):
                        print("Stats Capture failed recapturing one more time")
                        stats_capture_obj = self.new_memory_stats()

                    print("End Remote stats capture time:", datetime.datetime.now())

                    print("Start Dynamic stats writing called on time:", datetime.datetime.now())
                    self.dynamic_stats_file_copy(stats_capture_obj, curr_time)
                    print("End Dynamic stats writing called on time:", datetime.datetime.now())
                    self.stats_time_diff = self.stats_end_time - self.stats_start_time
                    self.hourly_mem_counter = int(self.stats_time_diff.total_seconds() / 60)
                    print("Time diff:", self.stats_time_diff)

                    if (
                        self.hourly_mem_counter >= 60 or self.zero_hour_count == 0 or self.stats_start_time.date() != self.stats_end_time.date()):
                        print("Start Hourly stats writing called on time:", datetime.datetime.now())
                        self.hourly_mem_counter = 0
                        self.stats_start_time = self.stats_end_time
                        self.zero_hour_count += int(self.stats_dur_name)
                        self.hourly_dynamic_stats_file_copy(stats_capture_obj, curr_time)
                        print("End Hourly stats writing called on time:", datetime.datetime.now())

                    print("End Capture after timeout time:", datetime.datetime.now())

        self.load_stop_memory_stats_flag = 0

        print("Exiting from memory stats thread")


class ApplicationStopper(UtilityLib, threading.Thread):
    def __init__(self, app_starter):
        threading.Thread.__init__(self)
        self.app_starter = app_starter
        self.stop_choice = "entry"

    def stop(self):
        print("Good Bye!")
        self.app_starter.load_stop_is_application_alive_flag = 1
        self.app_starter.load_stop_call_log_deleter_flag = 1
        self.app_starter.load_stop_memory_stats_flag = 1
        self.app_starter.stop_load()
        self.app_starter.close_ssh_connection()

        for item in self.app_starter.new_config_list:

            print(item)

            prod_file_desc = item[2] + "_" + item[14]
            with open(self.app_starter.product_min_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("</table></body></html>")

            with open(self.app_starter.product_hour_stat_file_name[prod_file_desc][0], 'a') as self.stat_file_obj:
                self.stat_file_obj.write("</table></body></html>")

            if (self.app_starter.server_min_sar_stat_file_name[item[14]] != "0"):

                print("Stop write stats : %s" % self.app_starter.server_min_sar_stat_file_name[item[14]])

                with open(self.app_starter.server_min_sar_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("</table></body></html>")

                with open(self.app_starter.server_hour_sar_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("</table></body></html>")

                if (item[4] in "SOLARIS"):
                    with open(self.app_starter.server_load_avg_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                    with open(self.app_starter.server_hour_load_avg_stat_file_name[item[14]][0],
                              'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                with open(self.app_starter.server_min_vmstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("</table></body></html>")

                with open(self.app_starter.server_hour_vmstat_stat_file_name[item[14]][0], 'a') as self.stat_file_obj:
                    self.stat_file_obj.write("</table></body></html>")

                if (item[4] in "SOLARIS"):
                    with open(self.app_starter.server_min_iostat_stat_file_name[item[14]][0],
                              'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                    with open(self.app_starter.server_hour_iostat_stat_file_name[item[14]][0],
                              'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                if (item[4] in "SOLARIS"):
                    with open(self.app_starter.server_min_netstat_stat_file_name[item[14]][0],
                              'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                    with open(self.app_starter.server_hour_netstat_stat_file_name[item[14]][0],
                              'a') as self.stat_file_obj:
                        self.stat_file_obj.write("</table></body></html>")

                self.app_starter.server_min_sar_stat_file_name[item[14]] = "0"
                self.app_starter.server_load_avg_stat_file_name[item[14]] = "0"
                self.app_starter.server_min_vmstat_stat_file_name[item[14]] = "0"

        self.stop_choice = "entry"
        time.sleep(5)

    def run(self):
        while True:

            if self.stop_choice in "exit":
                self.stop()
                break
            else:
                pass
        print("Exiting from stop main")
        return


def call_log_deleter(app_start):
    while app_start.load_stop_call_log_deleter_flag != 1:
        if (len(app_start.new_config_list) > 0):
            app_start.log_delete_rotate()

    app_start.load_stop_call_log_deleter_flag = 0


def app_live_check(app_start):
    app_start.load_current_restart_count = 0
    while app_start.load_stop_is_application_alive_flag != 1:
        if (len(app_start.new_config_list) > 0):
            t = time.localtime(time.time())
            curr_time = str(t.tm_year) + '/' + str(t.tm_mon).zfill(2) + '/' + str(t.tm_mday).zfill(2) + ' ' + str(
                t.tm_hour).zfill(2) + ':' + str(t.tm_min).zfill(2) + ':' + str(t.tm_sec).zfill(2)
            app_start.new_is_application_alive(curr_time)
            time.sleep(float(app_start.is_alive_interval))

    app_start.load_stop_is_application_alive_flag = 0


load_choice = 0
exit_choice = 7

if __name__ == "__main__":

    print(config_file)
    app_starter = ApplicationStarter(config_file)
    sim_starter = SimulatorStarter(config_file, app_starter.start_time)
    app_stopper = ApplicationStopper(app_starter)
    load_reporter = LoadReporter()

    while (load_choice != exit_choice):

        print(
            "\n1. Product Selection\n2. Simulator Selection\n3. Bringing Selected Applications\n4. Simulating Traffic from Simulator\n5. Stop entire load\n6. Prepare Load Report \n7. Exit\n")

        try:

            load_choice = int(input("Enter your choice : "))

            if (load_choice == 1):

                app_starter = app_starter.config_read()

                app_starter = app_starter.dynamic_config_decision()

            elif (load_choice == 2):

                sim_starter = sim_starter.simulator_config_read()

                sim_starter = sim_starter.dynamic_simulator_config_decision()

            elif (load_choice == 3):

                print("\nstarting DUT server applications...Please wait...\n")

                app_starter.stop_load()

                app_starter.start_load()

                """ initiate thread of application starter calss """
                app_starter.daemon = True
                app_starter.start()

                """ invoke dynamic log deleter thread """
                t1 = threading.Thread(target=call_log_deleter, args=(app_starter,))
                t1.daemon = True
                t1.start()

                """ invoke app live check thread """
                t2 = threading.Thread(target=app_live_check, args=(app_starter,))
                t2.daemon = True
                t2.start()

                """ invoke thread to monitor exit status of load """
                app_stopper.start()


            elif (load_choice == 4):

                sim_starter.simulator_choice_list()

            elif (load_choice == 5):
                app_stopper.stop_choice = "exit"

            elif (load_choice == 6):
                prepared = input("Load Report Prepared by : ")
                reviewed = input("Load Report Reviewed by : ")
                approved = input("Load Report Approved by : ")
                load_start_date = input("Load Execution Date : ")
                load_report_date = input("Load Report Preparation Date : ")
                load_stats_base_path = app_starter.root.find('stats_path').attrib['name']

                stats_dir = os.listdir(load_stats_base_path)
                stats_dir = sorted(stats_dir, reverse=True)

                print("\nLatest 10 Load Stats Directory are here : \n")
                n = 10
                if (len(stats_dir) < 10):
                    n = len(stats_dir)
                for i in range(n):
                    print(stats_dir[i])

                load_stats_path = input("\nEnter Load Stats Directory Name : ")
                load_stats_path = load_stats_base_path + "/" + load_stats_path
                print(load_stats_path)
                load_reporter.prepare_report(prepared, reviewed, approved, load_start_date, load_report_date,
                                             load_stats_path)


            elif (load_choice == exit_choice):
                app_stopper.stop_choice = "exit"

            else:
                print("\n Invalid Entry")

        except ValueError:
            print("Invalid Entry")

        except KeyboardInterrupt:
            print("Keyboard Interrupted the script")
            exit()
