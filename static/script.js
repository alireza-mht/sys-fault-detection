
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

        //remove previous table
        if (document.getElementById("table-body") != null)
            document.getElementById("table-body").remove()
        let tableBody = document.createElement("tbody")
        tableBody.id= "table-body"
        let table = document.getElementById("table")
        table.appendChild(tableBody)



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
        let lastUpdate = info.last_date
        let ipAddresses = info.ip_address
        let numberOfRequests = info.number_of_requests


        for (let date in numberOfRequests) {
            let tbody = document.getElementById("table-body")
            let lengthRowSpan = ipAddresses[date].length
            let firstTr = true
            for (let ip in ipAddresses[date]) {
                let tr = document.createElement("tr")

                if (firstTr === true) {
                    let tdDate = document.createElement("td")
                    let tdReqNumber = document.createElement("td")
                    tdDate.rowSpan = lengthRowSpan
                    tdReqNumber.rowSpan = lengthRowSpan
                    tdDate.innerHTML = date
                    tdReqNumber.innerHTML = numberOfRequests[date]
                    tr.appendChild(tdDate)
                    tr.appendChild(tdReqNumber)
                    firstTr = false
                }

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

    function showError(s) {
        document.getElementById("loader-graph").style.display = "none"
        let child = document.createElement("div");
        child.id = "error";
        child.innerHTML = "<p>" + s + "</p>"
        document.getElementById("graph").append(child)
    }
