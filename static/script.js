function loadingData() {
    let theUrl = "http://127.0.0.1:5000/get_sql_ids"
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState === 4) {
            if (xmlHttp.status === 200) {

                let elements = JSON.parse(xmlHttp.responseText);
                let select = document.querySelector("#myid")
                for (let elt of elements) {
                    let option = document.createElement("option");
                    option.text = elt;
                    option.value = elt;
                    select.appendChild(option);
                }
                document.getElementById("loader").style.display = "none"
                document.getElementById("page").style.display = "block"
            } else {
                document.getElementById("loader").style.display = "none"
                document.getElementById("page").style.display = "block"
                showError("There is an internal server error \n " + xmlHttp.responseText)
            }
        }
    };
    xmlHttp.open("GET", theUrl);
    xmlHttp.send();
}


function show() {
    document.getElementById("loader-graph").style.display = "block"
    document.getElementById("div-table").style.display = "none"

    let days = document.getElementById("fname").value
    let e = document.getElementById("myid")
    let sql_id = e.value

    //remove the error message
    if (document.getElementById("error") != null)
        document.getElementById("error").remove()


    //remove previous plot
    document.getElementById("chart").remove()
    let child = document.createElement("div")
    child.id = "chart"
    document.getElementById("data").append(child)

    //remove the last updated time
    if (document.getElementById("lastRequest")!=null)
        document.getElementById("lastRequest").remove()

    //remove previous table
    if (document.getElementById("table-body") != null)
        document.getElementById("table-body").remove()


    let tableBody = document.createElement("tbody")
    tableBody.id = "table-body"
    let table = document.getElementById("table")
    table.appendChild(tableBody)

    if (document.getElementById("tab") != null) {
        document.getElementById("tab").remove()
        let table= document.getElementById("div-table")
        let tab = document.createElement("div")
        tab.id = "tab"
        table.insertBefore(tab,table.children[0])
    }
    showFigure(sql_id, days)
    showInfo(sql_id)
    return false;
}

function showFigure(sql_id, days) {
    if (days === "" || !Number.isInteger(Number(days)) || Number(days) <= 0) {
        showError("please enter valid days number")
    } else {
        let theUrl = "http://127.0.0.1:5000/plot?sql_id=" + sql_id + "&days_num=" + days
        let xmlHttp = new XMLHttpRequest();
        xmlHttp.onreadystatechange = function () {
            if (xmlHttp.readyState === 4) {
                if (xmlHttp.status === 200) {
                    document.getElementById("loader-graph").style.display = "none"
                    let graph = JSON.parse(xmlHttp.responseText);

                    Plotly.plot('chart', graph, {});
                } else if (xmlHttp.status === 400) {
                    showError(xmlHttp.responseText)
                } else {
                    showError("There is an internal server error in showing graph \n " + xmlHttp.responseText)
                }
            }
        };
        xmlHttp.open("GET", theUrl);
        xmlHttp.send();
    }
}


function showInfo(sql_id) {
    let theUrl = "http://127.0.0.1:5000/get_info?sql_id=" + sql_id
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState === 4) {
            document.getElementById("loader-graph").style.display = "none"
            if (xmlHttp.status === 200) {
                let info = JSON.parse(xmlHttp.responseText);

                creatTable(info)

            } else if (xmlHttp.status === 400) {
                showError(xmlHttp.responseText)
            } else {
                showError("There is an internal server error in getting information \n " + xmlHttp.responseText)
            }
        }
    };
    xmlHttp.open("GET", theUrl);
    xmlHttp.send();
    return false
}

function creatTable(info) {
    document.getElementById("div-table").style.display = "block"
    let tbody = document.getElementById("table-body")
    tbody.style.display = "none"
    let lastUpdate = info.last_date
    let ipAddresses = info.ip_address
    let numberOfRequests = info.number_of_requests

    //add last update time
    let lastUpdateP =  document.createElement("p")
    lastUpdateP.innerHTML = "Last request on this sql_id: " + lastUpdate
    lastUpdateP.id = "lastRequest"
    let graph = document.getElementById("graph")
    graph.insertBefore(lastUpdateP,graph.children[2])

    for (let date in numberOfRequests) {
        let tabButton = document.createElement("button")
        tabButton.innerHTML = date
        tabButton.className = "tablinks"
        tabButton.setAttribute('onclick', "openTable(event,'" + date + "')")
        let tabDiv = document.getElementById("tab")
        tabDiv.appendChild(tabButton)

        let numberOfRequests = document.createElement("p")

        let lengthRowSpan = ipAddresses[date].length
        let firstTr = true
        for (let ip in ipAddresses[date]) {
            let tr = document.createElement("tr")
            tr.className = "tabcontent " + date


            let tdIp = document.createElement("td")
            let tdNumber = document.createElement("td")
            tdIp.innerHTML = Object.keys(ipAddresses[date][ip])[0]
            tdNumber.innerHTML = (ipAddresses[date][ip][tdIp.innerHTML])
            tr.appendChild(tdIp)
            tr.appendChild(tdNumber)

            tbody.appendChild(tr)
        }

    }

}

function openTable(evt, cityName) {
    var i, tabcontent, tablinks;

    let tbody = document.getElementById("table-body")
    tbody.removeAttribute("style")
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    te = document.getElementsByClassName(cityName);
    for (i = 0; i < te.length; i++) {
        te[i].style.display = ""
    }
    evt.currentTarget.className += " active";
}

function showError(s) {
    document.getElementById("loader-graph").style.display = "none"
    let child = document.createElement("div");
    child.id = "error";
    child.innerHTML = "<p>" + s + "</p>"
    document.getElementById("graph").append(child)
}
