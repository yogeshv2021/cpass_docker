import json
import sqlite3
import threading
import xml.etree.ElementTree as ET

import cx_Oracle
import numpy as np
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Markup, \
    send_from_directory
from werkzeug.utils import secure_filename

from flaskr.xml_parse import *

app = Flask(__name__) # create the application instance :)

#app.config.from_object(__name__)  load config from this file , flaskr.py

#app.config.from_object('config')
app.config.from_envvar('FLASK_CONFIG')
print(app.config['CONFIG_FILE'])

app.config['DATABASE']=os.path.join(app.root_path, app.config['DATABASE'])
load_table_type=app.config['LOAD_SUMMARY_TABLE_TYPE']

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='load key',
    USERNAME='admin',
    PASSWORD='default',

))

print(app.config['DATABASE'])

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app_starter=ApplicationStarter(app.config['CONFIG_FILE'])
app_starter.config_list=[]
app_starter.config_read()

sim_starter = SimulatorStarter(app.config['CONFIG_FILE'],app_starter.start_time)
sim_starter.sim_config_list=[]
sim_starter.simulator_config_read()
app_stopper = ApplicationStopper(app_starter)

load_reporter = LoadReporter(app.config['UPLOAD_FOLDER'])
current_query = ""
query_exceptions = ""

def reset():
    app_starter=ApplicationStarter(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.config_read()
    sim_starter.sim_config_list=[]
    sim_starter = SimulatorStarter(app.config['CONFIG_FILE'],app_starter.start_time)
    sim_starter.simulator_config_read()
    app_stopper = ApplicationStopper(app_starter)


@app.route('/database')
def database():
    return render_template('database.html')

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def executeDBQueries(query,tup):
    db = get_db()
    cur=db.cursor()
    cur.execute(query,tup)
    db.commit()
    cur.close()
    db.close()


def executeDBSelectQueries(query,tup):
    db = get_db()
    cur=db.cursor()
    cur.execute(query,tup)
    rows=cur.fetchone()
    cur.close()
    db.close()
    return rows


def executeAllDBSelectQueries(query):
    db = get_db()
    cur=db.cursor()
    cur.execute(query)
    rows=cur.fetchall()
    db.commit()
    cur.close()
    db.close()
    return rows


@app.route('/add_alias')
def add_alias():
    headings=["Add DB Connection Information to be used in load"]
    return render_template('add_alias.html',headings=headings)

@app.route('/save_alias_config', methods=['GET', 'POST'])
def save_add_alias_config():
    alias_name=request.form['alias_name'].upper()
    db_type=request.form['db_type'].upper()
    user_name=request.form['user_name'].upper()
    password=request.form['password'].upper()
    database_ip=request.form['database_ip'].upper()
    service_name=request.form['service_name'].upper()

    query=''' insert into dblists(alias,db_type,username,password,ip_address,service_name) values(?,?,?,?,?,?) '''
    tup=(alias_name,db_type,user_name,password,database_ip,service_name)
    executeDBQueries(query,tup)

    flash('Alias added Successfully')

    return render_template('home.html')

@app.route('/edit_alias')
def edit_alias():
    headings=["Edit DB Connection Information to be used in load"]
    return render_template('edit_alias.html',headings=headings)

@app.route('/search_alias', methods=['GET', 'POST'])
def search_alias():

    alias_name="%"+request.args.get('search').upper()+"%"
    button_label=request.args.get('label')

    query=''' select db_type,username,password,ip_address,service_name,alias from dblists where alias like ? '''
    tup=(alias_name,)
    rows=executeDBSelectQueries(query,tup)
    if rows:
        (db_type,username,password,ip_address,service_name,alias_name)=rows
        print(db_type,username,password,ip_address,service_name)

        resp='''
         </br><label for="alias name">Alias Name</label></br>
         <input type="text" class="input_read_only" id="alias_name" name="alias_name" placeholder="Enter Alias Name for DB Connection String"  value="'''+alias_name+'" readonly></br>'

        resp+='''

        <label for="db type">Database Type</label>

        <select id="db_type" name="db_type" class="input" value="'''+db_type+'''" required>
         <option value="'''+db_type+'''" selected="selected">'''+db_type+'''</option>'''

        if db_type!="ORACLE":
            resp+=''' <option value="ORACLE">ORACLE</option> '''
        if db_type!="MSSQL":
            resp+=''' <option value="MSSQL">MSSQL</option> '''
        if db_type!="MYSQL":
            resp+=''' <option value="MYSQL">MYSQL</option> '''
        resp+="</select>"


        resp+='''
        <label for="user name">User Name</label></br>
        <input type="text" class="input" id="user_name" name="user_name" placeholder="Enter User Name of DB"  value="'''+username+'''" required></br>
        '''

        resp+='''
        <label for="Password">Password</label></br>
        <input type="text" class="input" id="password" name="password" placeholder="Enter Password of DB"  value="'''+password+'''" required></br>
        ''' 
        resp+='''
        <label for="database ip">Database IP Address</label></br>
        <input type="text" class="input" id="database_ip" name="database_ip" placeholder="Enter IP Address of the DB"  value="'''+ip_address+'''" required></br>
        '''

        resp+='''
        <label for="service name">Service Name</label></br>
        <input type="text" class="input" id="service_name" name="service_name" placeholder="Enter Service Name to be connected"  value="'''+service_name+'''" required></br>
        '''

        resp+='<input type=submit class="button" value='+button_label+'>'

        print(resp)
        return resp
    else:
        return "<b></br>Alias does not exist</b></br>"
    return render_template('home.html')


@app.route('/save_edit_alias_config', methods=['GET', 'POST'])
def save_edit_alias_config():
    alias_name=request.form['alias_name'].upper()
    db_type=request.form['db_type'].upper()
    user_name=request.form['user_name'].upper()
    password=request.form['password'].upper()
    database_ip=request.form['database_ip'].upper()
    service_name=request.form['service_name'].upper()

    query=''' update dblists set db_type=?,username=?,password=?,ip_address=?,service_name=? where alias=? '''
    tup=(db_type,user_name,password,database_ip,service_name,alias_name)
    executeDBQueries(query,tup)

    flash('Alias edited Successfully')

    return render_template('home.html')


@app.route('/delete_alias')
def delete_alias():
    headings=["Delete DB Connection Information to be used in load"]
    return render_template('delete_alias.html',headings=headings)

@app.route('/save_delete_alias_config', methods=['GET', 'POST'])
def save_delete_alias_config():
    alias_name=request.form['alias_name'].upper()

    query=''' delete from dblists where alias=? '''
    tup=(alias_name,)
    executeDBQueries(query,tup)

    flash('Alias deleted Successfully')

    return render_template('home.html')


@app.route('/add_load_queries')
def add_load_queries():
    headings=["Add Load DB Queries here"]
    return render_template('add_load_queries.html',headings=headings)

@app.route('/save_add_queries', methods=['GET', 'POST'])
def save_add_queries():
    load_alias_name=request.form['load_alias_name'].upper()
    load_queries_name=request.form['load_queries_name'].upper()

    query=''' insert into loadqueries(load_alias,dbqueries) values(?,?) '''
    tup=(load_alias_name,load_queries_name)
    executeDBQueries(query,tup)

    flash('Load Queries added Successfully')

    return render_template('home.html')

@app.route('/edit_load_queries')
def edit_load_queries():
    headings=["Edit Load DB Queries here"]
    return render_template('edit_load_queries.html',headings=headings)


@app.route('/search_load_queries', methods=['GET', 'POST'])
def search_load_queries():

    load_alias_name="%"+request.args.get('search').upper()+"%"
    button_label=request.args.get('label')

    query=''' select load_alias,dbqueries from loadqueries where load_alias like ? '''
    tup=(load_alias_name,)
    rows=executeDBSelectQueries(query,tup)
    if rows:
        (load_alias,dbqueries)=rows
        print(load_alias,dbqueries)

        resp='''
        </br><label for="load alias name">Load Alias Name</label></br>
        <input type="text" class="input_read_only" id="load_alias_name" name="load_alias_name" placeholder="Enter an Alias Name for Load"  value="'''+load_alias+'" readonly></br>'

        resp+='''
        <label for="load queries name">Load Queries</label></br>
        <textarea rows="4" cols="50" name="load_queries_name">'''+dbqueries+'''</textarea></br>'''

        resp+='<input type=submit class="button" value='+button_label+'>'
        return resp

    else:
        return "<b></br>Alias does not exist</b></br>"
    return render_template('home.html')


@app.route('/save_edit_load_queries', methods=['GET', 'POST'])
def save_edit_load_queries():
    load_alias_name=request.form['load_alias_name'].upper()
    load_queries_name=request.form['load_queries_name'].upper()

    query=''' update loadqueries set dbqueries=? where load_alias=? '''
    tup=(load_queries_name,load_alias_name)
    executeDBQueries(query,tup)

    flash('Load Queries edited Successfully')

    return render_template('home.html')

@app.route('/delete_load_queries')
def delete_load_queries():
    headings=["Delete Load DB Queries here"]
    return render_template('delete_load_queries.html',headings=headings)

@app.route('/save_delete_load_queries', methods=['GET', 'POST'])
def save_delete_load_queries():
    load_alias_name=request.form['load_alias_name'].upper()

    query=''' delete from loadqueries where load_alias=? '''
    tup=(load_alias_name,)
    executeDBQueries(query,tup)

    flash('Load Queries deleted Successfully')

    return render_template('home.html')

@app.route('/execute_queries')
def execute_queries():
    headings=['Execute Queries based on DB selected and Load Type Chosen']
    alias_query="select alias from dblists;"
    queries_query="select load_alias from loadqueries;"

    alias_lists=[]
    load_lists=[]

    db = get_db()
    cur=db.cursor()
    cur.execute(alias_query)
    rows=cur.fetchall()

    for row in rows:
        for column in row:
            alias_lists.append(column)

    cur.execute(queries_query)
    rows=cur.fetchall()

    for row in rows:
        for column in row:
            load_lists.append(column)

    cur.close()
    db.close()

    return render_template('execute_queries.html',headings=headings,alias_lists=alias_lists,load_lists=load_lists)

@app.route('/execute_db_load_query', methods=['GET', 'POST'])
def execute_db_load_query():

    db_alias=request.form['db_alias']
    load_alias=request.form['load alias']

    print(db_alias)
    print(load_alias)
    alias_query="select username,password,ip_address,service_name,db_type from dblists where alias=?"
    load_query="select dbqueries from loadqueries where load_alias=?"

    db = get_db()
    cur=db.cursor()
    cur.execute(alias_query,(db_alias,))
    (username,password,ip_address,service_name,db_type)=cur.fetchone()
    cur.execute(load_query,(load_alias,))
    (queries)=cur.fetchone()
    cur.close()
    db.close()

    print(username,password,ip_address,service_name,db_type)
    print(queries[0])

    if db_type=="ORACLE":
        t4=threading.Thread(target=execute_oracle_db_load_query, args=(username,password,ip_address,service_name,queries[0],))
        t4.daemon=True
        if not t4.isAlive():
            print("starting DB thread")
            t4.start()


    global current_query
    global query_exceptions
    current_query = ""
    query_exceptions = ""

    flash("Executing Queries")
    return render_template('home.html')

def execute_oracle_db_load_query(username,password,ip_address,service_name,queries):

    connection_string=username+"/"+password+"@"+ip_address+"/"+service_name
    print(connection_string)

    con=cx_Oracle.connect(connection_string)
    cur = con.cursor()
    resp=""

    queries=queries.splitlines()
    for query in queries:
        query=query.strip()
        if query:
            try:
                print("Executing Query")
                global current_query
                current_query=query
                cur.execute(query)
                resp="Query executed successfully"
            except Exception as e:
                print(str(e))
                global query_exceptions
                query_exceptions+="Error in "+query+" with exception str(e)"
                resp="Query not executed successfully"

    con.commit()
    current_query="Query Executed Successfully"

    cur.close()
    con.close()
    return resp


@app.route('/current_query_check')
def current_query_check():
    resp="<b>Executing Query :</b></br>"
    resp+=current_query+"</br>"
    resp+="<b>Errors observed so far :</b></br>"
    if(query_exceptions):
        resp+=query_exceptions
    else:
        resp+="Nil"
    
    return resp


@app.route('/')
def show_entries():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/show_config')
def show_config():
    if not session.get('logged_in'):
        abort(401)
    products=[]
    app_starter.config_list=[]
    app_starter.config_read()
    print(app_starter.prod_instance_map)

    same_prod_in_diff_server_map={}

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Product you want to view configuration:']

    for key in app_starter.prod_instance_map.keys():
        prod=key.split(";")[1]
        if prod not in same_prod_in_diff_server_map:
            same_prod_in_diff_server_map[prod]=[key.split(";")[0]]
        else:
            same_prod_in_diff_server_map[prod].append(key.split(";")[0])

    print(same_prod_in_diff_server_map)

    entries=(json.dumps(app_starter.prod_instance_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    return render_template('show_config.html', entries=entries,headings=headings,same_prod_in_diff_server_map=same_prod_in_diff_server_map)


@app.route('/show_product_config', methods=['GET', 'POST'])
def show_product_config():
    if not session.get('logged_in'):
        abort(401)
    error = None
    if request.method == 'POST':
        prod=request.form['load_product_server']

    headings=[" "]
    entries={}
    print("product is %s" %prod)
     
    for instance in app_starter.prod_instance_map[prod]:

        entries[prod+";"+instance]=app_starter.instance_configuration_map[prod+";"+instance]

    return render_template('show_instances.html', entries=entries,product=prod,headings=headings)


@app.route('/edit_instance', methods=['GET', 'POST'])
def edit_instance():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Product you want to view configuration:']

    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    return render_template('edit_instance.html', entries=entries,headings=headings)


@app.route('/edit_instance_config', methods=['GET', 'POST'])
def edit_instance_config():
    if not session.get('logged_in'):
        abort(401)

    instance=request.form['load_instance']
    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    instance_config=app_starter.instance_configuration_map[instance]
    print(instance_config)

    headings=["Configured values for Instance "+instance.split(";")[2]]

    return render_template('edit_instance_config.html', instance=instance, instance_config=instance_config, headings=headings, entries=entries)


@app.route('/save_edit_instance_config', methods=['GET', 'POST'])
def save_edit_instance_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    server=request.form['server_id']
    server_tag=["server","id"]

    product=request.form['product_name']
    product_tag=["product","name"]

    instance=request.form['instance_name']
    instance_tag=["instance","name"]

    instance_starter_script=request.form['starter_script']
    instance_starter_script_tag=["instance_starter","name"]

    instance_logger=request.form['instance_logger']
    instance_logger_tag=["instance_logger_path","name"]

    dynamic_delete_mode=request.form['dynamic_delete_mode']
    dynamic_delete_mode_tag=["instance_logger_delete","name"]

    delete_file_count=request.form['delete_file_count']
    delete_file_count_tag=["instance_log_files_to_remain","name"]

    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)


    for serv in root.iter(server_tag[0]):
        print("server received from form : %s" %server)
        print("server received from file : %s" %serv.attrib.get(server_tag[1],''))

        if serv.attrib.get(server_tag[1],'')==server:
            print("server matched : %s" %server)

            for prod in serv.findall(product_tag[0]):
                if prod.get(product_tag[1])==product:

                    print("product matched : %s" %product)

                    for elem in prod.findall(instance_tag[0]):
                        if elem.get(instance_tag[1])==instance:

                            print("instance matched : %s" %instance)

                            inst_start_script=elem.find(instance_starter_script_tag[0])
                            old_inst_start_script_name=inst_start_script.get(instance_starter_script_tag[1])
                            if(instance_starter_script!=old_inst_start_script_name):
                                inst_start_script.set(instance_starter_script_tag[1],instance_starter_script)

                            inst_logger=elem.find(instance_logger_tag[0])
                            old_inst_logger_name=inst_logger.get(instance_logger_tag[1])
                            if(instance_logger!=old_inst_logger_name):
                                inst_logger.set(instance_logger_tag[1],instance_logger)

                            dyn_delete_mode=elem.find(dynamic_delete_mode_tag[0])
                            old_dyn_delete_mode_name=dyn_delete_mode.get(dynamic_delete_mode_tag[1])
                            if(dynamic_delete_mode!=old_dyn_delete_mode_name):
                                dyn_delete_mode.set(dynamic_delete_mode_tag[1],dynamic_delete_mode)

                            del_file_count=elem.find(delete_file_count_tag[0])
                            old_del_file_count_name=del_file_count.get(delete_file_count_tag[1])
                            if(delete_file_count!=old_inst_start_script_name):
                                del_file_count.set(delete_file_count_tag[1],delete_file_count)

                            loop_flag=False
                            break

                if not loop_flag:
                    break

        if not loop_flag:
            break

    tree.write(app.config['CONFIG_FILE'])

    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()

    flash('Instance Edited Successfully')

    headings=['Choose a Product you want to view configuration:']
    print("entries are %s" %entries)

    return render_template('edit_instance.html', entries=entries,headings=headings)


@app.route('/add_instance')
def add_instance():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new instance configuration"]
    return render_template('add_instance.html',servers=app_starter.app_server_map,headings=headings)

@app.route('/add_instance_config',methods=['GET', 'POST'])
def add_instance_config():
    if not session.get('logged_in'):
        abort(401)

    server_id_index=0
    product_index=1

    headings=["Add a new instance configuration"]
    server=request.form['load_server']
    instance_config=app_starter.app_server_map[server]
    product_array=np.array(app_starter.gui_config_list)
    products=set(product_array[np.where(product_array[:,server_id_index] == server)][:,product_index])
    return render_template('add_instance_config.html',server=server,headings=headings,instance_config=instance_config,products=products)

@app.route('/save_add_instance_config', methods=['GET', 'POST'])
def save_add_instance_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    server=request.args.get('server')
    server_tag=["server","id"]

    product=request.form['product_name']
    product_tag=["product","name"]

    instance=request.form['instance_name']
    instance_tag=["instance","name"]

    instance_starter_script=request.form['starter_script']
    instance_starter_script_tag=["instance_starter","name"]

    instance_logger=request.form['instance_logger']
    instance_logger_tag=["instance_logger_path","name"]

    dynamic_delete_mode=request.form['dynamic_delete_mode']
    dynamic_delete_mode_tag=["instance_logger_delete","name"]

    delete_file_count=request.form['delete_file_count']
    delete_file_count_tag=["instance_log_files_to_remain","name"]

    inst_tag=ET.Element(instance_tag[0])
    inst_tag.set(instance_tag[1],instance)

    inst_starter_tag=ET.Element(instance_starter_script_tag[0])
    inst_starter_tag.set(instance_starter_script_tag[1],instance_starter_script)
    inst_tag.append(inst_starter_tag)

    inst_logger_tag=ET.Element(instance_logger_tag[0])
    inst_logger_tag.set(instance_logger_tag[1],instance_logger)
    inst_tag.append(inst_logger_tag)

    dyn_delete_mode_tag=ET.Element(dynamic_delete_mode_tag[0])
    dyn_delete_mode_tag.set(dynamic_delete_mode_tag[1],dynamic_delete_mode)
    inst_tag.append(dyn_delete_mode_tag)

    del_file_count_tag=ET.Element(delete_file_count_tag[0])
    del_file_count_tag.set(delete_file_count_tag[1],delete_file_count)
    inst_tag.append(del_file_count_tag)

    for serv in root.iter(server_tag[0]):
        if serv.attrib.get(server_tag[1],'')==server:

            for prod in serv.findall(product_tag[0]):

                if prod.get(product_tag[1])==product:
                    prod.append(inst_tag)
                    break


    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()
    print(ET.tostring(root))

    flash('Instance Added Successfully')

    return redirect(url_for('show_config'))


@app.route('/delete_instance', methods=['GET', 'POST'])
def delete_instance():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Product you want to view configuration:']
    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    return render_template('delete_instance.html', entries=entries,headings=headings)


@app.route('/save_delete_instance_config', methods=['GET', 'POST'])
def save_delete_instance_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    received_key=request.form['load_instance'].split(";")

    server=received_key[0]
    server_tag=["server","id"]

    product=received_key[1]
    product_tag=["product","name"]

    instance=received_key[2]
    instance_tag=["instance","name"]
   

    for serv in root.iter(server_tag[0]):
        if serv.attrib.get(server_tag[1],'')==server:

            for prod in serv.findall(product_tag[0]):

                if prod.get(product_tag[1])==product:

                    for inst in prod.findall(instance_tag[0]):

                        if inst.get(instance_tag[1])==instance:
                            prod.remove(inst)
                            loop_flag=False
                            break

                if not loop_flag:
                    break

        if not loop_flag:
            break


    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()

    flash('Instance Deleted Successfully')

    return redirect(url_for('show_config'))



@app.route('/copy_instance', methods=['GET', 'POST'])
def copy_instance():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose the instance from which you want to copy :']
    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    return render_template('copy_instance.html', entries=entries,headings=headings)

@app.route('/save_copy_instance_config', methods=['GET', 'POST'])
def save_copy_instance_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    server_tag=["server","id"]
    product_tag=["product","name"]
    instance_tag=["instance","name"]
    instance_starter_script_tag=["instance_starter","name"]
    instance_logger_tag=["instance_logger_path","name"]
    dynamic_delete_mode_tag=["instance_logger_delete","name"]
    delete_file_count_tag=["instance_log_files_to_remain","name"]


    new_inst_tag=ET.Element(instance_tag[0])

    new_inst_starter_tag=ET.Element(instance_starter_script_tag[0])

    new_inst_logger_tag=ET.Element(instance_logger_tag[0])

    new_dyn_delete_mode_tag=ET.Element(dynamic_delete_mode_tag[0])

    new_del_file_count_tag=ET.Element(delete_file_count_tag[0])

    received_key=request.form['load_instance'].split(";")

    server=received_key[0]

    product=received_key[1]

    instance=received_key[2]

    new_instance=request.form['instance_name']
    new_inst_tag.set(instance_tag[1],new_instance)

    for serv in root.iter(server_tag[0]):
        print("server received from form : %s" %server)
        print("server received from file : %s" %serv.attrib.get(server_tag[1],''))

        if serv.attrib.get(server_tag[1],'')==server:
            print("server matched : %s" %server)

            for prod in serv.findall(product_tag[0]):
                if prod.get(product_tag[1])==product:

                    print("product matched : %s" %product)

                    for elem in prod.findall(instance_tag[0]):
                        if elem.get(instance_tag[1])==instance:

                            print("instance matched : %s" %instance)

                            inst_start_script=elem.find(instance_starter_script_tag[0])
                            old_inst_start_script_name=inst_start_script.get(instance_starter_script_tag[1])
                            new_inst_starter_tag.set(instance_starter_script_tag[1],old_inst_start_script_name)
                            new_inst_tag.append(new_inst_starter_tag)

                            inst_logger=elem.find(instance_logger_tag[0])
                            old_inst_logger_name=inst_logger.get(instance_logger_tag[1])
                            new_inst_logger_tag.set(instance_logger_tag[1],old_inst_logger_name)
                            new_inst_tag.append(new_inst_logger_tag)

                            dyn_delete_mode=elem.find(dynamic_delete_mode_tag[0])
                            old_dyn_delete_mode_name=dyn_delete_mode.get(dynamic_delete_mode_tag[1])
                            new_dyn_delete_mode_tag.set(dynamic_delete_mode_tag[1],old_dyn_delete_mode_name)
                            new_inst_tag.append(new_dyn_delete_mode_tag)

                            del_file_count=elem.find(delete_file_count_tag[0])
                            old_del_file_count_name=del_file_count.get(delete_file_count_tag[1])
                            new_del_file_count_tag.set(delete_file_count_tag[1],old_del_file_count_name)
                            new_inst_tag.append(new_del_file_count_tag)

                            loop_flag=False
                            prod.append(new_inst_tag)
                            break

                if not loop_flag:
                    break

        if not loop_flag:
            break

    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()

    flash('Instance copied Successfully')

    return redirect(url_for('show_config'))


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',[request.form['title'], request.form['text']])
    db.commit()
    print("Vehicle : %s" %request.form['vehicle'])
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/start_load')
def start_load():
#    if not session.get('logged_in'):
#        abort(401)

    products=[]
    servers={}
    app_starter.config_list=[]
    app_starter.config_read()
    print(app_starter.prod_instance_map)

    same_prod_in_diff_server_map={}

    server_id_index=14
    product_id_index=1
    instance_id_index=2

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose Products you want to start load with :']

    product_array=np.array(app_starter.config_list)

    for key in app_starter.prod_instance_map.keys():
        prod=key.split(";")[1]
        servers[prod]=list(set(product_array[np.where(product_array[:,product_id_index] == prod)][:,server_id_index]))

        if prod not in same_prod_in_diff_server_map:
            same_prod_in_diff_server_map[prod]=[key.split(";")[0]]
        else:
            same_prod_in_diff_server_map[prod].append(key.split(";")[0])

    print(same_prod_in_diff_server_map)

    entries=(json.dumps(app_starter.prod_instance_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    servers=(json.dumps(servers)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    return render_template('start_load.html', entries=entries,headings=headings,same_prod_in_diff_server_map=same_prod_in_diff_server_map,servers=servers)

@app.route('/selected_product', methods=['GET', 'POST'])
def selected_product():
    if not session.get('logged_in'):
        abort(401)

    selected_instances=request.form.getlist('load_instances')
    app_starter.new_config_list=[]
    print(selected_instances)

    for instance in selected_instances:
        print(instance)
        app_starter.new_config_list.append((app_starter.instance_configuration_map[instance]))

    print(app_starter.new_config_list)

    return redirect(url_for('start_simulator'))

@app.route('/auto_selected_product', methods=['GET', 'POST'])
def auto_selected_product():
#    if not session.get('logged_in'):
#        abort(401)

    app_starter.new_config_list=[]
    app_starter.new_config_list=app_starter.config_list

    print(app_starter.new_config_list)

    return redirect(url_for('start_simulator'))


@app.route('/bring_up_applications')
def bring_up_applications():
    if not session.get('logged_in'):
        abort(401)

    print("\nstarting DUT server applications...Please wait...\n")

    app_starter.stop_load()
    print("\n stopped load")
    time.sleep(2)

    app_starter.start_load()
    print("\n started load")
    time.sleep(2)

    """ initiate thread of application starter calss """
    app_starter.daemon=True
    if not app_starter.isAlive():
        app_starter.start()

    print("\n app starter start thread started")
    print(app_stopper.stop_choice)
    time.sleep(2)

    """ invoke dynamic log deleter thread """
    t1=threading.Thread(target=call_log_deleter, args=(app_starter,))
    t1.daemon=True
    print(type(t1))
    if not t1.isAlive():
        t1.start()

    print("\n dynamic log thread started")
    print(app_stopper.stop_choice)
    time.sleep(2)

    """ invoke app live check thread """
    t2=threading.Thread(target=app_live_check, args=(app_starter,))
    t2.daemon=True
    if not t2.isAlive():
        t2.start()
    print("\n app live check started")

    print(app_stopper.stop_choice)
    time.sleep(2)

    """ invoke thread to monitor exit status of load """
    if not app_stopper.isAlive():
        app_stopper.start()
    print("\n app stopper thread started")
    print(app_stopper.stop_choice)
    time.sleep(2)

    print('Load Applications brought up Successfully')
    flash('Load Applications brought up Successfully')
    return redirect(url_for('simulator_choice_list'))



@app.route('/start_process_monitor_threads')
def start_process_monitor_threads():
#    if not session.get('logged_in'):
#        abort(401)

    app_starter.monitor_load()

    """ initiate thread of application starter calss """
    app_starter.daemon=True
    if not app_starter.isAlive():
        app_starter.start()

    print("\n app starter start thread started")
    print(app_stopper.stop_choice)
    time.sleep(2)


    """ invoke app live check thread """
    t2=threading.Thread(target=app_live_check, args=(app_starter,))
    t2.daemon=True
    if not t2.isAlive():
        t2.start()
    print("\n app live check started")
    

    """ invoke thread to monitor exit status of load """
    if not app_stopper.isAlive():
        app_stopper.start()
    print("\n app stopper thread started")
    print(app_stopper.stop_choice)
    time.sleep(2)

    print('Load Applications Stats Collection Starts')
    flash('Load Applications Stats Collection Starts')
    return redirect(url_for('simulator_choice_list'))




@app.route('/stop_entire_load')
def stop_entire_load():
    if not session.get('logged_in'):
        abort(401)

    app_stopper.stop_choice="exit"
    flash('Load stopped Successfully')
    return render_template('home.html')


@app.route('/show_sim_config')
def show_sim_config():
    if not session.get('logged_in'):
        abort(401)
    sim_products=[]
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()

    simulator_index=1
    product_id_index=13

    product_array=np.array(sim_starter.sim_config_list)


    same_sim_prod_in_diff_server_map={}
    simulators={}

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Simulator Product you want to view configuration:']

    for key in sim_starter.sim_prod_instance_map.keys():
        prod=key.split(";")[2]

        simulators[prod]=list(set(product_array[np.where(product_array[:,product_id_index] == prod)][:,simulator_index]))

        if prod not in same_sim_prod_in_diff_server_map:
            same_sim_prod_in_diff_server_map[prod]=[key.split(";")[0]]
        else:
            same_sim_prod_in_diff_server_map[prod].append(key.split(";")[0])
            same_sim_prod_in_diff_server_map[prod]=list(set(same_sim_prod_in_diff_server_map[prod]))


    entries=(json.dumps(sim_starter.sim_prod_instance_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    
    simulators=(json.dumps(simulators)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    return render_template('show_sim_config.html', entries=entries,headings=headings,same_sim_prod_in_diff_server_map=same_sim_prod_in_diff_server_map,simulators=simulators)


@app.route('/show_scenarios_config', methods=['GET', 'POST'])
def show_scenarios_config():
    if not session.get('logged_in'):
        abort(401)
    error = None
    if request.method == 'POST':
        scen=request.form['load_simulator']

    headings=[" "]
    entries={}
     
    for scenario in sim_starter.sim_prod_instance_map[scen]:

        entries[scen+";"+scenario]=sim_starter.scenario_configuration_map[scen+";"+scenario]

    return render_template('show_scenarios.html', entries=entries,scenario=scen,headings=headings)


@app.route('/edit_scenario', methods=['GET', 'POST'])
def edit_scenario():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Scenario you want to edit configuration:']
    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    return render_template('edit_scenario.html', entries=entries,headings=headings)


@app.route('/edit_scenario_config', methods=['GET', 'POST'])
def edit_scenario_config():
    if not session.get('logged_in'):
        abort(401)

    scenario=request.form['load_scenario']

    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    scenario_config=sim_starter.scenario_configuration_map[scenario]
    print(scenario_config)

    headings=["Configured values for scenario"+scenario.split(";")[2]]

    return render_template('edit_scenario_config.html', scenario=scenario, scenario_config=scenario_config, headings=headings,entries=entries)


@app.route('/save_edit_scenario_config', methods=['GET', 'POST'])
def save_edit_scenario_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True
    server_id_index=9
    simulator_id_index=1
    simulator_product_id_index=13
    scenario_id_index=4


    server=request.form['server_id']
    server_tag=["server","id"]

    print("server is %s" %server)

    simulator=request.form['simulator_name']
    simulator_tag=["simulator","name"]
    print("simulator is %s" %simulator)

    simulator_product=request.form['simulator_product_name']
    simulator_product_tag=["simulator_product","name"]
    print("simulator_product is %s" %simulator_product)

    scenario=request.form['scenario_name']
    scenario_tag=["scenario","name"]
    print("scenario is %s" %scenario)

    scenario_starter_script=request.form['starter_script']
    scenario_starter_script_tag=["scenario_starter","name"]

    scenario_call_rate=request.form['call_rate']
    scenario_call_rate_tag=["scenario_callrate","name"]

    scenario_url=request.form['scenario_url']
    scenario_url_tag=["scenario_url","name"]
    scenario_type_tag=["scenario_type","name","times","timeout"]

    if simulator=="SEAGULL":
        scenario_stats=request.form['stats_file']
        scenario_stats_tag=["scenario_stats","name"]


    scenario_mode=request.form['scenario_mode']
    scenario_mode_tag=["scenario_mode","name"]
    print("scenario_mode")
    print(scenario_mode)

    if(scenario_mode=="STATEFULL"):
        initial_count=request.form['initial_count']
        initial_count_tag=["initial_count","name"]
        update_count=request.form['update_count']
        update_count_tag=["update_count","name"]
        terminate_count=request.form['terminate_count']
        terminate_count_tag=["terminate_count","name"]
        onhold_time=request.form['onhold_time']
        onhold_time_tag=["onhold_time","name"]

    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    if simulator=="MGTS":
        scenario_times=request.form['scenario_times']
        scenario_timeout=request.form['scenario_timeout']


    for serv in root.iter(server_tag[0]):

        if serv.attrib.get(server_tag[1],'')==server:
            print("server attrib matches")

            for sim in serv.findall(simulator_tag[0]):

                if sim.get(simulator_tag[1])==simulator:

                    print("simulator matches")

                    for sim_prod in sim.findall(simulator_product_tag[0]):

                        if sim_prod.get(simulator_product_tag[1])==simulator_product:

                            print("simulator product matches")

                            for elem in sim_prod.findall(scenario_tag[0]):
                                if elem.get(scenario_tag[1])==scenario:

                                    print("scenario matches")
                                    swap_edit_elements(elem,scenario_starter_script_tag[0],scenario_starter_script_tag[1],scenario_starter_script)
                                    swap_edit_elements(elem,scenario_call_rate_tag[0],scenario_call_rate_tag[1],scenario_call_rate)

                                    if simulator!="MGTS":
                                        swap_edit_elements(elem,scenario_url_tag[0],scenario_url_tag[1],scenario_url)
                                        if simulator=="SEAGULL":
                                            swap_edit_elements(elem,scenario_stats_tag[0],scenario_stats_tag[1],scenario_stats)

                                    elif simulator=="MGTS":
                                        swap_edit_elements(elem,scenario_type_tag[0],scenario_type_tag[1],scenario_url)
                                        swap_edit_elements(elem,scenario_type_tag[0],scenario_type_tag[2],scenario_times)
                                        swap_edit_elements(elem,scenario_type_tag[0],scenario_type_tag[3],scenario_timeout)

                                    scen_mode=swap_edit_elements(elem,scenario_mode_tag[0],scenario_mode_tag[1],scenario_mode)

                                    if scenario_mode=="STATEFULL":

                                        swap_edit_elements(scen_mode,initial_count_tag[0],initial_count_tag[1],initial_count)
                                        swap_edit_elements(scen_mode,update_count_tag[0],update_count_tag[1],update_count)
                                        swap_edit_elements(scen_mode,terminate_count_tag[0],terminate_count_tag[1],terminate_count)
                                        swap_edit_elements(scen_mode,onhold_time_tag[0],onhold_time_tag[1],onhold_time)


                                    loop_flag=False
                                    break

                                input("choice")

                        if not loop_flag:
                            break

                if not loop_flag:
                    break

            if not loop_flag:
                break

    tree.write(app.config['CONFIG_FILE'])
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()

    print("save edit scenario")
    print(len(sim_starter.new_sim_config_list))

    if(len(sim_starter.new_sim_config_list)>0):
        print("length greater than 0")

        for i in range(len(sim_starter.sim_config_list)):
            print("inside for loop for sim config list : %d" %i)

            if(sim_starter.sim_config_list[i][server_id_index]==server and sim_starter.sim_config_list[i][simulator_id_index]==simulator and sim_starter.sim_config_list[i][simulator_product_id_index]==simulator_product and sim_starter.sim_config_list[i][scenario_id_index]==scenario):
                print("inside if for sim config list : %d" %i)

                for j in range(len(sim_starter.new_sim_config_list)):
                    print("inside for loop for new sim config list : %d" %j)

                    if(sim_starter.new_sim_config_list[j][server_id_index]==server and sim_starter.new_sim_config_list[j][simulator_id_index]==simulator and sim_starter.new_sim_config_list[j][simulator_product_id_index]==simulator_product and sim_starter.new_sim_config_list[j][scenario_id_index]==scenario):
                            print("inside if for new sim config list : %d" %j)
                            sim_starter.new_sim_config_list[j]=sim_starter.sim_config_list[i]
                
        

    flash('Scenario Edited Successfully')
    headings=['Choose a Scenario you want to edit configuration:']

    return render_template('edit_scenario.html', entries=entries,headings=headings)


def swap_edit_elements(elem,tag,attrib,new_value):
    current_tag=elem.find(tag)
    old_value=current_tag.get(attrib)
    print(old_value)
    if(new_value!=old_value):
        current_tag.set(attrib,new_value)
    return current_tag


@app.route('/add_scenario')
def add_scenario():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new scenario configuration"]
    return render_template('add_scenario.html',servers=sim_starter.sim_server_map,headings=headings)

@app.route('/add_scenario_config',methods=['GET', 'POST'])
def add_scenario_config():
    if not session.get('logged_in'):
        abort(401)

    server_id_index=9
    product_index=13
    simulator_index=1

    headings=["Add a new instance configuration"]
    server=request.form['load_server']
    scenario_config=sim_starter.sim_server_map[server]
    product_array=np.array(sim_starter.sim_config_list)
    products=set(product_array[np.where(product_array[:,server_id_index] == server)][:,product_index])
    simulators=set(product_array[np.where(product_array[:,server_id_index] == server)][:,simulator_index])
    return render_template('add_scenario_config.html',server=server,headings=headings,scenario_config=scenario_config,products=products,simulators=simulators)



@app.route('/save_add_scenario_config',methods=['GET', 'POST'])
def save_add_scenario_config():

    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()
    loop_flag=True

    server=request.args.get('server')
    server_tag=["server","id"]

    simulator=request.form['simulator_name']
    simulator_tag=["simulator","name"]

    simulator_product=request.form['product_name']
    simulator_product_tag=["simulator_product","name"]

    scenario=request.form['scenario_name']
    scenario_tag=["scenario","name"]

    scenario_starter_script=request.form['starter_script']
    scenario_starter_script_tag=["scenario_starter","name"]

    scenario_callrate=request.form['call_rate']
    scenario_callrate_tag=["scenario_callrate","name"]

    scenario_url=request.form['scenario_url']
    scenario_url_tag=["scenario_url","name"]


    scenario_type=request.form['scenario_type']
    scenario_times=request.form['scenario_times']
    scenario_timeout=request.form['scenario_timeout']
    scenario_type_tag=["scenario_type","name","times","timeout"]

    scenario_mode=request.form['scenario_mode']
    scenario_mode_tag=["scenario_mode","name"]

    if(scenario_mode=="STATEFULL"):
        initial_count=request.form['initial_count']
        initial_count_tag=["initial_count","name"]
        update_count=request.form['update_count']
        update_count_tag=["update_count","name"]
        terminate_count=request.form['terminate_count']
        terminate_count_tag=["terminate_count","name"]
        onhold_time=request.form['onhold_time']
        onhold_time_tag=["onhold_time","name"]


    scen_tag=ET.Element(scenario_tag[0])
    scen_tag.set(scenario_tag[1],scenario)

    scen_starter_tag=ET.Element(scenario_starter_script_tag[0])
    scen_starter_tag.set(scenario_starter_script_tag[1],scenario_starter_script)
    scen_tag.append(scen_starter_tag)

    scen_callrate_tag=ET.Element(scenario_callrate_tag[0])
    scen_callrate_tag.set(scenario_callrate_tag[1],scenario_callrate)
    scen_tag.append(scen_callrate_tag)

    if simulator=="SEAGULL" or simulator=="SIPPY":
        scen_url_tag=ET.Element(scenario_url_tag[0])
        scen_url_tag.set(scenario_url_tag[1],scenario_url)
        scen_tag.append(scen_url_tag)

    elif simulator=="MGTS":
        scen_url_tag=ET.Element(scenario_type_tag[0])
        scen_url_tag.set(scenario_type_tag[1],scenario_type)
        scen_url_tag.set(scenario_type_tag[2],scenario_times)
        scen_url_tag.set(scenario_type_tag[3],scenario_timeout)
        scen_tag.append(scen_url_tag)

    if simulator=="SEAGULL":
        scenario_stats=request.form['stats_file']
        scenario_stats_tag=["scenario_stats","name"]
        scen_stats_tag=ET.Element(scenario_stats_tag[0])
        scen_stats_tag.set(scenario_stats_tag[1],scenario_stats)
        scen_tag.append(scen_stats_tag)

    scen_mode_tag=ET.Element(scenario_mode_tag[0])
    scen_mode_tag.set(scenario_mode_tag[1],scenario_mode)


    if(scenario_mode=="STATEFULL"):
        init_count_tag=ET.Element(initial_count_tag[0])
        init_count_tag.set(initial_count_tag[1],initial_count)
        scen_mode_tag.append(init_count_tag)

        upd_count_tag=ET.Element(update_count_tag[0])
        upd_count_tag.set(update_count_tag[1],update_count)
        scen_mode_tag.append(upd_count_tag)

        ter_count_tag=ET.Element(terminate_count_tag[0])
        ter_count_tag.set(terminate_count_tag[1],terminate_count)
        scen_mode_tag.append(ter_count_tag)

        on_hold_tag=ET.Element(onhold_time_tag[0])
        on_hold_tag.set(onhold_time_tag[1],onhold_time)
        scen_mode_tag.append(on_hold_tag)

    scen_tag.append(scen_mode_tag)

    for serv in root.iter(server_tag[0]):
        if serv.attrib.get(server_tag[1],'')==server:

            for sim in serv.findall(simulator_tag[0]):
                if sim.get(simulator_tag[1])==simulator:

                    for sim_prod in sim.findall(simulator_product_tag[0]):

                        if sim_prod.get(simulator_product_tag[1])==simulator_product:
                            sim_prod.append(scen_tag)
                            break

  
    tree.write(app.config['CONFIG_FILE'])
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()
    print(ET.tostring(root))

    flash('Scenario Added Successfully')

    return redirect(url_for('show_sim_config'))


@app.route('/delete_scenario', methods=['GET', 'POST'])
def delete_scenario():
    if not session.get('logged_in'):
        abort(401)

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Product you want to view configuration:']
    req=request.args.get('entries')
    req=req.replace("'","\"")
    entries=json.loads(req)

    return render_template('delete_scenario.html', entries=entries,headings=headings)


@app.route('/save_delete_scenario_config', methods=['GET', 'POST'])
def save_delete_scenario_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    received_key=request.form['load_scenario'].split(";")

    server=received_key[0]
    server_tag=["server","id"]

    simulator=received_key[1]
    simulator_tag=["simulator","name"]

    simulator_product=received_key[2]
    simulator_product_tag=["simulator_product","name"]

    scenario=received_key[3]
    scenario_tag=["scenario","name"]


    for serv in root.iter(server_tag[0]):
        if serv.attrib.get(server_tag[1],'')==server:

            for sim in serv.findall(simulator_tag[0]):
                if sim.get(simulator_tag[1])==simulator:

                    for sim_prod in sim.findall(simulator_product_tag[0]):

                        if sim_prod.get(simulator_product_tag[1])==simulator_product:

                            for scen in sim_prod.findall(scenario_tag[0]):

                                if scen.get(scenario_tag[1])==scenario:
                                    sim_prod.remove(scen)
                                    loop_flag=False
                                    break

                        if not loop_flag:
                            break

                if not loop_flag:
                    break

        if not loop_flag:
            break


    tree.write(app.config['CONFIG_FILE'])
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()

    flash('Scenario Deleted Successfully')

    return redirect(url_for('show_sim_config'))


@app.route('/start_simulator')
def start_simulator():
#    if not session.get('logged_in'):
#        abort(401)
    sim_products=[]
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()

    simulator_index=1
    product_id_index=13
    server_id_index=9

    product_array=np.array(sim_starter.sim_config_list)


    same_sim_prod_in_diff_server_map={}
    simulators={}
    simulator_wise_server_list={}

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Simulator Product you want to start load:']

    for key in sim_starter.sim_prod_instance_map.keys():
        prod=key.split(";")[2]
        simulator=key.split(";")[1]
        server=key.split(";")[0]
        simulator_wise_server_list_key=prod+";"+simulator

        simulators[prod]=list(set(product_array[np.where(product_array[:,product_id_index] == prod)][:,simulator_index]))
        simulator_wise_server_list[simulator_wise_server_list_key]=list(set(product_array[np.where((product_array[:,product_id_index] == prod) & (product_array[:,simulator_index] == simulator))][:,server_id_index]))

        if prod not in same_sim_prod_in_diff_server_map:
            same_sim_prod_in_diff_server_map[prod]=[key.split(";")[0]+";"+key.split(";")[1]]
        else:
            same_sim_prod_in_diff_server_map[prod].append(key.split(";")[0]+";"+key.split(";")[1])
            same_sim_prod_in_diff_server_map[prod]=list(set(same_sim_prod_in_diff_server_map[prod]))


    entries=(json.dumps(sim_starter.sim_prod_instance_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    
    simulators=(json.dumps(simulators)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));


    simulator_wise_server_list=(json.dumps(simulator_wise_server_list)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    return render_template('start_simulator.html', entries=entries,headings=headings,same_sim_prod_in_diff_server_map=same_sim_prod_in_diff_server_map,simulators=simulators,simulator_wise_server_list=simulator_wise_server_list)


@app.route('/start_monitor_simulator')
def start_monitor_simulator():
#    if not session.get('logged_in'):
#        abort(401)
    sim_products=[]
    sim_starter.sim_config_list=[]
    sim_starter.simulator_config_read()

    simulator_index=1
    product_id_index=13
    server_id_index=9

    product_array=np.array(sim_starter.sim_config_list)


    same_sim_prod_in_diff_server_map={}
    simulators={}
    simulator_wise_server_list={}

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Simulator Product you want to start load:']

    for key in sim_starter.sim_prod_instance_map.keys():
        prod=key.split(";")[2]
        simulator=key.split(";")[1]
        server=key.split(";")[0]
        simulator_wise_server_list_key=prod+";"+simulator

        simulators[prod]=list(set(product_array[np.where(product_array[:,product_id_index] == prod)][:,simulator_index]))
        simulator_wise_server_list[simulator_wise_server_list_key]=list(set(product_array[np.where((product_array[:,product_id_index] == prod) & (product_array[:,simulator_index] == simulator))][:,server_id_index]))

        if prod not in same_sim_prod_in_diff_server_map:
            same_sim_prod_in_diff_server_map[prod]=[key.split(";")[0]+";"+key.split(";")[1]]
        else:
            same_sim_prod_in_diff_server_map[prod].append(key.split(";")[0]+";"+key.split(";")[1])
            same_sim_prod_in_diff_server_map[prod]=list(set(same_sim_prod_in_diff_server_map[prod]))


    entries=(json.dumps(sim_starter.sim_prod_instance_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    
    simulators=(json.dumps(simulators)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));


    simulator_wise_server_list=(json.dumps(simulator_wise_server_list)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'));

    return render_template('start_monitor_simulator.html', entries=entries,headings=headings,same_sim_prod_in_diff_server_map=same_sim_prod_in_diff_server_map,simulators=simulators,simulator_wise_server_list=simulator_wise_server_list)




@app.route('/selected_simulator', methods=['GET', 'POST'])
def selected_simulator():
    if not session.get('logged_in'):
        abort(401)

    selected_scenarios=request.form.getlist('load_instances')
    print(selected_scenarios)
    sim_starter.new_sim_config_list=[]

    for scenario in selected_scenarios:
        print(scenario)
        sim_starter.new_sim_config_list.append((sim_starter.scenario_configuration_map[scenario]))


    return redirect(url_for('bring_up_applications'))
    """ return redirect(url_for('simulator_choice_list')) """



@app.route('/selected_monitor_simulator', methods=['GET', 'POST'])
def selected_monitor_simulator():
    if not session.get('logged_in'):
        abort(401)

    selected_scenarios=request.form.getlist('load_instances')
    print(selected_scenarios)
    sim_starter.new_sim_config_list=[]

    for scenario in selected_scenarios:
        print(scenario)
        sim_starter.new_sim_config_list.append((sim_starter.scenario_configuration_map[scenario]))


    return redirect(url_for('start_process_monitor_threads'))

@app.route('/auto_selected_simulator', methods=['GET', 'POST'])
def auto_selected_simulator():
    if not session.get('logged_in'):
        abort(401)

    sim_starter.new_sim_config_list=[]
    sim_starter.new_sim_config_list=sim_starter.sim_config_list

    return redirect(url_for('bring_up_applications'))
    """ return redirect(url_for('simulator_choice_list')) """


@app.route('/auto_selected_monitor_simulator', methods=['GET', 'POST'])
def auto_selected_monitor_simulator():
#    if not session.get('logged_in'):
#        abort(401)

    sim_starter.new_sim_config_list=[]
    sim_starter.new_sim_config_list=sim_starter.sim_config_list

    return redirect(url_for('start_process_monitor_threads'))


@app.route('/simulator_choices', methods=['GET', 'POST'])
def simulator_choices():
#    if not session.get('logged_in'):
#        abort(401)

    simulator_choice=request.form['simulator_choices']
    print(simulator_choice)
    simulator_choice_int=int(simulator_choice)

    if(simulator_choice_int>=7 and simulator_choice_int<=12):
        return redirect(url_for('specific_scenario_choose',simulator_choice=simulator_choice))

    stats_from_file_type=app.config['SEAGULL_STATS_FROM_CSV_FILE']

    result=sim_starter.gui_simulator_choice_list(simulator_choice_int,app.root_path,stats_from_file_type)
    if(result):
        results= result.splitlines()
        for line in results:
            flash(Markup(line))
    else:
        flash(result)

    return redirect(url_for('simulator_choice_list'))


@app.route('/simulator_choice_list', methods=['GET', 'POST'])
def simulator_choice_list():
#    if not session.get('logged_in'):
#        abort(401)

    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a load operation you want to perform :']

    return render_template('simulator_choice_list.html',headings=headings)


@app.route('/specific_scenario_choose')
def specific_scenario_choose():
    if not session.get('logged_in'):
        abort(401)

    choice=request.args.get('simulator_choice')

    scenario_index=4

    headings=['Choose a respective scenario :']
    product_array=np.array(sim_starter.new_sim_config_list)
    scenarios=sorted(list(set(product_array[:,scenario_index])))
    print(scenarios)

    return render_template('specific_scenario_choose.html',headings=headings,scenarios=scenarios,choice=choice)


@app.route('/selected_specific_scenarios', methods=['GET', 'POST'])
def selected_specific_scenarios():
    if not session.get('logged_in'):
        abort(401)

    sim_starter.scen_choice_list=[]
    curr_choice=int(request.args.get('choice'))
    selected_scenarios=request.form.getlist('load_scenarios')
    sim_starter.scen_choice_list=selected_scenarios
    stats_from_file_type=app.config['SEAGULL_STATS_FROM_CSV_FILE']

    result=sim_starter.gui_simulator_choice_list(curr_choice,app.root_path,stats_from_file_type)
    if(result):
        results= result.splitlines()
        for line in results:
            if(curr_choice==6 or curr_choice==12):
                flash(Markup(line))
            else:
                flash(line)
    else:
        flash(result)

    return redirect(url_for('simulator_choice_list'))


@app.route('/start_simulator_alive_check', methods=['GET', 'POST'])
def start_simulator_alive_check():

    """ invoke sim live check thread """
    t3=threading.Thread(target=sim_live_check, args=(sim_starter,))
    t3.daemon=True
    if not t3.isAlive():
        print("starting thread")
        t3.start()
    print("\n sim live check started")
    return "<b>Simulator Process Alive Check Started</b></br>"


@app.route('/stop_simulator_alive_check', methods=['GET', 'POST'])
def stop_simulator_alive_check():
    sim_starter.load_sim_stop_is_application_alive_flag=1
    return "<b>Simulator Process Alive Check Stopped</b></br>"


@app.route('/prepare_load_report')
def prepare_load_report():
#    if not session.get('logged_in'):
#        abort(401)

    headings=['Load Report Preparation']

    load_stats_base_path=app_starter.root.find('stats_path').attrib['name']
    print(load_stats_base_path)
    stats_dir=os.listdir(load_stats_base_path)
    stats_dir=sorted(stats_dir,reverse=True)
    print(stats_dir)

    return render_template('prepare_load_report.html',headings=headings,dir=stats_dir,load_stats_base_path=load_stats_base_path)


@app.route('/proceed_load_report_preparation', methods=['GET', 'POST'])
def proceed_load_report_preparation():
#    if not session.get('logged_in'):
#        abort(401)

    prepared=request.form['prepared_by']
    product_by=request.form['product_by']
    reviewed=request.form['reviewed_by']
    approved=request.form['approved_by']
    start_date=request.form['start_date']
    report_date=request.form['report_date']
    stats_path=request.form['stats_path']
    load_duration=request.form['load_duration']
    status_result=request.form['status_result']
    dbstatus_result=request.form['dbstatus_result']
    comment=request.form['comment']
    comment=comment.replace("\n","</br>")
    dbcomment=request.form['dbcomment']
    dbcomment=dbcomment.replace("\n","</br>")


    load_reporter.prepare_report(prepared,reviewed,approved,start_date,report_date,stats_path,comment,status_result,dbstatus_result,dbcomment,product_by,load_table_type,load_duration)

    messages = json.dumps({"filename":"load_report.pdf","path":stats_path})

    flash("Load Report Prepared Successfully")

    download_link_tag='<a href="'+url_for('download',messages=messages)+'" class="ahref">Download Report</a>'


    """ return redirect(url_for('download',messages=messages)) """

    flash(Markup(download_link_tag))

    return render_template('home.html')


@app.route('/download_load_report')
def download_load_report():
    if not session.get('logged_in'):
        abort(401)

    headings=['Load Report Download']

    load_stats_base_path=app_starter.root.find('stats_path').attrib['name']
    print(load_stats_base_path)
    stats_dir=os.listdir(load_stats_base_path)
    stats_dir=sorted(stats_dir,reverse=True)
    print(stats_dir)

    return render_template('download_load_report.html',headings=headings,dir=stats_dir,load_stats_base_path=load_stats_base_path)

@app.route('/proceed_download', methods=['GET', 'POST'])
def proceed_download():

    stats_path=request.form['stats_path']

    messages = json.dumps({"filename":"load_report.pdf","path":stats_path})
    messages=json.loads(messages)
    print(messages)
    filename=messages['filename']
    path=messages['path']
    
    return send_from_directory(directory=path, filename=filename,as_attachment=True)


@app.route('/download')
def download():

    messages=request.args.get("messages")
    messages=json.loads(messages)
    print(messages)
    filename=messages['filename']
    path=messages['path']
    
    return send_from_directory(directory=path, filename=filename,as_attachment=True)

def file_store(picture_url):
    response = redirect(picture_url) #url is definitely correct
    picture = sqlite3.Binary(response)
    con = sqlite3.connect(db_filename)
    cursor = con.cursor()
    file_name="test.pdf"
    sql = '''INSERT INTO files (filename,content) VALUES (?, ?)'''
    cursor.execute(sql, (file_name, picture))
    cursor.execute(sql)
    con.commit()


@app.route('/get_load_stats')
def get_load_stats():

    new_sim_config_len=len(sim_starter.new_sim_config_list)
    sim_config_len=len(sim_starter.sim_config_list)

    if(sim_config_len<=0):
        sim_starter.simulator_config_read()

    if(new_sim_config_len<=0):
        sim_starter.new_sim_config_list=sim_starter.sim_config_list

    return redirect(url_for('simulator_choice_list'))


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return render_template('home.html')


""" Load Report Static Files Editing """

@app.route('/edit_static_report')
def edit_static_report():

    return render_template('edit_static_report.html')

def get_content_from_static_file(file,iso_flag):
    try:

        if not iso_flag:
            with open(file,'r') as gui_read:
                content=gui_read.read()

        else:
            with open(file,'r',encoding = "ISO-8859-1") as gui_read:
                content=gui_read.read()

        return content
    except:
        return "<h3>File Not Found</h3>"


@app.route('/write_content_to_static_file', methods=['GET', 'POST'])
def write_content_to_static_file():

    file=request.form['file_name']
    content=request.form['edited_content']

    with open(file,'w') as gui_write:
        gui_write.write(content)

    return render_template('home.html')

@app.route('/edit_execution_summary')
def edit_execution_summary():
    file=load_reporter.load_execution_summary
    content=get_content_from_static_file(file,0)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value='+file+'></br>'
    result+="</br><label>Edit Content Here</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    return(result)
    return render_template('home.html')

@app.route('/edit_callrate')
def edit_callrate():
    file=load_reporter.load_report_call_rate
    content=get_content_from_static_file(file,0)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value='+file+'></br>'
    result+="</br><label>Edit Content Here in CSV Format</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    return(result)
    return render_template('home.html')

@app.route('/edit_purpose')
def edit_purpose():
    file=load_reporter.load_purpose_environment
    content=get_content_from_static_file(file,0)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value='+file+'></br>'
    result+="</br><label>Edit Content Here</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    return(result)
    return render_template('home.html')

@app.route('/edit_environment')
def edit_environment():
    file=load_reporter.load_environment_details
    content=get_content_from_static_file(file,1)
    print(content)
    content=content+"content"
    print(content)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value="'+file+'"></br>'
    result+="</br><label>Edit Content Here in CSV Format</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    print(result)
    return(result)
    return render_template('home.html')

@app.route('/edit_inhouse')
def edit_inhouse():
    file=load_reporter.load_inhouse_products
    content=get_content_from_static_file(file,1)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value='+file+'></br>'
    result+="</br><label>Edit Content Here in CSV Format</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    return(result)
    return render_template('home.html')

@app.route('/edit_architecture')
def edit_architecture():
    file=load_reporter.load_architecture
    content=get_content_from_static_file(file,0)
    result="</br><label>Static Template File Name</label></br>"
    result+='<input type="text" class="input" name="file_name" value='+file+'></br>'
    result+="</br><label>Edit Content Here</label></br>"
    result+='<textarea rows="4" cols="50" name="edited_content" value="">'+content+'</textarea></br>'
    result+='<input type="submit" class="button" value="Edit"></br>'
    return(result)
    return render_template('home.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_file',methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Architecture Uploaded Successfully')
            return redirect(url_for('home'))

    return render_template('architecture_image_upload.html')


""" End of Load Report Static Files Editing """


""" Product add,edit,delete configurations """

@app.route('/show_product_operations')
def show_product_operations():
    if not session.get('logged_in'):
        abort(401)

    return render_template('show_product_operations.html')

@app.route('/add_product')
def add_product():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new product configuration"]
    return render_template('add_product.html',servers=app_starter.app_server_map,headings=headings)

@app.route('/add_product_config',methods=['GET', 'POST'])
def add_product_config():
    if not session.get('logged_in'):
        abort(401)

    server_id_index=14
    product_index=1

    headings=["Add a new product configuration"]
    server=request.form['load_server']
    product_config=app_starter.app_server_map[server]
    product_array=np.array(app_starter.config_list)
    products=product_array[np.where(product_array[:,server_id_index] == server)]
    products=products[0]
    return render_template('add_product_config.html',server=server,headings=headings,products=products)

@app.route('/save_add_product_config', methods=['GET', 'POST'])
def save_add_product_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    server=request.args.get('server')
    server_tag=["server","id"]

    product=request.form['product_name']
    product_tag=["product","name"]

    sleep_time=request.form['sleep_name']
    sleep_time_tag=["sleep_time","name"]

    prod_tag=ET.Element(product_tag[0])
    prod_tag.set(product_tag[1],product)

    sleep_tag=ET.Element(sleep_time_tag[0])
    sleep_tag.set(sleep_time_tag[1],sleep_time)
    prod_tag.append(sleep_tag)


    for serv in root.iter(server_tag[0]):
        if serv.attrib.get(server_tag[1],'')==server:

            serv.append(prod_tag)
            break


    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()
    print(app_starter.config_list)
    print(ET.tostring(root))

    flash('Product Added Successfully')

    return redirect(url_for('add_product'))



@app.route('/edit_product', methods=['GET', 'POST'])
def edit_product():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Server you want to edit product configuration:']
    prod_server_map={}

    server_id_index=0
    product_index=1
    print(app_starter.gui_config_list)
    product_array=np.array(app_starter.gui_config_list)

    for server in app_starter.app_server_map.keys():
        prod_server_map[server]=list(set(product_array[np.where(product_array[:,server_id_index] == server)][:,product_index]))

    print("prod_server_map")
    print(prod_server_map)

    entries=(json.dumps(prod_server_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    return render_template('edit_product.html',headings=headings,prod_server_map=prod_server_map,entries=entries)


@app.route('/edit_product_config', methods=['GET', 'POST'])
def edit_product_config():
    if not session.get('logged_in'):
        abort(401)

    headings=["Edit a new product configuration"]
    product_index=1
    server=request.form['load_server']
    product=request.form['product']
    print("product")
    print(product)
    product_array=np.array(app_starter.config_list)
    product_fields=product_array[np.where(product_array[:,product_index] == product)][0,:]
  
    return render_template('edit_product_config.html',server=server,headings=headings,products=product_fields)


@app.route('/save_edit_product_config', methods=['GET', 'POST'])
def save_edit_product_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    server=request.args.get('server')
    server_tag=["server","id"]

    product=request.form['product_name']
    product_tag=["product","name"]

    sleep_time=request.form['sleep_name']
    sleep_time_tag=["sleep_time","name"]

    for serv in root.iter(server_tag[0]):
        print("server received from form : %s" %server)
        print("server received from file : %s" %serv.attrib.get(server_tag[1],''))

        if serv.attrib.get(server_tag[1],'')==server:
            print("server matched : %s" %server)

            for prod in serv.findall(product_tag[0]):
                if prod.get(product_tag[1])==product:

                    print("product matched : %s" %product)

                    sleep_element=prod.find(sleep_time_tag[0])
                    old_sleep_time=sleep_element.get(sleep_time_tag[1])
                    if(sleep_time!=old_sleep_time):
                        sleep_element.set(sleep_time_tag[1],sleep_time)

                    loop_flag=False
                    break

        if not loop_flag:
            break

    tree.write(app.config['CONFIG_FILE'])

    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()
    print(app_starter.config_list)

    flash('Product Edited Successfully')

    headings=['Choose a Product you want to view configuration:']

    return redirect(url_for('edit_product'))


@app.route('/delete_product', methods=['GET', 'POST'])
def delete_product():
    if not session.get('logged_in'):
        abort(401)
    """ dictionary contains tag name as keys and values as start and end index of the pattern needs to be displayed in GUI"""
    headings=['Choose a Server you want to delete product configuration:']
    prod_server_map={}

    server_id_index=0
    product_index=1
    print(app_starter.gui_config_list)
    product_array=np.array(app_starter.gui_config_list)

    for server in app_starter.app_server_map.keys():
        prod_server_map[server]=list(set(product_array[np.where(product_array[:,server_id_index] == server)][:,product_index]))

    print("prod_server_map")
    print(prod_server_map)

    entries=(json.dumps(prod_server_map)
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    return render_template('delete_product.html',headings=headings,prod_server_map=prod_server_map,entries=entries)


@app.route('/save_delete_product_config', methods=['GET', 'POST'])
def save_delete_product_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    loop_flag=True

    server=request.form['load_server']
    server_tag=["server","id"]

    product=request.form['product']
    product_tag=["product","name"]

    for serv in root.iter(server_tag[0]):
        print("server received from form : %s" %server)
        print("server received from file : %s" %serv.attrib.get(server_tag[1],''))

        if serv.attrib.get(server_tag[1],'')==server:
            print("server matched : %s" %server)

            for prod in serv.findall(product_tag[0]):
                if prod.get(product_tag[1])==product:

                    print("product matched : %s" %product)

                    serv.remove(prod)

                    loop_flag=False
                    break

        if not loop_flag:
            break

    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()
    print(app_starter.config_list)

    flash('Product Deleted Successfully')

    headings=['Choose a Product you want to view configuration:']

    return redirect(url_for('delete_product'))



""" Server add,edit,delete configurations """

@app.route('/show_server_operations')
def show_server_operations():
    if not session.get('logged_in'):
        abort(401)

    return render_template('show_server_operations.html')

@app.route('/add_server')
def add_server():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new server configuration"]
    return render_template('add_server.html',headings=headings)

@app.route('/save_add_server_config', methods=['GET', 'POST'])
def save_add_server_config():
    if not session.get('logged_in'):
        abort(401)

    tree=ET.parse(app.config['CONFIG_FILE'])
    root=tree.getroot()

    server_id=request.form['server_name']
    server_name=request.form['server_ip']
    server_tag=["server","id","name"]

    server_type=request.form['server_type']
    server_type_tag=["server_type","name"]

    server_user=request.form['user_name']
    server_user_tag=["server_user","name"]

    server_key_path=request.form['ssh_key']
    server_key_path_tag=["server_key_path","name"]

    server_mode=request.form['server_mode']
    server_mode_tag=["server_mode","name"]

    server_prompt=request.form['server_prompt']
    server_prompt_tag=["server_prompt","name"]

    log_delete_sleep_interval=request.form['delete_frequency']
    log_delete_sleep_interval_tag=["log_delete_sleep_interval","name"]

    serv_tag=ET.Element(server_tag[0])
    serv_tag.set(server_tag[1],server_id)
    serv_tag.set(server_tag[2],server_name)

    serv_type_tag=ET.Element(server_type_tag[0])
    serv_type_tag.set(server_type_tag[1],server_type)
    serv_tag.append(serv_type_tag)

    serv_user_tag=ET.Element(server_user_tag[0])
    serv_user_tag.set(server_user_tag[1],server_user)
    serv_tag.append(serv_user_tag)

    serv_key_path_tag=ET.Element(server_key_path_tag[0])
    serv_key_path_tag.set(server_key_path_tag[1],server_key_path)
    serv_tag.append(serv_key_path_tag)

    serv_mode_tag=ET.Element(server_mode_tag[0])
    serv_mode_tag.set(server_mode_tag[1],server_mode)
    serv_tag.append(serv_mode_tag)

    serv_prompt_tag=ET.Element(server_prompt_tag[0])
    serv_prompt_tag.set(server_prompt_tag[1],server_prompt)
    serv_tag.append(serv_prompt_tag)


    serv_log_delete_sleep_interval_tag=ET.Element(log_delete_sleep_interval_tag[0])
    serv_log_delete_sleep_interval_tag.set(log_delete_sleep_interval_tag[1],server_prompt)
    serv_tag.append(serv_log_delete_sleep_interval_tag)

    root.append(serv_tag)
    ET.indent(root)


    tree.write(app.config['CONFIG_FILE'])
    app_starter.config_list=[]
    app_starter.gui_config_list=[]
    app_starter.app_server_map={}
    app_starter.prod_instance_map={}
    app_starter.config_read()
    print(app_starter.config_list)
    print(ET.tostring(root))

    flash('Server Added Successfully')

    return redirect(url_for('add_server'))

@app.route('/edit_server')
def edit_server():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new server configuration"]
    return render_template('add_server.html',headings=headings)

@app.route('/delete_server')
def delete_server():
    if not session.get('logged_in'):
        abort(401)

    headings=["Add a new server configuration"]
    return render_template('add_server.html',headings=headings)

""" End of Server add,edit,delete configurations """

""" Start of Active Process Check """
@app.route('/active_process_check')
def active_process_check():

    resp=app_starter.active_processes()
    print(resp)
    return(resp)


""" Start of Active Process Check
@app.route('/ows_profile_view')
def ows_profile_view():

    return render_template('OSW_profile.html')
"""

""" End of Active Process Check """



""" Start of Load Analysis GUI """

@app.route('/analyze_file_select')
def analyze_file_select():
    if not session.get('logged_in'):
        abort(401)

    headings=['Load Analysis ']

    load_stats_base_path=app_starter.root.find('stats_path').attrib['name']
    print(load_stats_base_path)
    stats_dir=os.listdir(load_stats_base_path)
    stats_dir=sorted(stats_dir,reverse=True)
    print(stats_dir)

    return render_template('load_analyzer.html',headings=headings,dir=stats_dir,load_stats_base_path=load_stats_base_path)

@app.route('/list_stat_files', methods=['GET', 'POST'])
def list_stat_files():

    path=request.args.get('path')
    files = os.listdir(os.path.join(load_stats_base_path,path))
    print(files)
    return(files)
    return render_template('home.html')






    




















