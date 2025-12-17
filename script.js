let chartInstance = null;

function runSimulation() {

    const diskSize = diskSizeVal();
    const requests = requestArray();
    const head = headVal();
    const algorithm = document.getElementById("algorithm").value;

    fetch("http://127.0.0.1:5000/simulate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSize,
            requests: requests,
            head_position: head,
            algorithm: algorithm
        })
    })
    .then(res => res.json())
    .then(data => {
        updateMetrics(data);
        drawChart(data.seek_sequence);
    });
}

function compareAll() {

    fetch("http://127.0.0.1:5000/compare", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSizeVal(),
            requests: requestArray(),
            head_position: headVal()
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("bestAlgo").innerText = data.best_algorithm;
    });
}

/* ===== Helper Functions ===== */

function diskSizeVal() {
    return document.getElementById("diskSize").value;
}

function headVal() {
    return document.getElementById("headPosition").value;
}

function requestArray() {
    return document.getElementById("requestQueue")
        .value.split(",").map(n => parseInt(n.trim()));
}

function updateMetrics(data) {
    document.getElementById("totalSeekTime").innerText = data.total_seek_time;
    document.getElementById("averageSeekTime").innerText = data.average_seek_time;
    document.getElementById("throughput").innerText = data.throughput;
}

function drawChart(sequence) {

    const ctx = document.getElementById("movementChart");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: sequence.map((_, i) => i),
            datasets: [{
                label: "Head Position",
                data: sequence,
                tension: 0.3
            }]
        },
        options: {
            responsive: true
        }
    });
}
