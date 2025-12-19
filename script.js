let moveChart = null;
let compareChart = null;

/* ===== DARK MODE ===== */
function toggleDarkMode() {
    document.body.classList.toggle("dark");
}

/* ===== RUN SINGLE ALGORITHM ===== */
function runSimulation() {

    fetch("http://127.0.0.1:5000/simulate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSize(),
            requests: requests(),
            head_position: headPos(),
            algorithm: algo()
        })
    })
    .then(res => res.json())
    .then(data => {
        updateMetrics(data);
        animateHead(data.seek_sequence);
    });
}

/* ===== COMPARE ALL ===== */
function compareAll() {

    fetch("http://127.0.0.1:5000/compare", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            disk_size: diskSize(),
            requests: requests(),
            head_position: headPos()
        })
    })
    .then(res => res.json())
    .then(data => {
        drawComparisonChart(data.comparison);
        document.getElementById("bestAlgo").innerText = data.best_algorithm;
    });
}

/* ===== ANIMATION ===== */
function animateHead(sequence) {

    let i = 0;
    const labels = [];
    const dataPoints = [];

    if (moveChart) moveChart.destroy();

    moveChart = new Chart(document.getElementById("movementChart"), {
        type: "line",
        data: {
            labels,
            datasets: [{ label: "Head Movement", data: dataPoints }]
        }
    });

    const interval = setInterval(() => {
        if (i >= sequence.length) {
            clearInterval(interval);
            return;
        }
        labels.push(i);
        dataPoints.push(sequence[i]);
        moveChart.update();
        i++;
    }, 500); // animation speed
}

/* ===== BAR CHART ===== */
function drawComparisonChart(results) {

    const labels = [];
    const seekTimes = [];

    for (let algo in results) {
        labels.push(algo);
        seekTimes.push(results[algo].total_seek_time);
    }

    if (compareChart) compareChart.destroy();

    compareChart = new Chart(document.getElementById("comparisonChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Total Seek Time",
                data: seekTimes
            }]
        }
    });
}

/* ===== HELPERS ===== */
const diskSize = () => document.getElementById("diskSize").value;
const headPos = () => document.getElementById("headPosition").value;
const algo = () => document.getElementById("algorithm").value;
const requests = () =>
    document.getElementById("requestQueue").value.split(",").map(x => parseInt(x.trim()));

function updateMetrics(d) {
    totalSeekTime.innerText = d.total_seek_time;
    averageSeekTime.innerText = d.average_seek_time;
    throughput.innerText = d.throughput;
}
