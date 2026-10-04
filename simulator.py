#!/usr/bin/python

from flaskr.mgts.mgts_simulator import *
from flaskr.seagull.seagull_simulator import *
from flaskr.sippy.sippy_simulator import *

SEAGULL_SIMULATOR = "SEAGULL"

SIPPY_SIMULATOR = "SIPPY"

MGTS_SIMULATOR = "MGTS"

EXIT_CHOICE = 15

localip = socket.gethostbyname(socket.gethostname())


class SimulatorStarter(UtilityLib, threading.Thread):
    """ Initialize configurtion and reading xml config file """

    def __init__(self, config_file, start_time):
        threading.Thread.__init__(self)
        UtilityLib.__init__(self, config_file)

        """ To store the optimized configuration value based on user decision """
        self.new_sim_config_list = []

        self.is_alive_interval = 5
        self.load_sim_stop_is_application_alive_flag = 0
        self.scenario_map = {}
        self.scen_choice_map = {}
        self.scen_choice_list = []
        self.time_stats = str(start_time.tm_year) + '_' + str(start_time.tm_mon).zfill(2) + '_' + str(
            start_time.tm_mday).zfill(2) + '_' + str(start_time.tm_hour).zfill(2) + '_' + str(start_time.tm_min).zfill(
            2) + '_' + str(start_time.tm_sec).zfill(2)

    """ Based on user decision, create a new list to store which simulators and scenarios needs to be executed currently in the load """

    def dynamic_simulator_config_decision(self):
        self.server_temp = ""
        self.sim_temp = ""
        self.sim_product_temp = ""
        self.new_sim_config_list = []

        if self.sim_choice not in "y":

            for self.item_index in range(len(self.sim_config_list)):

                if self.server_temp != "" and self.server_temp == self.sim_config_list[self.item_index][0]:
                    pass

                else:
                    print("Do you want to run load in the server %s? y/n" % self.sim_config_list[self.item_index][0])
                    self.server_choice = input()
                    self.server_choice = self.server_choice.lower()

                if (self.server_choice in "y"):

                    if self.sim_temp != "" and self.sim_temp == self.sim_config_list[self.item_index][1]:
                        pass
                    else:
                        print("Do you want to execute load with this simulator %s? y/n" %
                              self.sim_config_list[self.item_index][1])
                        self.sim_choice = input()
                        self.sim_choice = self.sim_choice.lower()

                    if self.sim_choice in "y":

                        if self.sim_product_temp != "" and self.sim_product_temp == \
                                self.sim_config_list[self.item_index][13]:
                            pass
                        else:
                            print("Do you want to execute load for the product %s with the simulator? y/n" %
                                  self.sim_config_list[self.item_index][13])
                            self.sim_prod_choice = input()
                            self.sim_prod_choice = self.sim_prod_choice.lower()

                        if (self.sim_prod_choice in "y"):
                            print("Do you want to execute load with scenario %s of simulator %s? y/n" % (
                                self.sim_config_list[self.item_index][4], self.sim_config_list[self.item_index][1]))
                            self.scen_choice = input()
                            self.scen_choice = self.scen_choice.lower()

                            if self.scen_choice in "y":
                                print("Scenario %s selected to be executed in load" %
                                      self.sim_config_list[self.item_index][4])
                                self.new_sim_config_list.append(self.sim_config_list[self.item_index][:])

                            self.sim_product_temp = self.sim_config_list[self.item_index][13]

                        self.sim_temp = self.sim_config_list[self.item_index][1]

                self.server_temp = self.sim_config_list[self.item_index][0]

        else:
            self.new_sim_config_list = self.sim_config_list

        self.sim_config_list = []

        print("configuration loaded successfully")

        return (self)

    """method to invoke respective simultors to initiate traffic"""

    def simulator_starter(self, app_path):

        print("Entering Simulator Starter")
        self.result_flag = True

        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_simulator_starter(item, app_path)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to set call rate for each type of simulator scenarios started"""

    def simulator_set_call_rate(self):

        self.result_flag = True
        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_set_call_rate(item)
            if not self.result:
                self.result_flag = False

        MGTSSimulator.unique_mgts_sequence_group_map = {}
        return self.result_flag

    """method to pause the load for each type of simulator scenarios started"""

    def simulator_pause(self):

        self.result_flag = True
        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_pause(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to restart the load for each type of simulator scenarios started"""

    def simulator_restart(self):

        self.result_flag = True
        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_restart(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to stop the load for each type of simulator scenarios started"""

    def simulator_stop(self):

        self.result_flag = True
        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_stop(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to get the load stats for each type of simulator scenarios started"""

    def simulator_get_stats(self):

        self.result = ""
        self.copy_flag = True
        print("in simulator get stats")

        for item in self.new_sim_config_list:
            print(item)
            self.result += self.simulator_categorize_get_stats(item)
            if item[1] == MGTS_SIMULATOR and item[30] == '1':
                if self.copy_flag:
                    print(item[15])
                    self.mgts_assignment_name = item[15]

                if self.mgts_assignment_name == item[15]:
                    print("Same MGTS Assignment")
                    self.copy_flag = False
                else:
                    print("MGTS Assignment Changed")
                    self.copy_flag = True
            self.result += "\n"

        return self.result

    """method to write the load stats into stats file for each type of simulator scenarios started"""

    def simulator_write_stats(self, stats_from_file_type):

        self.result_flag = True
        self.copy_flag = True
        curr_time_stats = self.simulator_create_stats()
        for item in self.new_sim_config_list:
            self.result = self.simulator_categorize_write_stats(item, curr_time_stats, stats_from_file_type)
            if item[1] == MGTS_SIMULATOR and item[30] == '1':
                if self.copy_flag:
                    print(item[15])
                    self.mgts_assignment_name = item[15]

                if self.mgts_assignment_name == item[15]:
                    print("Same MGTS Assignment")
                    self.copy_flag = False
                else:
                    print("MGTS Assignment Changed")
                    self.copy_flag = True

            if not self.result:
                self.result_flag = False

        """ self.simulator_close_stats(curr_time_stats) """

        return self.result

    """method to monitor the load stats into stats file for each type of simulator scenarios on regular intervals"""

    def simulator_monitoring_stats(self, stats_from_file_type):

        print("simulator_monitoring_stats start")
        self.result_flag = True
        curr_time_stats = self.simulator_stats_monitor()
        print(self.new_sim_config_list)
        for item in self.new_sim_config_list:
            print("Inside for loop")
            self.result = self.simulator_monitor_write_stats(item, curr_time_stats, stats_from_file_type)
            if not self.result:
                self.result_flag = False

        """ self.simulator_close_stats(curr_time_stats) """
        print("simulator_monitoring_stats end")
        #return self.result

    """method to set call rate for a single specific scenario"""

    def simulator_item_set_call_rate(self, item):

        self.result = self.simulator_categorize_set_call_rate(item)

        MGTSSimulator.unique_mgts_sequence_group_map = {}

        return self.result

    """method to pause load for a single specific scenario"""

    def simulator_item_pause(self, item):

        self.result = self.simulator_categorize_pause(item)

        return self.result

    """method to restart load for a single specific scenario"""

    def simulator_item_restart(self, item):

        self.result = self.simulator_categorize_restart(item)

        return self.result

    """method to stop load for a single specific scenario"""

    def simulator_item_stop(self, item):

        self.result = self.simulator_categorize_stop(item)

        return self.result

    """method to get the load stats for each type of simulator scenarios started"""

    def simulator_item_get_stats(self, item):

        self.result = self.simulator_categorize_get_stats(item)

        return self.result

    """method to invoke respective simultors to initiate traffic"""

    def simulator_item_starter(self, item, app_path):

        self.result = self.simulator_categorize_simulator_starter(item, app_path)
        return self.result

    """method to invoke respective simultors to initiate traffic"""

    def simulator_items_starter(self, items, app_path):

        print("Entering Simulator Starter")
        self.result_flag = True

        for item in items:
            self.result = self.simulator_categorize_simulator_starter(item, app_path)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to set call rate for each type of simulator scenarios started"""

    def simulator_items_set_call_rate(self, items):

        self.result_flag = True

        for item in items:
            self.result = self.simulator_categorize_set_call_rate(item)
            if not self.result:
                self.result_flag = False

        MGTSSimulator.unique_mgts_sequence_group_map = {}

        return self.result_flag

    """method to pause the load for each type of simulator scenarios started"""

    def simulator_items_pause(self, items):

        self.result_flag = True

        for item in items:
            self.result = self.simulator_categorize_pause(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to restart the load for each type of simulator scenarios started"""

    def simulator_items_restart(self, items):

        self.result_flag = True

        for item in items:
            self.result = self.simulator_categorize_restart(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to stop the load for each type of simulator scenarios started"""

    def simulator_items_stop(self, items):

        self.result_flag = True

        for item in items:
            self.result = self.simulator_categorize_stop(item)
            if not self.result:
                self.result_flag = False

        return self.result_flag

    """method to get the load stats for each type of simulator scenarios started"""

    def simulator_items_get_stats(self, items):

        self.result = ""

        for item in items:
            self.result += self.simulator_categorize_get_stats(item)
            self.result += "\n"

        return self.result

    """ method to bring up each simulator for each scenario """

    def simulator_categorize_simulator_starter(self, item, app_path):
        try:

            if item[1] == SEAGULL_SIMULATOR:
                seagull_sim = SeagullSimulator()
                seagull_sim.seagullScriptStart(item[4], item[11], item[5], item[8], item[3], app_path)
                self.scenario_map[item[4]] = item
                del seagull_sim

            elif item[1] == MGTS_SIMULATOR:

                """ to connect to MGTS Server only once and retain the connection till stopping the load """
                if item[8] not in MGTSSimulator.unique_mgts_server_map:
                    MGTSSimulator.unique_mgts_server_map[item[8]] = MGTSSimulator(item[0], item[8], item[19], item[18])
                    MGTSSimulator.unique_mgts_assignment_shelf_map[item[15]] = item[14] + ";" + item[8]
                    MGTSSimulator.unique_mgts_server_map[item[8]].MGTSServerConnect()
                    print("connected to MGTS Server\n")
                    print(MGTSSimulator.unique_mgts_server_map)

                MGTSSimulator.unique_mgts_server_map[item[8]].MGTSSimulatorStarter(item[5], item[11], item[14],
                                                                                   item[15], item[17], item[18],
                                                                                   item[20], item[21], item[3])


            elif item[1] == SIPPY_SIMULATOR:
                sippy_sim = SippySimulator()
                sippy_sim.sippyScriptStart(item[4], item[11], item[5], item[8], item[3], app_path)
                self.scenario_map[item[4]] = item
                del sippy_sim

            return True

        except Exception as e:
            print(str(e))
            return False

    def simulator_categorize_pause(self, item):

        if item[1] == SEAGULL_SIMULATOR:
            seagull_sim = SeagullSimulator()
            seagull_sim.loadPause(item[4], item[11])
            del seagull_sim

        elif item[1] == MGTS_SIMULATOR:

            if item[8] in MGTSSimulator.unique_mgts_server_map and item[15] in MGTSSimulator.unique_mgts_assignment_map:
                MGTSSimulator.unique_mgts_server_map[item[8]].MGTSScenarioStop(item[14], item[15], item[20], item[5])

        elif item[1] == SIPPY_SIMULATOR:
            sippy_sim = SippySimulator()
            sippy_sim.loadPause(item[4], item[11])
            del sippy_sim

        return True

    def simulator_categorize_restart(self, item):

        if item[1] == SEAGULL_SIMULATOR:
            seagull_sim = SeagullSimulator()
            seagull_sim.loadPause(item[4], item[11])
            del seagull_sim

        elif item[1] == MGTS_SIMULATOR:
            if item[8] in MGTSSimulator.unique_mgts_server_map and item[15] in MGTSSimulator.unique_mgts_assignment_map:
                MGTSSimulator.unique_mgts_server_map[item[8]].MGTSSimulatorStarter(item[5], item[11], item[14],
                                                                                   item[15], item[17], item[18],
                                                                                   item[20], item[21])

        elif item[1] == SIPPY_SIMULATOR:
            sippy_sim = SippySimulator()
            sippy_sim.loadPause(item[4], item[11])
            del sippy_sim

        return True

    def simulator_categorize_set_call_rate(self, item):

        print(item)

        if item[1] == SEAGULL_SIMULATOR:
            seagull_sim = SeagullSimulator()
            seagull_sim.loadStart(item[4], item[11], item[6])
            print("exiting from sim cat set call rate")
            del seagull_sim

        elif item[1] == MGTS_SIMULATOR:
            mgts_sim = MGTSSimulator(item[0], item[8], item[19], item[18])
            mgts_sim.MGTSServerConnect()
            mgts_sim.MGTSSetCallRate(item[5], item[4], item[16], item[6], item[22])
            mgts_sim.MGTSCallRateCopy()
            mgts_sim.MGTSServerDisconnect()
            del mgts_sim

        elif item[1] == SIPPY_SIMULATOR:
            sippy_sim = SippySimulator()
            sippy_sim.loadStart(item[4], item[11], item[6])
            print("exiting from sim cat set call rate")
            del sippy_sim

        return True

    def simulator_categorize_stop(self, item):

        self.directory = item[12] + '/' + self.time_stats + '/'
        if item[1] == SEAGULL_SIMULATOR:
            seagull_sim = SeagullSimulator()
            seagull_sim.loadStop(item[4], item[11])
            del seagull_sim

        elif item[1] == MGTS_SIMULATOR:

            if item[8] in MGTSSimulator.unique_mgts_server_map and item[15] in MGTSSimulator.unique_mgts_assignment_map:
                MGTSSimulator.unique_mgts_server_map[item[8]].MGTSScenarioStop(item[14], item[15], item[20], item[5])

        elif item[1] == SIPPY_SIMULATOR:
            sippy_sim = SippySimulator()
            sippy_sim.loadStop(item[4], item[11])
            del sippy_sim

        return True

    """method to capture stats on GUI"""
    def simulator_categorize_get_stats(self, item):

        result = ""
        self.directory = item[12] + '/' + self.time_stats + '/'
        if item[1] == SEAGULL_SIMULATOR:
            seagull_sim = SeagullSimulator()
            result = seagull_sim.loadStats(item[4], item[11], item[6], item[23], item[24], item[25], item[26], item[27],
                                           0, 0)
            del seagull_sim

        elif item[1] == MGTS_SIMULATOR:

            self.mgtsdir = self.directory + "mgts/"
            self.mgtsip = item[0]
            self.mgtsfile = item[29]
            self.mgtsuser = item[8]
            head,tail=os.path.split(item[29])
            self.mgtsstatsfile=self.mgtsdir + tail
            print(self.mgtsstatsfile)
            if item[30] == '1' and self.copy_flag==True:
                self.copy_mgts_stats_file(self.mgtsip, self.mgtsuser, self.mgtsfile, self.mgtsdir)

            try:
                if item[30] == '0':
                    if item[8] in MGTSSimulator.unique_mgts_server_map and item[15] in MGTSSimulator.unique_mgts_assignment_map:
                        result = MGTSSimulator.unique_mgts_server_map[item[8]].MGTSScenarioStats(item[14], item[15], item[20],
                                                                                                 item[5], item[4], 0, item[6],
                                                                                                 item[23], item[24], item[25],
                                                                                                 item[26], item[27], 0)

                if item[30] == '1':
                    if os.path.exists(self.mgtsstatsfile):
                        result=MGTSSimulator.MGTSScenariofileStats(self,item[5],item[4],self.mgtsstatsfile,0,item[6],0)
                        print(result)

            except Exception as e:
                print(str(e))


        elif item[1] == SIPPY_SIMULATOR:
            sippy_sim = SippySimulator()
            result = sippy_sim.loadStats(item[4], item[5], item[11], item[8], item[6], item[23], item[24], item[25],
                                         item[26], item[27], 0, 0)
            del sippy_sim

        return result

    """method to capture stats on file for reporting"""
    def simulator_create_stats(self):

        curr_time = time.localtime(time.time())
        curr_time_stats = str(curr_time.tm_year) + '_' + str(curr_time.tm_mon).zfill(2) + '_' + str(
            curr_time.tm_mday).zfill(2) + '_' + str(curr_time.tm_hour).zfill(2) + '_' + str(curr_time.tm_min).zfill(
            2) + '_' + str(curr_time.tm_sec).zfill(2)

        for item in self.new_sim_config_list:

            self.directory = item[12] + '/' + self.time_stats + '/'
            self.create_directory(self.directory)
            self.create_directory(self.directory + "/html")
            self.create_directory(self.directory + "/csv")
            self.create_directory(self.directory + "/graph")
            self.create_directory(self.directory + "/seagull")
            self.create_directory(self.directory + "/sipp")
            self.create_directory(self.directory + "/mgts")
            self.create_directory(self.directory + "/appstats")
            self.create_directory(self.directory + "/loadstats")

            stats_file = self.directory + "/html/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".html"
            csv_stats_file = self.directory + "/csv/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".csv"

            if item[1] == SEAGULL_SIMULATOR:

                if item[23] == "STATEFULL":

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption><thead><tr><th>Scenario</th><th>Ini/Sec</th><th>Upd/Sec</th><th>Ter/Sec</th><th>Tot_Tps/Sec</th><th>On_Hold_Sessions</th><th>In_Req</th><th>Out_Req</th><th>Success</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,Total TPS/Sec,On-Hold Sessions,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

                else:

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption></b></caption><thead><tr><th>Scenario</th><th>Req/Sec</th><th>Inc_Req</th><th>Out_Req</th><th>Successsful</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Requests/Sec,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

            elif item[1] == MGTS_SIMULATOR:

                if item[23] == "STATEFULL":

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption></b></caption><thead><tr><th>Scenario</th><th>Ini/Sec</th><th>Upd/Sec</th><th>Ter/Sec</th><th>Tot_Tps/Sec</th><th>On_Hold_Sessions</th><th>In_Req</th><th>Out_Req</th><th>Success</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,Total Req/sec,On-Hold Sessions,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

                else:

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption></b></caption><thead><tr><th>Scenario</th><th>Req/Sec</th><th>Inc_Req</th><th>Out_Req</th><th>Successs</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Requests/Sec,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

            elif item[1] == SIPPY_SIMULATOR:

                if item[23] == "STATEFULL":

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption></b></caption><thead><tr><th>Scenario</th><th>Ini/Sec</th><th>Upd/Sec</th><th>Ter/Sec</th><th>Tot_Tps/Sec</th><th>On_Hold_Sessions</th><th>In_Req</th><th>Out_Req</th><th>Success</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,On-Hold Sessions,Total Calls,Successsful Calls,% of success\n")

                else:

                    with open(stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("<html><head><title>" + item[
                            13] + "</title></head><body><table border='1'><caption><u><b>" + item[
                                                    13] + "_Scenario_Results</b></u></br></caption></b></caption><thead><tr><th>Scenario</th><th>Req/Sec</th><th>Total</th><th>Successs</th><th>%_Of_Success</th></tr></thead><tbody>")

                    with open(csv_stats_file, 'w') as stats_file_writer:
                        stats_file_writer.write("Scenario,Requests/Sec,Total Calls,Successsful Calls,% of success\n")

        return curr_time_stats

    """method to monitor and capture stats on statistics on regular intervels"""
    def simulator_stats_monitor(self):

        print("simulator_stats_monitor start")
        curr_time = time.localtime(time.time())
        curr_time_stats = str(curr_time.tm_year) + '_' + str(curr_time.tm_mon).zfill(2) + '_' + str(
            curr_time.tm_mday).zfill(2) + '_' + str(curr_time.tm_hour).zfill(2) + '_' + str(curr_time.tm_min).zfill(
            2) + '_' + str(curr_time.tm_sec).zfill(2)

        for item in self.new_sim_config_list:

            print("Inside simulator_stats_monitor for loop")
            self.directory = item[12] + '/' + self.time_stats + '/'
            self.create_directory(self.directory)
            self.create_directory(self.directory + "/html")
            self.create_directory(self.directory + "/csv")
            self.create_directory(self.directory + "/graph")
            self.create_directory(self.directory + "/seagull")
            self.create_directory(self.directory + "/sipp")
            self.create_directory(self.directory + "/mgts")
            self.create_directory(self.directory + "/appstats")
            self.create_directory(self.directory + "/loadstats")

            csv_stats_file = self.directory + "/loadstats/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".csv"

            if item[1] == SEAGULL_SIMULATOR:

                if item[23] == "STATEFULL":
                    print("Inside seagull simulator stats writing")
                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,Total TPS/Sec,On-Hold Sessions,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

                else:

                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Requests/Sec,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

            elif item[1] == MGTS_SIMULATOR:

                if item[23] == "STATEFULL":

                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,Total Req/sec,On-Hold Sessions,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

                else:

                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Requests/Sec,Incoming Calls,Outgoing Calls,Successsful Calls,% of success\n")

            elif item[1] == SIPPY_SIMULATOR:

                if item[23] == "STATEFULL":

                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write(
                            "Scenario,Initials/Sec,Updates/Sec,Terminate/Sec,On-Hold Sessions,Total Calls,Successsful Calls,% of success\n")

                else:

                    with open(csv_stats_file, 'a') as stats_file_writer:
                        stats_file_writer.write("Scenario,Requests/Sec,Total Calls,Successsful Calls,% of success\n")

        print("simulator_stats_monitor end")
        return curr_time_stats

    """method to capture stats on file for reporting"""
    def simulator_categorize_write_stats(self, item, curr_time_stats, stats_from_file_type):

        self.directory = item[12] + '/' + self.time_stats + '/'
        stats_file = self.directory + "/html/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".html"
        csv_stats_file = self.directory + "/csv/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".csv"

        if item[1] == SEAGULL_SIMULATOR:
            self.seagulldir = self.directory + "seagull/"
            print(self.seagulldir)
            seagull_sim = SeagullSimulator()
            try:
                if (stats_from_file_type == 0):
                    print("calling load stats")
                    seagull_sim.loadStats(item[4], item[11], item[6], item[23], item[24], item[25], item[26], item[27],
                                          2, (stats_file, csv_stats_file))
                elif (stats_from_file_type == 1):
                    print("calling write stats")
                    print(item[28])
                    seagull_sim.writeStats(item[4], item[5], item[11], item[8], item[6], item[23], item[24], item[25],
                                           item[26], item[27], 2, (stats_file, csv_stats_file), item[28],
                                           self.seagulldir)

            except Exception as e:
                print(str(e))
            del seagull_sim


        elif item[1] == MGTS_SIMULATOR:

            self.mgtsdir = self.directory + "mgts/"
            self.mgtsip = item[0]
            self.mgtsfile = item[29]
            self.mgtsuser = item[8]
            head,tail=os.path.split(item[29])
            self.mgtsstatsfile=self.mgtsdir + tail
            print(self.mgtsstatsfile)
            if item[30] == '1' and self.copy_flag==True:
                self.copy_mgts_stats_file(self.mgtsip, self.mgtsuser, self.mgtsfile, self.mgtsdir)

            try:
                if item[30] == '0':
                    if item[8] in MGTSSimulator.unique_mgts_server_map and item[
                        15] in MGTSSimulator.unique_mgts_assignment_map:
                        MGTSSimulator.unique_mgts_server_map[item[8]].MGTSScenarioStats(item[14], item[15], item[20],
                                                                                        item[5], item[4], 2, item[6],
                                                                                        item[23], item[24], item[25],
                                                                                        item[26], item[27],
                                                                                        (stats_file, csv_stats_file))

                if item[30] == '1':
                    if os.path.exists(self.mgtsstatsfile):
                        self.scenario_result=MGTSSimulator.MGTSScenariofileStats(self,item[5],item[4],self.mgtsstatsfile,2,item[6],(stats_file, csv_stats_file))
                        print(self.scenario_result)

            except Exception as e:
                print(str(e))

        elif item[1] == SIPPY_SIMULATOR:
            self.sippdir = self.directory + "sipp/"
            sippy_sim = SippySimulator()
            try:
                result = sippy_sim.loadStats(item[4], item[5], item[11], item[8], item[6], item[23], item[24], item[25],
                                             item[26], item[27], 2, (stats_file, csv_stats_file))
            except Exception as e:
                print(str(e))
            del sippy_sim

        return True

    """method to copy mgts scenario stats file from mgts server for offline statistics"""
    def copy_mgts_stats_file(self, mgtsip, mgtsuser, mgtsfile, mgtsdir):

        self.remoteCopy(mgtsip, mgtsuser, mgtsfile, mgtsdir)
        time.sleep(5)
        return self

    """method to monitor and capture stats on statistics on regular intervels"""
    def simulator_monitor_write_stats(self, item, curr_time_stats, stats_from_file_type):

        print("simulator_monitor_write_stats start")
        self.directory = item[12] + '/' + self.time_stats + '/'
        csv_stats_file = self.directory + "/loadstats/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".csv"

        if item[1] == SEAGULL_SIMULATOR:
            self.seagulldir = self.directory + "seagull/"
            print(self.seagulldir)
            seagull_sim = SeagullSimulator()
            try:
                if (stats_from_file_type == 0):
                    print("calling load stats")
                    seagull_sim.loadStats(item[4], item[11], item[6], item[23], item[24], item[25], item[26], item[27],
                                          2, csv_stats_file)
                elif (stats_from_file_type == 1):
                    print("calling monitoring write stats")
                    print(item[28])
                    seagull_sim.MonitorStats(item[4], item[5], item[11], item[8], item[6], item[23], item[24], item[25],
                                             item[26], item[27], 2, csv_stats_file, item[28], self.seagulldir)

            except Exception as e:
                print(str(e))
            del seagull_sim


        elif item[1] == MGTS_SIMULATOR:

            self.mgtsdir = self.directory + "mgts/"
            self.mgtsip = item[0]
            self.mgtsfile = item[29]
            self.mgtsuser = item[8]
            self.remoteCopy(self.mgtsip, self.mgtsuser, self.mgtsfile, self.mgtsdir)

            try:
                if item[8] in MGTSSimulator.unique_mgts_server_map and item[
                    15] in MGTSSimulator.unique_mgts_assignment_map:
                    MGTSSimulator.unique_mgts_server_map[item[8]].MGTSScenarioMonitorStats(item[14], item[15], item[20],
                                                                                           item[5], item[4], 2, item[6],
                                                                                           item[23], item[24], item[25],
                                                                                           item[26], item[27],
                                                                                           csv_stats_file)

            except Exception as e:
                print(str(e))

        elif item[1] == SIPPY_SIMULATOR:
            self.sippdir = self.directory + "sipp/"
            sippy_sim = SippySimulator()
            try:
                result = sippy_sim.loadStats(item[4], item[5], item[11], item[8], item[6], item[23], item[24], item[25],
                                             item[26], item[27], 2, csv_stats_file)
            except Exception as e:
                print(str(e))
            del sippy_sim

        print("simulator_monitor_write_stats end")
        return True

    """method to close simulator stastics"""
    def simulator_close_stats(self, curr_time_stats):

        for item in self.new_sim_config_list:
            self.directory = item[12] + '/' + self.time_stats + '/'
            stats_file = self.directory + "/html/" + item[1] + "_" + item[13] + "_" + curr_time_stats + ".html"

            with open(stats_file, 'a') as stats_file_writer:
                stats_file_writer.write("</tbody></table></body></html>")

    def simulator_specific_choice_select(self):

        scen_choice_list = []
        scen_choice_map = {}
        scen_choice = 10000

        for count, item in enumerate(self.new_sim_config_list):
            print("Enter %d to start scenario %s" % (count + 1, item[4]))
            scen_choice_map[count + 1] = item
        print("Enter 0 to exit after selecting scenarios")

        while (scen_choice != 0):
            try:
                scen_choice = int(eval(input("Enter Your Choice : ")))
                print("your choice is %d" % scen_choice)
                scen_choice_list.append(scen_choice)
            except:
                print("Invalid Input")

        return (scen_choice_list, scen_choice_map)

    def gui_simulator_specific_choice_select(self):

        scen_choice_map = {}
        for item in self.new_sim_config_list:
            scen_choice_map[item[4]] = item
            print("Scenarios to be started is %s" %scen_choice_map)

        return (scen_choice_map)

    def disconnect_simulators(self):
        MGTSSimulator.DisconnectMGTSSimulator()
        MGTSSimulator.MGTSGlobalValuesReset()

    """ Method to check whether application is live or not """

    def new_simulator_is_application_alive(self, curr_time):

        server_id_index = 9
        product_id_index = 1
        instance_id_index = 2

        """ Used to find the current product to capture product wise statistcis """
        self.active_product_count = {}

        cmd = ""

        product_array = np.array(self.new_sim_config_list)
        print(product_array)

        servers = list(set(product_array[:, server_id_index]))
        print(servers)

        for server in servers:

            server_specific_details = product_array[np.where(product_array[:, server_id_index] == server)]
            product_indices = np.where(product_array[:, server_id_index] == server)
            cmd = ""
            count = 0
            print("product_indices")
            print(product_indices)
            print("server_specific_details")
            print(server_specific_details)

            for item in server_specific_details:

                print(item[1])

                if item[1] == "SEAGULL_SIMULATOR" or item[1] == "SIPPY_SIMULATOR":
                    cmd = cmd + 'ps -ef | grep -w ' + item[5] + ' | grep -v "grep" | awk \'{print $2}\';echo END;'
                    print("cmd")
                    print(cmd)

            print(cmd)

            if cmd:
                if (item[0] == localip or item[0] == "127.0.0.1"):
                    app_result = self.localCommand([cmd])
                else:
                    app_status = self.remoteCommand(server_specific_details[0, 0], cmd, server_specific_details[0, 5])
                    del app_status.res[-1]
                    app_result = app_status.res
            else:
                app_result = ""

            print(app_result)

            if (app_result):

                for i in range(len(app_result)):

                    if (i == 0):

                        if app_result[i] != "END":
                            self.new_config_list[product_indices[0][count]][8] = app_result[i]
                            count += 1

                        elif app_result[i] == "END":
                            print("issue at index %d" % i)
                            count = self.restart_process(product_indices, count, curr_time)

                    else:

                        if app_result[i - 1] == "END" and app_result[i] != "END":
                            self.new_config_list[product_indices[0][count]][8] = app_result[i]
                            count += 1

                        elif app_result[i - 1] == "END" and app_result[i] == "END":
                            print("issue at index %d" % i)
                            count = self.restart_process(product_indices, count, curr_time)

                        elif app_result[i - 1] != "END" and app_result[i] == "END":
                            pass

        cmd = ""
        return (self)

    def restart_sim_process(self, product_indices, count, curr_time, app_path=None):

        with open(self.inst_restart_stat_file_name, 'a') as self.stat_file_obj:
            self.stat_file_obj.write("\nScenario %s Restarted in Load at %s\n" % (
                self.new_sim_config_list[product_indices[0][count]][4], curr_time))

        if self.new_sim_config_list[product_indices[0][count]][1] == "SEAGULL_SIMULATOR" or \
                        self.new_sim_config_list[product_indices[0][count]][1] == "SIPPY_SIMULATOR":
            self.simulator_categorize_simulator_starter(self.new_sim_config_list[product_indices[0][count]], app_path)

        count += 1

        return (count)

    def simulator_choice_list(self):

        self.choice = 0
        while (self.choice != EXIT_CHOICE):

            print(
                "\n1. Start Scenarios of entire load \n2. Set Call Rate \n3. Pause Load \n4. Restart Load \n5. Stop Load \n6. Get Load Stats\n7. Start Specific Scenario\n8. Set Call Rate for specific scenario\n9. Pause specific scenario\n10. Restart specific scenario\n11. Stop Specific scenario\n12. Get Load Stats for specific scenario\n13. Generate Load Stats Report\n14. Disconnect from Load Simulators \n15.Exit\n")
            print("\nEnter Your Choice")

            try:
                self.choice = int(input())
                print(self.choice)

                if (self.choice == 1):
                    self.simulator_starter()

                elif (self.choice == 2):
                    self.simulator_set_call_rate()
                    print("exiting from sim choice list")

                elif (self.choice == 3):
                    self.simulator_pause()

                elif (self.choice == 4):
                    self.simulator_restart()

                elif (self.choice == 5):
                    self.simulator_stop()

                elif (self.choice == 6):
                    self.simulator_get_stats()

                elif (self.choice == 7):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_starter(self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 8):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_set_call_rate(
                            self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 9):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_pause(self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 10):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_restart(self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 11):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_stop(self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 12):

                    self.scen_choice_list = []
                    self.scen_choice_map = {}

                    (self.scen_choice_list, self.scen_choice_map) = self.simulator_specific_choice_select()

                    for self.scenario_index in range(len(self.scen_choice_list) - 1):
                        self.simulator_item_get_stats(self.scen_choice_map[self.scen_choice_list[self.scenario_index]])

                elif (self.choice == 13):
                    self.simulator_write_stats()

                elif (self.choice == 14):
                    self.disconnect_simulators()

                elif (self.choice == EXIT_CHOICE):
                    print("Exiting from simulator option")

            except ValueError:
                print("Invalid Input..Please Retry")
                self.choice = 0

            except:
                print("observed abnormal behaviour in the script..!so exiting from simulator section.")
                self.choice = EXIT_CHOICE

    def gui_simulator_choice_list(self, choice, app_path, stats_from_file_type):

        self.choice = choice
        if (self.choice != EXIT_CHOICE):

            print(
                "\n1. Start Scenarios of entire load \n2. Set Call Rate \n3. Pause Load \n4. Restart Load \n5. Stop Load \n6. Get Load Stats\n7. Start Specific Scenario\n8. Set Call Rate for specific scenario\n9. Pause specific scenario\n10. Restart specific scenario\n11. Stop Specific scenario\n12. Get Load Stats for specific scenario\n13. Generate Load Stats Report\n14. Disconnect from Load Simulators \n15.Exit\n")
            print("\nEnter Your Choice")

            try:
                if (self.choice == 1):
                    result = self.simulator_starter(app_path)
                    if (result):
                        return "scenarios started successfully"

                elif (self.choice == 2):
                    result = self.simulator_set_call_rate()
                    if (result):
                        return "call rate set successfully"
                    print("exiting from sim choice list")

                elif (self.choice == 3):
                    result = self.simulator_pause()
                    if (result):
                        return "scenarios paused successfully"

                elif (self.choice == 4):
                    result = self.simulator_restart()
                    if (result):
                        return "scenarios restarted successfully"

                elif (self.choice == 5):
                    result = self.simulator_stop()
                    if (result):
                        return "scenarios stopped successfully"

                elif (self.choice == 6):
                    result = self.simulator_get_stats()
                    result
                    if (result):
                        return result

                elif (self.choice == 7):

                    self.scen_choice_map = {}

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()

                    for self.scenario in self.scen_choice_list:
                        self.simulator_item_starter(self.scen_choice_map[self.scenario], app_path)

                    return "scenarios started successfully"


                elif (self.choice == 8):

                    self.scen_choice_map = {}

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()

                    for self.scenario in self.scen_choice_list:
                        self.simulator_item_set_call_rate(self.scen_choice_map[self.scenario])

                    return "call rate set successfully"


                elif (self.choice == 9):

                    self.scen_choice_map = {}

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()

                    for self.scenario in self.scen_choice_list:
                        self.simulator_item_pause(self.scen_choice_map[self.scenario])

                    return "scenarios paused successfully"


                elif (self.choice == 10):

                    self.scen_choice_map = {}

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()

                    for self.scenario in self.scen_choice_list:
                        self.simulator_item_restart(self.scen_choice_map[self.scenario])

                    return "scenarios restarted successfully"


                elif (self.choice == 11):

                    self.scen_choice_map = {}

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()

                    for self.scenario in self.scen_choice_list:
                        self.simulator_item_stop(self.scen_choice_map[self.scenario])

                    return "scenarios stopped successfully"


                elif (self.choice == 12):

                    self.scen_choice_map = {}
                    result = ""

                    self.scen_choice_map = self.gui_simulator_specific_choice_select()
                    print(self.scen_choice_list)

                    for self.scenario in self.scen_choice_list:
                        result += self.simulator_item_get_stats(self.scen_choice_map[self.scenario])

                    return result


                elif (self.choice == 13):
                    self.simulator_write_stats(stats_from_file_type)
                    return "stats report generated successfully"

                elif (self.choice == 14):
                    self.disconnect_simulators()

                elif (self.choice == EXIT_CHOICE):
                    print("Exiting from simulator option")

            except ValueError:
                print("Invalid Input..Please Retry")
                self.choice = 0

            except Exception as e:
                print(e)
                print("observed abnormal behaviour in the script..!so exiting from simulator section.")
                self.choice = EXIT_CHOICE


def sim_live_check(sim_start):
    print("sim_start.load_sim_stop_is_application_alive_flag : %d" % sim_start.load_sim_stop_is_application_alive_flag)

    while sim_start.load_sim_stop_is_application_alive_flag != 1:

        if (len(sim_start.new_sim_config_list) > 0):
            t = time.localtime(time.time())
            curr_time = str(t.tm_year) + '/' + str(t.tm_mon).zfill(2) + '/' + str(t.tm_mday).zfill(2) + ' ' + str(
                t.tm_hour).zfill(2) + ':' + str(t.tm_min).zfill(2) + ':' + str(t.tm_sec).zfill(2)
            sim_start.new_simulator_is_application_alive(curr_time)
            time.sleep(float(sim_start.is_alive_interval))

    sim_start.load_sim_stop_is_application_alive_flag = 0
