const BACKEND_URL = "http://127.0.0.1:5000";
let moveChart, compareChart, lastSequence = [];

// ================= DARK MODE =================
function toggleDarkMode() {
    document.body.classList.toggle("dark");
}

// ================= VALIDATION =================
function validateInputs() {
    const d = parseInt(diskSize.value);
    const h = parseInt(headPosition.value);
    const r = requestQueue.value.split(",").map(x => parseInt(x.trim()));

    if (isNaN(d) || d <= 0) return alert("Invalid disk size"), false;
    if (isNaN(h) || h < 0 || h >= d) return alert("Invalid head position"), false;
    if (r.some(x => isNaN(x) || x < 0 || x >= d)) return alert("Invalid requests"), false;
    return true;
}

// ================= SIMULATE =================
function runSimulation() {
    if (!validateInputs()) return;

    fetch(`${BACKEND_URL}/simulate`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSize.value,
            requests: requestQueue.value.split(",").map(Number),
            head_position: headPosition.value,
            algorithm: algorithm.value,
            direction: scanDirection.value
        })
    })
    .then(r => r.json())
    .then(d => {
        totalSeekTime.innerText = d.total_seek_time;
        averageSeekTime.innerText = d.average_seek_time;
        throughput.innerText = d.throughput;
        animate(d.seek_sequence);
        fillTable(d.seek_sequence);
        lastSequence = d.seek_sequence;
    });
}

// ================= COMPARE =================
function compareAll() {
    if (!validateInputs()) return;

    fetch(`${BACKEND_URL}/compare`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSize.value,
            requests: requestQueue.value.split(",").map(Number),
            head_position: headPosition.value,
            direction: scanDirection.value
        })
    })
    .then(r => r.json())
    .then(d => {
        drawComparison(d.comparison);
        bestAlgo.innerText = d.best_algorithm;
    });
}

// ================= ANIMATION =================
function animate(seq) {
    let i = 0, labels = [], data = [];
    if (moveChart) moveChart.destroy();

    moveChart = new Chart(movementChart, {
        type: "line",
        data: { labels, datasets: [{ label: "Head Position", data }] },
        options: {
            scales: {
                x: { title: { display: true, text: "Step" }},
                y: { title: { display: true, text: "Disk Track" }}
            }
        }
    });

    const interval = setInterval(() => {
        if (i >= seq.length) return clearInterval(interval);
        labels.push(i);
        data.push(seq[i++]);
        moveChart.update();
    }, 400);
}

// ================= COMPARISON CHART =================
function drawComparison(cmp) {
    const labels = Object.keys(cmp);
    const values = labels.map(k => cmp[k].total_seek_time);

    if (compareChart) compareChart.destroy();

    compareChart = new Chart(comparisonChart, {
        type: "bar",
        data: { labels, datasets: [{ label: "Total Seek Time", data: values }] }
    });
}

// ================= TABLE =================
function fillTable(seq) {
    stepTable.innerHTML = "";
    seq.forEach((v, i) => {
        stepTable.innerHTML += `<tr><td>${i}</td><td>${v}</td></tr>`;
    });
}

// ================= CSV =================
function downloadReport() {
    let csv = "Step,Head\n";
    lastSequence.forEach((v, i) => csv += `${i},${v}\n`);
    const blob = new Blob([csv], {type:"text/csv"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "disk_scheduling_report.csv";
    a.click();
}
