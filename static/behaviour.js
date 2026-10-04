
function addInstanceHideShowChange(id1,id2) {
          document.getElementById(id1).style.display="block";
          document.getElementById(id2).style.display="none";
}



function showElement(id) {
          document.getElementById(id).style.display="block";
}

function hideElement(id) {
          document.getElementById(id).style.display="none";
}

function showHideOnState(id,state) {

          if(state=="STATEFULL") {
          document.getElementById(id).style.display="block";
          }
          else {
          document.getElementById(id).style.display="none";
          }

}


function showHideMGTSSeagullDiv(val) {

          console.log(val);

          if(val=="MGTS") {
            addInstanceHideShowChange("MGTS","SEAGULL");
            console.log("entered mgts if section");
          }
          else if(val=="SEAGULL") {
            addInstanceHideShowChange("SEAGULL","MGTS");
            console.log("entered seagull if section");
          }
          else {
          document.getElementById("MGTS").style.display="none";
          document.getElementById("SEAGULL").style.display="none";
          console.log("entered none if section");
          }

}


function showInstanceElements(id,instance_key) {

         try {

          document.getElementById(id).style.display="block";

          var entries_data = $('#my_entries_data').data("entries");
          var instances=entries_data[instance_key]
          fLen = instances.length;
          text = "<hr color=\"gray\"><ul>";

          for (i = 0; i < fLen; i++) {

            if (i < fLen-1) {

             text += "<li>" + instances[i] + "</li>";

            }
            else{
             text += "<li>" + instances[i] + "</li>";
            }

          }
          text += "</ul>";
          document.getElementById(id).innerHTML = text;
        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }

}

function selectProducts(id,key) {

         try {

          document.getElementById(id).style.display="block";

          var entries_data = $('#my_entries_data').data("entries");
          console.log(entries_data)
          console.log(key)
          var products=entries_data[key]
          console.log(products)
          var plen=products.length;
          text = "<hr color=\"gray\">";

          for (i = 0; i < plen; i++) {

             text += '<input type="radio" name="product" id="product" value="'+products[i]+'">' + products[i] + "</br></br>";

          }
          document.getElementById(id).innerHTML = text;
        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }
}
          



function showServers(id,prod,servers) {

         try {

          document.getElementById(id).style.display="block";
          console.log(servers)
          var server_lists=servers.split(",");
          var serv;
          fLen = server_lists.length;
          text = "<hr color=\"gray\">";
        
          for (i = 0; i < fLen; i++) {

            if (i < fLen-1) {

             serv=server_lists[i].slice(2,server_lists[i].length-1);

            }
            else{

             serv=server_lists[i].slice(2,server_lists[i].length-2);

            }
            console.log(serv)

               html_value=serv+";"+prod;

             text += '&emsp;<input type="radio" name="load_product_server" value="'+html_value+'" onclick=\'showInstanceElements("product_instance_list","'+html_value+'")\' required>'+serv+"</input></br></br>";

          }

          document.getElementById(id).innerHTML = text;
        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }

}


function startBkpServers(id,prod,servers,ctr) {

         try {

          document.getElementById(id).style.display="block";
          var server_lists=servers.split(",");
          var serv;
          fLen = server_lists.length;
          text = "<hr color=\"gray\">";
        
          for (i = 0; i < fLen; i++) {

            if (i < fLen-1) {

             serv=server_lists[i].slice(2,server_lists[i].length-1);

            }
            else{

             serv=server_lists[i].slice(2,server_lists[i].length-2);

            }

               html_value=serv+";"+prod;

             text += '&emsp;<input type="checkbox" name="load_product_server" value="'+html_value+'" onclick=\'startInstanceElements("product_instance_list'+id+ctr+'","'+html_value+'")\' >'+serv+"</input></br></br>";

          }

          document.getElementById(id).innerHTML = text;
        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }

}

function startServers(prod,id,ctr) {

          var element = document.createElement("div");
          divid=prod;
          element.id = divid;
          element.style.display="block"
          console.log(id);
          console.log(prod);
          document.getElementById(ctr).appendChild(element);

          var servers_data = $('#my_servers_data').data("servers");
          console.log(servers_data);
          servers=servers_data[prod];
          console.log(servers);

          var serv;
          sLen = servers.length;
          text = "<hr color=\"gray\"><h4>Product selected is "+prod+"</h4>";
        
          for (i = 0; i < sLen; i++) {

               serv=servers[i]
               html_value=serv+";"+prod;

             text += '&emsp;<input type="checkbox" name="load_server" value="'+html_value+'" onclick=\'startInstanceElements("'+prod+'","'+id+'","'+ctr+'","'+serv+'")\'>'+serv+"</input></br></br>";

          }

          console.log(text)

          document.getElementById(divid).innerHTML = text;

}


function startInstanceElements(prod,id,ctr,server) {

          console.log(id);
          console.log(prod);
          console.log(ctr)
          console.log(server)

          var element = document.createElement("div");
          divid=prod+server;
          element.id = divid;
          element.style.display="block"
          document.getElementById(prod).appendChild(element);


          current_server=server;

          console.log(current_server);


          var entries_data = $('#my_entries_data').data("entries");
          var entries_key=server+";"+prod;
          console.log(entries_data)

          var instance_lists=entries_data[entries_key];
          var inst;
          fLen = instance_lists.length;
          text = "<hr color=\"gray\"><h4>Server selected is "+current_server+"</h4>";

       
          for (i = 0; i < fLen; i++) {

               inst=instance_lists[i]
               html_value=current_server+";"+prod+";"+inst;



             text += '&emsp;<input type="checkbox" name="load_instances" value="'+html_value+'">'+inst+"</input></br></br>";

          }

          console.log(text)

          document.getElementById(divid).innerHTML = text;

}


function showSimulatorTypes(id,prod,servers) {

         try {

          text=""
 
          document.getElementById(id).style.display="block";

          var myDiv = document.getElementById(id);

          if(document.getElementById("simulator_type")) {
           var mySelect = document.getElementById("simulator_type");
           mySelect.remove();
          document.getElementById("server_list").style.display="none";
          }

          var simulators_data = $('#my_simulators_data').data("simulators");
          var simulators=simulators_data[prod];
          
          var selectList = document.createElement("select");
          selectList.id = "simulator_type";
          selectList.name = "simulator_type";
          selectList.className = "input";
          selectList.onchange = function(){showSimulators("server_list",selectList.id,prod,servers);};
          myDiv.appendChild(selectList);

          var option = document.createElement("option");
          option.value = "none";
          option.text = "--select--";
          selectList.appendChild(option);

          for (var i = 0; i < simulators.length; i++) {
             var option = document.createElement("option");
             option.value = simulators[i];
             option.text = simulators[i];
             selectList.appendChild(option);
          }

        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }

}


function showSimulators(id,selectid,prod,servers) {

         try {


          var simulator = document.getElementById(selectid).value;
          if(simulator!="none"){
          document.getElementById(id).style.display="block";
          }
          else{
          document.getElementById(id).style.display="none";
          }

          var server_lists=servers.split(",");
          var serv;
          fLen = server_lists.length;
          text = "<hr color=\"gray\">";
        
          for (i = 0; i < fLen; i++) {

            if (i < fLen-1) {

             serv=server_lists[i].slice(2,server_lists[i].length-1);

            }
            else {

             serv=server_lists[i].slice(2,server_lists[i].length-2);

            }

               html_value=serv+";"+simulator+";"+prod;

             text += '&emsp;<input type="radio" name="load_simulator" value="'+html_value+'" onclick=\'showInstanceElements("product_instance_list","'+html_value+'")\' required>'+serv+"</input></br></br>";

          }

          document.getElementById(id).innerHTML = text;

        }
        catch(err) {
        document.getElementById(id).innerHTML = err.message;
        }

}

function showMGTSTimesTimeout(id,val,times_id,timeout_id) {

          if (val=="mandatory") {
           document.getElementById(id).style.display="block";
          }
          else {
           document.getElementById(id).style.display="none";
           var times=document.getElementById(times_id);
           times.value=0;
           document.getElementById(timeout_id).value=0;
          }

}


function startSimulatorTypes(id,prod,ctr) {

         try {

          var element = document.createElement("div");
          divid=id
          element.id = divid;
          element.style.display="block"
          document.getElementById(ctr).appendChild(element);

          product=prod;
          counter=ctr;

          var simulators_data = $('#my_simulators_data').data("simulators");
          console.log(simulators_data);
          console.log(prod);
          simulators=simulators_data[prod];
          console.log(simulators);
          
          text = "<hr color=\"gray\">";
        
          for (i = 0; i < simulators.length; i++) {

             curr_sim=simulators[i];
             console.log(curr_sim);
             text += '&emsp;<input type="checkbox" id="simulator_type" name="simulator_type" value="'+simulators[i]+'" onclick=startSimulators(product,divid,counter,"'+curr_sim+'")>'+simulators[i]+'</input></br></br>'

           }
           text+="</div>";

          document.getElementById(divid).innerHTML = text;
          console.log(text)

        }
        catch(err) {
        document.getElementById(divid).innerHTML = err.message;
        }

}


function startSimulators(prod,id,ctr,simulator) {


          var element = document.createElement("div");
          divid=prod+simulator;
          element.id = divid;
          element.style.display="block"
          document.getElementById(prod).appendChild(element);

          current_simulator=simulator;

          console.log(id);
          console.log(current_simulator);


          var simulator_wise_server_list_data = $('#my_simulator_wise_server_list_data').data("simulator_wise_server_list");
          var simulator_wise_server_list_key=prod+";"+simulator;

          var server_lists=simulator_wise_server_list_data[simulator_wise_server_list_key];
          var serv;
          fLen = server_lists.length;
          text = "<hr color=\"gray\"><h4>Simulator selected is "+current_simulator+"</h4>";
        
          for (i = 0; i < fLen; i++) {

               serv=server_lists[i]
               html_value=serv+";"+current_simulator+";"+prod;

             text += '&emsp;<input type="checkbox" name="load_simulator" value="'+html_value+'" onclick=\'startScenarioElements("product_instance_list'+id+ctr+'","'+html_value+'")\' >'+serv+"</input></br></br>";

          }

          console.log(text)

          document.getElementById(divid).innerHTML = text;

}



function startScenarioElements(id,instance_key) {

         try {

          instance_array=instance_key.split(";");
          var element = document.createElement("div");
          divid=instance_key;
          element.id = divid;
          element.style.display="block";
          prod=instance_array[2]+instance_array[1];
          console.log(prod)
          document.getElementById(prod).appendChild(element);

          var entries_data = $('#my_entries_data').data("entries");
          console.log(entries_data);
          console.log(instance_key);
          var instances=entries_data[instance_key]
          console.log(instances);

          fLen = instances.length;
          text = "<hr color=\"gray\"><h4>Server selected is "+instance_array[0]+"</h4>";

          for (i = 0; i < fLen; i++) {

             text += '&emsp;&emsp;<input type="checkbox" name="load_instances" value="'+instance_key+";"+instances[i]+'" >'+instances[i]+"</input></br></br>";

          }
          document.getElementById(divid).innerHTML = text;
        }
        catch(err) {
        document.getElementById(divid).innerHTML = err.message;
        }

}

function searchAlias(id,str,button) {
    console.log(str)

    var xhttp; 
    if (str == "") {
        document.getElementById(id).innerHTML = "";
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById(id).innerHTML = this.responseText;
      }
    };
    xhttp.open("GET", "search_alias?search="+str+"&label="+button, true);
    xhttp.send();

}

function searchLoadQueries(id,str,button) {
    console.log(str)

    var xhttp; 
    if (str == "") {
        document.getElementById(id).innerHTML = "";
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById(id).innerHTML = this.responseText;
      }
    };
    xhttp.open("GET", "search_load_queries?search="+str+"&label="+button, true);
    xhttp.send();

}

function openNav() {
    document.getElementById("myNav").style.height = "100%";
}

function closeNav() {
    document.getElementById("myNav").style.height = "0%";
}

function searchStaticContent(id,hideid,url) {

    var xhttp; 
    addInstanceHideShowChange(id,hideid);
    if (url == "") {
        document.getElementById(id).innerHTML = "";
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById(id).innerHTML = this.responseText;
      }
    };
    xhttp.open("GET", url, true);
    xhttp.send();

}

function uploadContent(id,hideid,url) {

    var xhttp; 
    addInstanceHideShowChange(id,hideid);
    if (url == "") {
        document.getElementById(id).innerHTML = "";
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById(id).innerHTML = this.responseText;
      }
    };
    xhttp.open("POST", url, true);
    xhttp.send();

}

function processCheck(id,url) {

    var xhttp; 
    showElement(id);
    if (url == "") {
        document.getElementById(id).innerHTML = "";
        return;
    }
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById(id).innerHTML = this.responseText;
      }
    };
    xhttp.open("GET", url, true);
    xhttp.send();

}

