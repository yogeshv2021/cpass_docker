#!/usr/bin/python
import math
import os
import subprocess
import threading
import shutil
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pdfkit
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PyPDF2.pdf import PageObject
from matplotlib.font_manager import FontProperties

import flaskr.simulator as simulator
from flaskr.utilities import *

path_wkthmltopdf = r'/opt/Python/lib/python3.6/python-pdfkit-master/wkhtmltox/bin/wkhtmltopdf'

class LoadReporter(UtilityLib,threading.Thread):

    def __init__(self,UPLOAD_FOLDER):
        threading.Thread.__init__(self)
        self.load_report_title=UPLOAD_FOLDER+"/title.html"
        self.load_report_summary=UPLOAD_FOLDER+"/summary.html"
        self.load_report_call_rate=UPLOAD_FOLDER+"/call_rate.csv"
        self.load_execution_summary=UPLOAD_FOLDER+"/execution_summary.html"
        self.load_architecture=UPLOAD_FOLDER+"/architecture.html"
        self.load_purpose_environment=UPLOAD_FOLDER+"/purpose_environment.html"
        self.load_environment_details=UPLOAD_FOLDER+"/environment.csv"
        self.load_inhouse_products=UPLOAD_FOLDER+"/in_house_products.csv"
        self.load_architecture_image=UPLOAD_FOLDER+"/architecture.png"

        self.max_memory={}
        self.max_cpu={}
        self.max_cpu_util={}

        with subprocess.Popen(['date','+"%Y"'],stdout=subprocess.PIPE) as self.pipe:
            self.year=self.pipe.stdout.read()
            self.year=self.year.decode("utf-8")


    def plot_cpu_memory(self,filename,stats_path):
        sizes=[]
        cpu=[]
        times=[]
        graph_flag=0

        save_file=stats_path+"/graph/"+filename+"_graph.png"
        filename=stats_path+"/csv/"+filename
        print("file csv to be processed : %s" %filename)
    
        df=pd.read_csv(filename,names=["ti","pro","proc","tim","memkb","memmb","cpu","mempercent","netiorx","netiotx","blockioread","blockiowrite","pid"])

        time=np.arange(1,len(df['ti']),1)

        print(len(df['cpu']),df['memmb'])

        if(len(df['cpu'])>1):
    
            for i in range(1,len(df['cpu'])):
                sizes.append(float(df['memmb'][i][:-1]))
                cpu.append(float(df['cpu'][i][:-1]))

            """
            df['memmb'][1:]=[s.strip('M') for s in df['memmb'][1:]]
            df['memmb'][1:]=[s.strip('m') for s in df['memmb'][1:]]
            df['memmb'][1:]=[s.strip('g') for s in df['memmb'][1:]]
            df['memmb'][1:]=[s.strip('G') for s in df['memmb'][1:]]
            df['memmb'][1:]=[float(i) for i in df['memmb'][1:]]

            self.max_memory[df['pro'][1]]=str(max(df['memmb'][1:]))
            print(self.max_memory[df['pro'][1]])
            self.max_cpu[df['pro'][1]]=max(df['cpu'][1:])
            print(self.max_cpu[df['pro'][1]])
            """

            k=[float(float(s.strip('k'))/1024) for s in df['memmb'][1:] if 'k' in s]
            m=[float(s.strip('m')) for s in df['memmb'][1:] if 'm' in s]
            M=[float(s.strip('M')) for s in df['memmb'][1:] if 'M' in s]
            g=[float(float(s.strip('g'))*1024) for s in df['memmb'][1:] if 'g' in s]
            f=[float(float(s.strip('b'))/1024) for s in df['memmb'][1:] if 'b' in s]

            appmem=m
            appmem.extend(M)
            appmem.extend(k)
            appmem.extend(g)
            appmem.extend(f)
            print(appmem)
            print(df['cpu'][1:])
            appcpu = [float(x.strip('%') ) for x in df['cpu'][1:]]
            print(appcpu)
            self.max_memory[df['pro'][1]]=str(max(appmem))
            print(self.max_memory[df['pro'][1]])
            self.max_cpu[df['pro'][1]]=str(max(appcpu))
            print(self.max_cpu[df['pro'][1]])
      
            plt.ioff()
            fig1=plt.figure(1,figsize=(10,10))
            plt.subplot(211)
            plt.plot(time,sizes,'r-o')
            plt.xticks(np.arange(min(time), max(time)+1, 1.0))
            plt.xlabel("Time")
            plt.ylabel("Memory")
            red_line = mlines.Line2D([], [], color='red', marker='o',markersize=5, label='Memory Utilization')
            plt.legend(handles=[red_line])
            plt.subplots_adjust(hspace = .75)
        
            plt.subplot(212)
            plt.plot(time,cpu,'b-o')
            plt.xticks(np.arange(min(time), max(time)+1, 1.0))
            plt.xlabel("Time")
            plt.ylabel("CPU")
            blue_line = mlines.Line2D([], [], color='blue', marker='o',markersize=5, label='CPU Utilization')
            plt.legend(handles=[blue_line])
            fig1.savefig(save_file)
            plt.close('all')
            graph_flag=1

        return (save_file,graph_flag)


    
    def plot_sar_stats(self,filename,stats_path):
        usr=[]
        sys=[]
        wio=[]
        idle=[]
        graph_flag=0

        save_file=stats_path+"/graph/"+filename+"_sar.png"
        filename=stats_path+"/csv/"+filename
        print("file csv to be processed : %s" %filename)

        df=pd.read_csv(filename,names=["ti","ser","pro","usr","sys","wio","idle"])
        time=np.arange(1,len(df['ti']),1)

        if(len(df['ti'])>1):
    
            for i in range(1,len(df['ti'])):
                usr.append(float(df['usr'][i]))
                sys.append(float(df['sys'][i]))
                wio.append(float(df['wio'][i]))
                idle.append(float(df['idle'][i]))

            self.max_cpu_util[df['ser'][1]]=max(df['sys'][1:])

            plt.ioff()
            f, axarr = plt.subplots(2, 2,figsize=(10,10))
            axarr[0, 0].plot(time,usr,'r-o')
            axarr[0, 0].set_xticks(np.arange(min(time), max(time)+1, 1.0))
            axarr[0, 0].set_title('SAR Usr Stats')
            red_line = mlines.Line2D([], [], color='red', marker='o',markersize=5, label='%usr')
            axarr[0, 0].legend(handles=[red_line])
    
            axarr[0, 1].plot(time, sys,'b-o')
            axarr[0, 1].set_xticks(np.arange(min(time), max(time)+1, 1.0))
            axarr[0, 1].set_title('SAR Sys stats')
            blue_line = mlines.Line2D([], [], color='blue', marker='o',markersize=5, label='%sys')
            axarr[0, 1].legend(handles=[blue_line])
    
            axarr[1, 0].plot(time, wio,'g-o')
            axarr[1, 0].set_xticks(np.arange(min(time), max(time)+1, 1.0))
            axarr[1, 0].set_title('SAR Wio stats')
            green_line = mlines.Line2D([], [], color='green', marker='o',markersize=5, label='%wio')
            axarr[1, 0].legend(handles=[green_line])
    
            axarr[1, 1].plot(time, idle,'m-o')
            axarr[1, 1].set_xticks(np.arange(min(time), max(time)+1, 1.0))
            axarr[1, 1].set_title('SAR Idle stats')
            magenta_line = mlines.Line2D([], [], color='magenta', marker='o',markersize=5, label='%idle')
            axarr[1, 1].legend(handles=[magenta_line])
            f.subplots_adjust(hspace=0.75)
            plt.xlabel("Time")
            f.savefig(save_file)
            plt.close('all')

            graph_flag=1

        return (save_file,graph_flag)

    
    def plot_iostats(self,filename,stats_path):
    
        disk=[]
        mrpersec=[]
        mwpersec=[]
        serv_time=[]
        wait_perc=[]
        busy_perc=[]
        graph_flag=0

        save_file=stats_path+"/graph/"+filename+"_disk.png"
        filename=stats_path+"/csv/"+filename
        print("file csv to be processed : %s" %filename)
    
        df=pd.read_csv(filename,names=["ti","disk","mrpersec","mwpersec","serv_time","wait_perc","busy_perc","server"])

        if(len(df['disk'])>1):

            disks=list(set(df.disk[1:]))
            print(disks)
            num_of_disks=len(disks)
            print("num of disks : %d" %num_of_disks)
            row_count=math.ceil(num_of_disks/2)
            print("row count : %d" %row_count)

            red_line = mlines.Line2D([], [], color='red', marker='o',markersize=5, label='MR/sec')
            green_line = mlines.Line2D([], [], color='green', marker='*',markersize=10, label='MW/sec')
            blue_line = mlines.Line2D([], [], color='blue', marker='o',markersize=5, label='Service Time')

            plt.ioff()
            fig, axs = plt.subplots(num_of_disks,2,figsize=(10,10))

            x=0
            y=0
            for each_disk in disks:
                per_disk_df=df[df.disk==each_disk]
                time=np.arange(1,len(per_disk_df['ti'])+1,1)

                if(num_of_disks>1):
                    axs[x,y].plot(time,list(per_disk_df['serv_time']),'b-o')
                    axs[x,y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[x,y].set_title('Disk '+per_disk_df['disk'][per_disk_df.index[0]]+' Service Time Stats')
                    y+=1
                    axs[x,y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[x,y].plot(time,list(per_disk_df['wait_perc']),'g-o')
                    axs[x,y].plot(time,list(per_disk_df['busy_perc']),'r-o')
                    axs[x,y].set_title('Disk '+per_disk_df['disk'][per_disk_df.index[0]]+' Wait & Busy Stats')
                    if x==0 and y==1:
                        axs[x, y].legend(handles=[red_line,green_line,blue_line],loc='upper right')

                    if(y==1):
                        y=0
                        x+=1
                else:
                    axs[y].plot(time,list(per_disk_df['serv_time']),'b-o')
                    axs[y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[y].set_title('Disk '+per_disk_df['disk'][per_disk_df.index[0]]+' Service Time Stats')
                    y+=1
                    axs[y].plot(time,list(per_disk_df['wait_perc']),'g-o')
                    axs[y].plot(time,list(per_disk_df['busy_perc']),'r-o')
                    axs[y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[y].set_title('Disk '+per_disk_df['disk'][per_disk_df.index[0]]+' Wait & Busy Stats')
                    if y==1:
                        axs[y].legend(handles=[red_line,green_line,blue_line],loc='upper right')

                    if(y==1):
                        y=0

            fig.subplots_adjust(hspace=1.5)
            fig.savefig(save_file)
            plt.close('all')

            graph_flag=1

        return (save_file,graph_flag)


    def plot_netstats(self,filename,stats_path):
    
        interface=[]
        input_packets=[]
        output_packets=[]
        input_errors=[]
        output_errors=[]
        collisions=[]
        graph_flag=0

        save_file=stats_path+"/graph/"+filename+"_netstats.png"
        filename=stats_path+"/csv/"+filename
        print("file csv to be processed : %s" %filename)
        fontP = FontProperties()
        fontP.set_size('small')
    
        df=pd.read_csv(filename,names=["ti","interface","input_packets","input_errors","output_packets","output_errors","collisions","server"])

        if(len(df['interface'])>1):

            interfaces=list(set(df.interface[1:]))
            print(interfaces)
            num_of_interfaces=len(interfaces)
            print("num of interfaces : %d" %num_of_interfaces)
            row_count=math.ceil(num_of_interfaces/2)
            print("row count : %d" %row_count)

            red_line = mlines.Line2D([], [], color='red', marker='o',markersize=5, label='Input Packets/sec')
            green_line = mlines.Line2D([], [], color='green', marker='*',markersize=10, label='Output Packets/sec')
            blue_line = mlines.Line2D([], [], color='blue', marker='o',markersize=5, label='Input Errors/Sec')
            cyan_line = mlines.Line2D([], [], color='cyan', marker='o',markersize=5, label='Output Errors/Sec')
            magenta_line = mlines.Line2D([], [], color='magenta', marker='o',markersize=5, label='Collisions/Sec')

            plt.ioff()
            fig, axs = plt.subplots(num_of_interfaces,2,figsize=(10,10))

            x=0
            y=0
            for each_interface in interfaces:
                per_interface_df=df[df.interface==each_interface]
                time=np.arange(1,len(per_interface_df['ti'])+1,1)

                if(num_of_interfaces>1):
                    axs[x,y].plot(time,list(per_interface_df['input_packets']),'r-o')
                    #axs[x,y].plot(time,list(per_interface_df['output_packets']),'g-o')
                    #axs[x,y].plot(time,list(per_interface_df['collisions']),'m-o')
                    axs[x,y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[x,y].set_title(per_interface_df['interface'][per_interface_df.index[0]]+' Input,Output Pkts & Collisions/sec Stats')
                    y+=1
                    axs[x,y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[x,y].plot(time,list(per_interface_df['input_errors']),'b-o')
                    #axs[x,y].plot(time,list(per_interface_df['output_errors']),'c-o')
                    axs[x,y].set_title(per_interface_df['interface'][per_interface_df.index[0]]+' Network Error Stats')
                    if x==0 and y==1:
                        axs[x, y].legend(handles=[red_line,green_line,blue_line,cyan_line,magenta_line],loc='upper right',prop = fontP,bbox_to_anchor=(1.3, 1.05)).get_frame().set_alpha(0.5)
                        pass

                    if(y==1):
                        y=0
                        x+=1
                else:
                    axs[y].plot(time,list(per_interface_df['input_packets']),'r-o')
                    axs[y].plot(time,list(per_interface_df['output_packets']),'g-o')
                    axs[y].plot(time,list(per_interface_df['collisions']),'m-o')
                    axs[y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[y].set_title(per_interface_df['interface'][per_interface_df.index[0]]+' Input & Output Packets and Collisions Stats')
                    y+=1
                    axs[y].set_xticks(np.arange(min(time), max(time)+1, 1.0))
                    axs[y].plot(time,list(per_interface_df['input_errors']),'b-o')
                    axs[y].plot(time,list(per_interface_df['output_errors']),'c-o')
                    axs[y].set_title(per_interface_df['interface'][per_interface_df.index[0]]+' Network Error Stats')
                    if y==1:
                        axs[y].legend(handles=[red_line,green_line,blue_line,cyan_line,magenta_line],loc='upper right')
                        pass

                    if(y==1):
                        y=0

            fig.subplots_adjust(hspace=2.0)
            fig.savefig(save_file)
            plt.close('all')

            graph_flag=1

        return (save_file,graph_flag)



    def plot_scenario_stats(self,filename,stats_path,simulator):

        try:

            success_ratio=[]
            labels=[]
            graph_flag=0
            num_of_bars_per_image=10

            title_font = {'fontname':'Arial', 'size':'15', 'color':'black', 'weight':'normal' }
            axis_font = {'fontname':'Arial', 'size':'10'}
            label_font='Arial'
            label_fontsize=10
 
            save_file=stats_path+"/graph/"+filename+"_"+simulator+"_graph.png"
            chart_save_file=stats_path+"/graph/"+filename+"_"+simulator+"_chart.png"
            filename=stats_path+"/csv/"+filename
            print("file csv to be processed : %s" %filename)

            df=pd.read_csv(filename,names=["scenario","requests","incoming","outgoing","success","success_percent"])
            if(len(df['scenario'])>1):
                num_of_scenario=np.arange(1,len(df['scenario']),1)
                ytick_values=np.arange(0,125,25)
                start=1
                height_start=0

                row_count=math.ceil(len(num_of_scenario)/num_of_bars_per_image)
                plt.ioff()
                fig,axes=plt.subplots(row_count,figsize=(10, 10))

                for i in range(1,len(df['scenario'])):
                    success_ratio.append(float(df['success_percent'][i]))

                if(row_count>1):

                    for i in range(row_count):
                        if(i!=(row_count-1)):
                            axes[i].bar(np.arange(start,start+num_of_bars_per_image,1),height=success_ratio[height_start:height_start+num_of_bars_per_image],facecolor='g')
                            axes[i].set_xticks(num_of_scenario[height_start:height_start+num_of_bars_per_image])
                        else:
                            heights=success_ratio[height_start:len(success_ratio)]
                            axes[i].bar(np.arange(start,len(num_of_scenario)+1,1),height=heights,facecolor='g')
                            axes[i].set_xticks(num_of_scenario[height_start:len(num_of_scenario)])

                        axes[i].set_xlabel('Scenarios',**axis_font)
                        axes[i].set_ylabel('Success %',**axis_font)
                        axes[i].set_ylim(0,100)
                        axes[i].set_yticks(ytick_values)
                        axes[i].set_title('Scenario Success Ratio',**title_font)

                        for label in (axes[i].get_xticklabels() + axes[i].get_yticklabels()):
                            label.set_fontname(label_font)
                            label.set_fontsize(label_fontsize)
     
                        start+=num_of_bars_per_image
                        height_start+=num_of_bars_per_image

                else:
                    heights=success_ratio[height_start:len(success_ratio)]
                    axes.bar(np.arange(start,len(num_of_scenario)+1,1),height=heights,facecolor='g')
                    axes.set_xticks(num_of_scenario[height_start:len(num_of_scenario)])
                    axes.set_xlabel('Scenarios',**axis_font)
                    axes.set_ylabel('Success %',**axis_font)
                    axes.set_ylim(0,100)
                    axes.set_yticks(ytick_values)
                    axes.set_title('Scenario Success Ratio',**title_font)

                    for label in (axes.get_xticklabels() + axes.get_yticklabels()):
                        label.set_fontname(label_font)
                        label.set_fontsize(label_fontsize)

                    

                fig.subplots_adjust(hspace=1.5)

                fig.savefig(save_file)

                plt.close('all')

                colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']

                labels=df['scenario'][1:]

                patches, texts = plt.pie(df['success_percent'][1:],colors=colors, startangle=90)

                plt.legend(patches, labels, loc="best")

                plt.axis('equal')
                plt.tight_layout()

                plt.savefig(chart_save_file)

                plt.close('all')

                graph_flag=1

            return (save_file,chart_save_file,graph_flag)

        except Exception as e:
            print(str(e))


    def total_scenario_stats(self,filename,stats_path,simulator):

        try:

            self.result_column=[]
            self.summary_column=[]
            csv_filename=filename
            htmlfile_without_ext=csv_filename.split(".")
            html_filename= htmlfile_without_ext[0]+".html"
            htmlfilename= stats_path+"/html/"+html_filename
            print(htmlfilename)
            html_filename_orig= htmlfile_without_ext[0]+"_orig.html"
            htmlorigfilename= stats_path+"/loadstats/"+html_filename_orig
            print(htmlorigfilename)
            if(os.path.isfile(htmlorigfilename)):
                shutil.copy(htmlorigfilename,htmlfilename)
                print("Simulator Original copy already exists=%s" %htmlorigfilename)
            else:
                shutil.copy(htmlfilename,htmlorigfilename)
                print("Copy of Simulator Stats File=%s" %htmlorigfilename)
            filename=stats_path+"/csv/"+filename
            print("file csv to be processed : %s" %filename)

            scen_hdr=pd.read_csv(filename,nrows=1).columns
            df=pd.read_csv(filename)
            if(simulator == "mgts" or simulator == "seagull"):
                for colname in scen_hdr:
                    if colname=="Incoming Calls":
                        self.summary_column.append(df[colname].sum())
                    if colname=="Outgoing Calls":
                        self.summary_column.append(df[colname].sum())
                    if colname=="Successsful Calls":
                        self.summary_column.append(df[colname].sum())

                self.success_percentage=((self.summary_column[2]/(self.summary_column[0]+self.summary_column[1]))*100)
                self.success_percentage=(round(self.success_percentage,2))
                print("Printing Results")
                print(self.summary_column)
                print(self.success_percentage)

            if simulator == "sippy":
                for colname in scen_hdr:
                    if colname=="Total Calls":
                        self.summary_column.append(df[colname].sum())
                    if colname=="Successsful Calls":
                        self.summary_column.append(df[colname].sum())

                self.success_percentage=((self.summary_column[1]/self.summary_column[0])*100)
                self.success_percentage=(round(self.success_percentage,2))
                print("Printing Results")
                print(self.summary_column)
                print(self.success_percentage)


            for colname in scen_hdr:
                if colname=="Scenario":
                    self.result_column.append("Summary")
                elif colname=="% of success":
                    self.result_column.append(self.success_percentage)
                else:
                    self.result_column.append(df[colname].sum())

            print(self.result_column)
            tfoot = '''<tfoot style="font-weight:bold">{0}</tfoot>'''
            td = "<td><strong>{0}</strong></td>"
            subitems = [tfoot.format(''.join([td.format(a) for a in self.result_column]))]
            str1 = ''.join(str(e) for e in subitems)
            print(str1)
            with open(htmlfilename,'a') as simulator_report_write:
                simulator_report_write.write(str1)
                simulator_report_write.write("</tbody></table></body></html>")

        except Exception as e:
            print(str(e))

    def system_memory_stats(self,filename,stats_path):

        try:

            self.system_memory_result=[]
            csv_filename=filename
            filename=stats_path+"/csv/"+filename
            print("file csv to be processed : %s" %filename)
            df=pd.read_csv(filename, encoding="utf-8", skiprows=2, header=None)
            self.system_memory_result.append(df[1].max())
            self.system_memory_result.append(df[2].max())
            self.system_memory_result.append(df[3].max())
            self.system_memory_result.append(df[4].max())
            self.system_memory_result.append(df[5].max())
            self.system_memory_result.append(df[20].max())
            self.system_memory_result.append(df[21].max())
            self.system_memory_result.append(df[22].max())
            self.system_memory_result.append(df[23][0])
            print(self.system_memory_result)

        except Exception as e:
            print(str(e))

    def system_iostat_stats(self,filename,stats_path):

        try:

            self.system_iostat_result=[]
            csv_filename=filename
            filename=stats_path+"/csv/"+filename
            print("file csv to be processed : %s" %filename)
            df=pd.read_csv(filename, encoding="utf-8", skiprows=1, header=None)
            Max_disk_reads = df.groupby([1])[2].transform(max) == df[2]
            Max_disk_writes = df.groupby([1])[3].transform(max) == df[3]
            Max_disk_service_time = df.groupby([1])[4].transform(max) == df[4]
            Max_disk_wait = df.groupby([1])[5].transform(max) == df[5]
            Max_disk_busy = df.groupby([1])[6].transform(max) == df[6]
            System_name = df[7][0]
            print(df[Max_disk_reads])
            print(df[Max_disk_writes])
            print(df[Max_disk_service_time])
            print(df[Max_disk_wait])
            print(df[Max_disk_busy])
            print(System_name)

        except Exception as e:
            print(str(e))



    def pdf_insert_report_prepare(self,base_file,insert_file,output_file,index):

        output=PdfFileWriter()

        pdf1=PdfFileReader(open(base_file,'rb'))
        pdf2=PdfFileReader(open(insert_file,'rb'))

    
        for page in range(0,pdf1.getNumPages()):
            output.addPage(pdf1.getPage(page ))
    
        output.insertPage(pdf2.getPage(0),index) 
        output.setPageMode("/UseOutlines") 
        outputStream=open(output_file,'wb')
        output.write(outputStream)
        outputStream.close()

    def pdf_merge_pages_prepare(self,base_file,basefile_pagenum,insert_file,insertfile_pagenum,midindex,output_file):

        reader = PdfFileReader(open(base_file,'rb'))
        invoice_page = reader.getPage(basefile_pagenum)
        sup_reader = PdfFileReader(open(insert_file,'rb'))
        sup_page = sup_reader.getPage(insertfile_pagenum)  # We pick the second page here

        translated_page = PageObject.createBlankPage(None, sup_page.mediaBox.getWidth(), sup_page.mediaBox.getHeight())
        translated_page.mergeScaledTranslatedPage(sup_page, 1, 0, midindex)

        translated_page.mergePage(invoice_page)

        writer = PdfFileWriter()
        writer.addPage(translated_page)

        writer.setPageMode("/UseOutlines") 

        with open(output_file, 'wb') as f:
            writer.write(f)


    def pdf_merge_report_preapre(self,input_file1,input_file2,output_file):

        merger=PdfFileMerger()

        pdfs=[input_file1,input_file2]

        for pdf in pdfs:
            merger.append(PdfFileReader(open(pdf,'rb')),import_bookmarks=False)

        with open(output_file, 'wb') as fout:
            merger.write(fout)
 

    def prepare_report(self,prepared,reviewed,approved,load_start_date,load_date,load_stats_path,comments,status_result,dbstatus_result,dbcomment,product_by,load_table_type,load_duration):

        self.load_report_file=load_stats_path+"/html/load_report.html"
        self.load_report_current_title=load_stats_path+"/html/title.html"
        self.load_report_current_exec_summary=load_stats_path+"/html/exec_summary.html"
        self.load_current_purpose_environment=load_stats_path+"/html/purpose_environment.html"
        self.load_report_pdf_file=load_stats_path+"/load_report.pdf"

        config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

        with open(self.load_report_title,'r') as load_report_read:
            content=load_report_read.read()
            content=content.replace("<PASS>",status_result)
            content=content.replace("<TITLE>",product_by)
            content=content.replace("<START_DATE>",load_start_date)
            content=content.replace("<PREPARED>",prepared)
            content=content.replace("<REVIEWED>",reviewed)
            content=content.replace("<APPROVED>",approved)
            content=content.replace("<APPROVED_DATE>",load_date)
            content=content.replace("<YEAR>",self.year)

        with open(self.load_report_current_title,'w') as load_report_write:
            load_report_write.write(content)

        with open(self.load_execution_summary,'r') as load_report_read:
            content=load_report_read.read()
            content=content.replace("<LOAD_DURATION>",load_duration)

        with open(self.load_report_current_exec_summary,'w') as load_report_write:
            load_report_write.write(content)

        with open(self.load_report_call_rate,'r') as load_report_read:
            content=load_report_read.readlines()

        with open(self.load_report_current_exec_summary,'a') as load_report_write:
            load_report_write.write("<html><body><center><table border='1'><tbody>")
            for line in content:
                items=line.split(",")
                load_report_write.write("<tr>")
                for item in items:
                    load_report_write.write("<td>"+item+"</td>")
                load_report_write.write("</tr>")
            load_report_write.write("</tbody></table></center></body></html>")


        with open(self.load_purpose_environment,'r') as load_report_read:
            content=load_report_read.read()

        with open(self.load_current_purpose_environment,'w') as load_report_write:
            load_report_write.write(content)

        with open(self.load_environment_details,'r',encoding = "ISO-8859-1") as load_report_read:
            content=load_report_read.readlines()

        with open(self.load_current_purpose_environment,'a') as load_report_write:
            load_report_write.write("<html><body><center><table border='1'><tbody>")
            for line in content:
                items=line.split(",")
                load_report_write.write("<tr>")
                for item in items:
                    load_report_write.write("<td>"+item+"</td>")
                load_report_write.write("</tr>")
            load_report_write.write("</tbody></table></center></body></html>")

        with open(self.load_inhouse_products,'r',encoding = "ISO-8859-1") as load_report_read:
            content=load_report_read.readlines()

        with open(self.load_current_purpose_environment,'a') as load_report_write:
            load_report_write.write("<html><body><h4>In House Products</h4><center><table border='1'><tbody>")
            for line in content:
                items=line.split(",")
                load_report_write.write("<tr>")
                for item in items:
                    load_report_write.write("<td>"+item+"</td>")
                load_report_write.write("</tr>")
            load_report_write.write("<tbody></table></center></body></html>")


        with open(self.load_architecture,'r') as load_report_read:
            content=load_report_read.read()

        with open(self.load_report_file,'w') as load_report_write:
            image=self.load_architecture_image
            load_report_write.write(content)
            load_report_write.write('</br>')
            load_report_write.write('<center><img src="'+image+'"/></center>')
            load_report_write.write('</br></body></html>')
            print("Architecture included in pdf")


        loadStats_path=load_stats_path+"/appstats/"
        print(loadStats_path)
        loadStats_files=sorted(os.listdir(loadStats_path))
        report_title_count=0

        for stat_file in loadStats_files:
            if "csv" in stat_file:
                print(stat_file)
                file_without_ext=stat_file.split(".")
                html_file=loadStats_path+file_without_ext[0]+".html"
                print(html_file)
                read_statsfile=loadStats_path+stat_file
                print(read_statsfile)
                df = pd.read_csv(loadStats_path+stat_file)
                df.to_html(html_file)

        for stat_file in loadStats_files:
            if "html" in stat_file:
                f=open(load_stats_path+"/appstats/"+stat_file,'r')
                content=f.read()
                print(content)
                print(self.load_report_file)
                with open(self.load_report_file,'a') as load_report_write:
                    load_report_write.write("<div style=\"page-break-before:always\"></div>")
                    load_report_write.write("</br><h2>External Report:"+stat_file+"</h2></br>")
                    load_report_write.write(content)
                    load_report_write.write('</br>')
                f.close()

        for stat_file in loadStats_files:
            print("statsfile: %s" %stat_file)
            if "jpg" or "jpeg" or "png" in stat_file:
                with open(self.load_report_file,'a') as load_report_write:
                    image=stat_file
                    load_report_write.write(content)
                    load_report_write.write('</br>')
                    load_report_write.write('<center><img src="'+image+'"/></center>')
                    load_report_write.write('</br></body></html>')
                    print("Docker Image added in pdf")
                load_report_write.close()

        report_title_count=0

        path=load_stats_path+"/html"
        stat_files=sorted(os.listdir(path))

        for stat_file in stat_files:

            if simulator.SEAGULL_SIMULATOR in stat_file and "html" in stat_file:
                file_without_ext=stat_file.split(".")
                csv_file_name=file_without_ext[0]+".csv"
                self.total_scenario_stats(csv_file_name,load_stats_path,"seagull")
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>Seagull Stats</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</br>')
                    #(csv_result_file,chart_save_file,flag)=self.plot_scenario_stats(csv_file_name,load_stats_path,"seagull")

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>Seagull Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                        #load_report_write.write('</br></br><h2>Success Ratio Pie Stats</h2></br>')
                        #load_report_write.write('<img src="'+chart_save_file+'"/>')
                f.close()

        report_title_count=0

        for stat_file in stat_files:

            if simulator.MGTS_SIMULATOR in stat_file and "html" in stat_file:

                file_without_ext=stat_file.split(".")
                csv_file_name=file_without_ext[0]+".csv"
                self.total_scenario_stats(csv_file_name,load_stats_path,"seagull")
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>MGTS Stats</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</br>')
                    #(csv_result_file,chart_save_file,flag)=self.plot_scenario_stats(csv_file_name,load_stats_path,"mgts")

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>MGTS Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                        #load_report_write.write('</br></br><h2>Success Ratio Pie Stats</h2></br>')
                        #load_report_write.write('<img src="'+chart_save_file+'"/>')
                f.close()


        report_title_count=0

        for stat_file in stat_files:

            if simulator.SIPPY_SIMULATOR in stat_file and "html" in stat_file:
                file_without_ext=stat_file.split(".")
                csv_file_name=file_without_ext[0]+".csv"
                self.total_scenario_stats(csv_file_name,load_stats_path,"sippy")
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>SIPP Stats</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</br>')
                    #(csv_result_file,chart_save_file,flag)=self.plot_scenario_stats(csv_file_name,load_stats_path,"seagull")

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>Seagull Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                        #load_report_write.write('</br></br><h2>Success Ratio Pie Stats</h2></br>')
                        #load_report_write.write('<img src="'+chart_save_file+'"/>')
                f.close()

        report_title_count=0


        for stat_file in stat_files:

            if "HOUR_MEM_STATS" in stat_file and "html" in stat_file:

                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("</br><h2>CPU & Memory Utilization</h2></br>")
                        report_title_count+=1

                    load_report_write.write(content)
                    load_report_write.write('</tbody></table></body></html>')
                    file_without_ext=stat_file.split(".")
                    csv_file_name=file_without_ext[0]+".csv"
                    csv_file_name.replace("HOUR_MEM_STATS","MINUTES_MEM_STATS")
                    (csv_result_file,flag)=self.plot_cpu_memory(csv_file_name,load_stats_path)

                    if(flag==1):
                        print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>CPU & Memory Utilization Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')

                f.close()


        report_title_count=0


        for stat_file in stat_files:

            if "HOUR_VMSTAT" in stat_file and "html" in stat_file:

                file_without_ext=stat_file.split(".")
                csv_file_name=file_without_ext[0]+".csv"
                #self.system_memory_stats(csv_file_name,load_stats_path)
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>Server VMSTAT</h2></br>")
                        report_title_count+=1

                    load_report_write.write(content)
                    load_report_write.write('</tbody></table></body></html>')
                f.close()



        report_title_count=0

        for stat_file in stat_files:
            if "HOUR_SAR" in stat_file and "html" in stat_file:
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>Server SAR STAT</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</tbody></table></body></html>')
                    #file_without_ext=stat_file.split(".")
                    #csv_file_name=file_without_ext[0]+".csv"
                    #(csv_result_file,flag)=self.plot_sar_stats(csv_file_name,load_stats_path)

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>SAR Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                f.close()


        report_title_count=0

        for stat_file in stat_files:
            if "HOUR_IOSTAT" in stat_file and "html" in stat_file:

                file_without_ext=stat_file.split(".")
                csv_file_name=file_without_ext[0]+".csv"
                #self.system_iostat_stats(csv_file_name,load_stats_path)
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("writing io stat")
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>Server IOSTAT</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</tbody></table></body></html>')
                    #file_without_ext=stat_file.split(".")
                    #csv_file_name=file_without_ext[0]+".csv"
                    #(csv_result_file,flag)=self.plot_iostats(csv_file_name,load_stats_path)

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>IO Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                f.close()

        report_title_count=0

        for stat_file in stat_files:
            if "HOUR_NET_STATS" in stat_file and "html" in stat_file:
                f=open(load_stats_path+"/html/"+stat_file,'r')
                content=f.read()
                print("writing net stat")
                print("File Name : %s" %stat_file)
                print(content)

                with open(self.load_report_file,'a') as load_report_write:
                    if(report_title_count==0):
                        load_report_write.write("<div style=\"page-break-before:always\"></div>")
                        load_report_write.write("<h2>Server NETSTAT</h2></br>")
                        report_title_count+=1
                    load_report_write.write(content)
                    load_report_write.write('</br></table></body></html>')
                    #file_without_ext=stat_file.split(".")
                    #csv_file_name=file_without_ext[0]+".csv"
                    #(csv_result_file,flag)=self.plot_netstats(csv_file_name,load_stats_path)

                    #if(flag==1):
                        #print("Graph Printing disabled")
                        #load_report_write.write('</br><h2>Net Stats Graph</h2></br>')
                        #load_report_write.write('<img src="'+csv_result_file+'"/>')
                f.close()



        with open(self.load_report_file,'a') as load_report_write:
            load_report_write.write('</br><h2>Load Status : '+status_result+'</h2></br>')

        with open(self.load_report_file,'a') as load_report_write:
            load_report_write.write('</br><h2>Test Result Summary</h2></br>')
            load_report_write.write('<p>'+comments+'</p>')


        with open(self.load_report_file,'a') as load_report_write:
            load_report_write.write('</br><h2>Load DB Report Status : '+dbstatus_result+'</h2></br>')

        with open(self.load_report_file,'a') as load_report_write:
            load_report_write.write('</br><h2>Database Test Result Summary</h2></br>')
            load_report_write.write('<p>'+dbcomment+'</p>')
            load_report_write.write('</font>')


        mem_summary_text=""
        cpu_summary_text=""

        if(load_table_type==0):

            for (key,value) in self.max_memory.items():
                mem_summary_text+=key+" application was consuming maximum <b>"+value+"</b> of Memory</br>"

            for (key,value) in self.max_cpu.items():
                cpu_summary_text+=key+" application was taking maximum <b>"+value+"</b> of CPU</br>"

            with open(self.load_report_summary,'w') as load_report_write:
                load_report_write.write("<html><body><h3><u>Application Statistics Conclusions:</u></h3></br><p><b>Memory Utilization</b></br>")
                load_report_write.write(mem_summary_text)
                load_report_write.write("</br><b>CPU Utilization</b></br>")
                load_report_write.write(cpu_summary_text)

        elif(load_table_type==1):
     
            mem_summary_text+="<html><body><h3><u>Application Statistics Conclusions:</u></h3></br>"
            mem_summary_text+="<table border='1'><thead><tr><th>Application</th><th>Max Memory(MB)</th><th>Max CPU %</th></tr></thead><tbody><tr>"
            for (key,value) in self.max_memory.items():
                mem_summary_text+="<td>"+key+"</td><td>"+value+"</td><td>"+self.max_cpu[key]+"</td></tr>"
            mem_summary_text+="<tbody></table></body></html>"

            with open(self.load_report_summary,'w') as load_report_write:
                load_report_write.write(mem_summary_text)


        options = {'page-size': 'A4', 'dpi': 400, 'margin-top': '0.75in','margin-right': '0.75in','margin-bottom': '0.75in','margin-left': '0.75in','header-spacing': '5','header-line': '','header-html': '/opt/product/LOAD_GUI/bin/flaskr/templates/header.html','footer-left':  "Internal",'footer-center':  "NSS Load Test Report Template V1.0",'footer-right': '[page] of [topage]','footer-font-size': '10','footer-line': '','footer-spacing': '5','encoding': "UTF-8",'custom-header' : [('Accept-Encoding', 'gzip')] }

        pdfkit.from_file([self.load_report_current_title,self.load_report_current_exec_summary,self.load_report_summary,self.load_current_purpose_environment,self.load_report_file],self.load_report_pdf_file,configuration=config,options = options)

