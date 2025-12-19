const BACKEND_URL = "http://127.0.0.1:5000";

let moveChart = null;
let compareChart = null;
let lastSequence = [];



const algorithmInfo = {
    "FCFS": "First Come First Serve schedules disk requests in the order they arrive. It is simple but can result in long seek times.",
    "SSTF": "Shortest Seek Time First selects the request closest to the current head position, minimizing average seek time.",
    "SCAN": "SCAN moves the disk head in one direction servicing requests, then reverses direction like an elevator.",
    "CSCAN": "C-SCAN services requests in one direction only and jumps back to the beginning, providing uniform wait time."
};

function updateAlgorithmDescription() {
    const algo = document.getElementById("algorithm").value;
    document.getElementById("algoDescription").innerText = algorithmInfo[algo];
}

updateAlgorithmDescription();



function validateInputs() {
    const diskSize = parseInt(document.getElementById("diskSize").value);
    const head = parseInt(document.getElementById("headPosition").value);
    const requests = document.getElementById("requestQueue")
        .value.split(",").map(r => parseInt(r.trim()));

    if (isNaN(diskSize) || diskSize <= 0) {
        alert("Invalid disk size");
        return false;
    }

    if (isNaN(head) || head < 0 || head >= diskSize) {
        alert("Invalid head position");
        return false;
    }

    if (requests.some(r => isNaN(r) || r < 0 || r >= diskSize)) {
        alert("Invalid request values");
        return false;
    }

    return true;
}



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
    .then(res => res.json())
    .then(data => {
        totalSeekTime.innerText = data.total_seek_time;
        averageSeekTime.innerText = data.average_seek_time;
        throughput.innerText = data.throughput;

        animateHead(data.seek_sequence);
        fillStepTable(data.seek_sequence);

        lastSequence = data.seek_sequence;
    });
}



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
    .then(res => res.json())
    .then(data => {
        drawComparisonChart(data.comparison);
        bestAlgo.innerText = data.best_algorithm;
    });
}



function animateHead(sequence) {
    let i = 0;
    const labels = [];
    const values = [];

    if (moveChart) moveChart.destroy();

    moveChart = new Chart(document.getElementById("movementChart"), {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Disk Head Position",
                data: values
            }]
        },
        options: {
            scales: {
                x: { title: { display: true, text: "Step" }},
                y: { title: { display: true, text: "Disk Track" }}
            }
        }
    });

    const interval = setInterval(() => {
        if (i >= sequence.length) {
            clearInterval(interval);
            return;
        }
        labels.push(i);
        values.push(sequence[i]);
        moveChart.update();
        i++;
    }, 400);
}



function drawComparisonChart(results) {
    const labels = Object.keys(results);
    const values = labels.map(k => results[k].total_seek_time);

    if (compareChart) compareChart.destroy();

    compareChart = new Chart(document.getElementById("comparisonChart"), {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Total Seek Time",
                data: values
            }]
        }
    });
}



function fillStepTable(sequence) {
    const table = document.getElementById("stepTable");
    table.innerHTML = "";

    sequence.forEach((pos, i) => {
        table.innerHTML += `<tr><td>${i}</td><td>${pos}</td></tr>`;
    });
}



function downloadReport() {
    let csv = "Step,Head Position\n";
    lastSequence.forEach((v, i) => csv += `${i},${v}\n`);

    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "disk_scheduling_report.csv";
    link.click();
}



function exportToPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.setFontSize(16);
    doc.text("Advanced Disk Scheduling Simulator Report", 10, 15);

    doc.setFontSize(12);
    doc.text(`Algorithm: ${algorithm.value}`, 10, 30);
    doc.text(`Total Seek Time: ${totalSeekTime.innerText}`, 10, 40);
    doc.text(`Average Seek Time: ${averageSeekTime.innerText}`, 10, 50);
    doc.text(`Throughput: ${throughput.innerText}`, 10, 60);

    doc.text("Disk Head Movement:", 10, 75);

    let y = 85;
    lastSequence.forEach((pos, i) => {
        doc.text(`Step ${i}: ${pos}`, 10, y);
        y += 7;
        if (y > 280) {
            doc.addPage();
            y = 20;
        }
    });

    doc.save("disk_scheduling_report.pdf");
}
