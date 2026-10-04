#!/usr/bin/python
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime
import os, re
from dateutil.parser import parse
from pandas.plotting import table
from pandas import *
from datetime import datetime
from datetime import timedelta
import subprocess

path_wkthmltopdf = r'/opt/Python/lib/python3.6/python-pdfkit-master/wkhtmltox/bin/wkhtmltopdf'


class LoadAnalyzer():
    def __init__(self):
        pass
    """execute command in remote server and will return output"""

    def remoteCommand(self, ip, cmd, username):

        print("Start remoteCommand time:", datetime.now())
        self.HOST = username + "@" + ip
        self.COMMAND = cmd
        print(cmd)
        self.ssh = subprocess.Popen(["ssh", "%s" % self.HOST, self.COMMAND], shell=False, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        self.res = self.ssh.communicate()[0]
        self.res = self.res.decode("utf-8")
        self.res = self.res.split("\n")
        print(self.res)
        print("End remoteCommand time:", datetime.now())
        return (self.res)


    def column_field_stats_analyze(self, file, column_index, row_index=-1, skip_rows=6):
        df = pd.read_csv(file)
        df_transposed = df.transpose()
        #print(df_transposed)
        if (row_index == -1):
            cumulative_sum = df_transposed[column_index][skip_rows:].sum()
        else:
            cumulative_sum = df_transposed[column_index][row_index]

        print(cumulative_sum)

    def gen_util_stats_file_parse(self, file, analyze_file, include_from_field):
        with open(file, 'r') as file_read:
            content = file_read.readlines()

        with open(analyze_file, 'w') as file_write:
            res = "\n".join(content[include_from_field:])
            file_write.write(res)

    def grouped_column_field_stats_analyze(self, file, start_column_index, end_column_index, start_row_index=-1,
                                           end_row_index=-1, skip_rows=6, label_index=1):
        df = pd.read_csv(file)
        cumulative_sum = []
        labels = []
        df_transposed = df.transpose()
        for i in range(start_column_index, end_column_index):
            if (start_row_index == -1) or (end_row_index == -1):
                cumulative_sum.append(df_transposed[i][skip_rows:].sum())
                labels.append(df_transposed[i][label_index])
            else:
                for j in range(start_row_index, end_row_index):
                    key = str(i) + str(j)
                    cumulative_sum.append(df_transposed[i][j])
                    labels.append(df_transposed[i][label_index])

        print(cumulative_sum)
        print(labels)
        return (labels, cumulative_sum)

    def plot_graph(self, labels, cumulative_sum):
        # plt.ioff()
        plt.plot(labels, cumulative_sum)
        max_val = max(cumulative_sum)
        max_ind = cumulative_sum.index(max_val)
        text = "Index " + str(labels[max_ind]) + " is " + str(max_val)
        plt.annotate(text, xy=(labels[max_ind], max_val), xytext=(labels[max_ind] + 1, max_val + 0.5),
                     arrowprops=dict(facecolor='black', shrink=0.05), )
        min_val = min(cumulative_sum)
        min_ind = cumulative_sum.index(min_val)
        min_text = "Index " + str(labels[min_ind]) + " is " + str(min_val)
        plt.annotate(min_text, xy=(labels[min_ind], min_val), xytext=(labels[min_ind] + 1, min_val + 0.5),
                     arrowprops=dict(facecolor='black', shrink=0.05), )
        plt.xticks(np.arange(min(labels), max(labels) + 1, 1.0))
        plt.xlabel("Cumulative Values")
        plt.ylabel("Stats Parameter")
        plt.show()

    def consolidate_stats(self,app_stats_directory,rowlist):
        dfList = []
        print(app_stats_directory)
        for root, dirs, files in os.walk(app_stats_directory):
            print(files)
            for fname in files:
                print(fname)
                if re.match("^.*.txt$", fname):
                    with open(os.path.join(root, fname)) as f:
                        lines = f.readlines()
                        rgt = lines[0].split(":", 1)
                        dt = parse(rgt[1])
                        dt = dt.strftime('%d-%m-%Y')
                        product = lines[1].split(":", 2)[1].replace(' ', '').rstrip()
                        instance = lines[3].split(":", 1)[1]
                        instance = instance.split(":", 1)[0].replace(' ', '')
                    frame = pd.read_csv(os.path.join(root, fname), skiprows=6)
                    frame.insert(0, 'date', dt)
                    frame.insert(1, 'product', product)
                    frame.insert(2, 'instance', instance)
                    frame = frame.rename(columns={c: c.replace(' ', '') for c in frame.columns})
                    frame = frame.replace(' ', '', regex=True)
                    frame = frame.iloc[rowlist, :]
                    # print(frame.head())
                    # frame['key'] = "file{}".format(i)
                    dfList.append(frame)
        return (dfList)

    def generate_load_app_stats_report(self,loadstatdate):
        cmd = "/opt/product/testteam/Products/NSSLOAD/DATALOAD/DATA_LOAD_STATS/greprun.sh " + loadstatdate
        print(cmd)
        stats_gen = self.remoteCommand("192.168.151.84",cmd,"testteam")
        print(stats_gen)


    def prepare_stats_related_info(self,load_start_date,load_stop_date,load_start_hour,load_stop_hour):
        load_total_hours = 24
        format = '%d-%m-%Y'
        format2 = '%Y-%m-%d %H:%M:%S'
        format_dt = '%d-%m-%Y %H:%M:%S'
        f_date = datetime.strptime(load_start_date, format)
        l_date = datetime.strptime(load_stop_date, format)
        f_datetime = f'{load_start_date} {load_start_hour}:00:00'
        f_datetime = datetime.strptime(f_datetime, format_dt)
        l_datetime = f'{load_stop_date} {load_stop_hour}:00:00'
        l_datetime = datetime.strptime(l_datetime, format_dt)
        if load_start_date==load_stop_date:
            stats_hours = load_stop_hour - load_start_hour
            self.generate_load_app_stats_report(str(f_date).split(" ",1)[0].replace("-",""))
            print(stats_hours)
        else:
            delta = l_date - f_date
            diff = l_datetime - f_datetime
            delta_days = delta.days
            load_stat_date = f_date
            self.generate_load_app_stats_report(str(f_date).split(" ",1)[0].replace("-",""))
            for i in range(delta_days):
                load_stat_date = load_stat_date + timedelta(days=1)
                self.generate_load_app_stats_report(str(load_stat_date).split(" ",1)[0].replace("-",""))
            print(l_date +  + timedelta(days=1))

la = LoadAnalyzer()
app_stats_directory = '/opt/product/LOAD_GUI/DATA_SOLARIS_LOAD/app_stats'
rowlist = [11,12,13,14,15,16]
load_start_date = "25-02-2020"
load_stop_date = "25-02-2020"
load_start_hour = 10
load_stop_hour = 10
file = "/opt/product/LOAD/stats/LOAD_STAT_20171012.txt"
analyze_file = "/opt/product/LOAD/stats/ANA_LOAD_STAT_20171012.txt"
#final_stats = la.consolidate_stats(app_stats_directory,rowlist,load_stop_hour)
la.prepare_stats_related_info(load_start_date,load_stop_date,load_start_hour,load_stop_hour)
#df = pd.concat(final_stats)
#df = pd.DataFrame(df)
#final_stats.to_html('final_stats.html')
#plot data
#la.gen_util_stats_file_parse(file, analyze_file, 7)
#la.column_field_stats_analyze(analyze_file, 2, skip_rows=6)
#la.column_field_stats_analyze(analyze_file, 2, row_indAddtionalData1ex=28)
#(labels, cumulative_sum) = la.grouped_column_field_stats_analyze(analyze_file, 43, 65)
#la.plot_graph(labels, cumulative_sum)