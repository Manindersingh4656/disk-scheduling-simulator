/*
This file handles:
1. Reading user input
2. Sending data to backend (Flask API)
3. Receiving results
4. Displaying results
5. Drawing charts
*/

let chartInstance = null;

/* Main function called when user clicks "Run Simulation" */
function runSimulation() {

    // Read values from input fields
    const diskSize = document.getElementById("diskSize").value;
    const requestQueue = document.getElementById("requestQueue").value;
    const headPosition = document.getElementById("headPosition").value;
    const algorithm = document.getElementById("algorithm").value;

    // Basic validation
    if (!diskSize || !requestQueue || !headPosition) {
        alert("Please fill all fields");
        return;
    }

    // Convert request queue string into array of numbers
    const requests = requestQueue
        .split(",")
        .map(num => parseInt(num.trim()));

    /*
    Send data to backend using fetch API
    Backend URL will be Flask server
    */
    fetch("http://127.0.0.1:5000/simulate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            disk_size: diskSize,
            requests: requests,
            head_position: headPosition,
            algorithm: algorithm
        })
    })
    .then(response => response.json())
    .then(data => {

        // Display numerical results
        document.getElementById("totalSeekTime").innerText =
            "Total Seek Time: " + data.total_seek_time;

        document.getElementById("averageSeekTime").innerText =
            "Average Seek Time: " + data.average_seek_time;

        document.getElementById("throughput").innerText =
            "Throughput: " + data.throughput;

        // Draw graph
        drawChart(data.seek_sequence);
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Backend not running!");
    });
}

/* Function to draw disk head movement chart */
function drawChart(sequence) {

    const ctx = document.getElementById("movementChart").getContext("2d");

    // Destroy previous chart to avoid overlap
    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: sequence.map((_, index) => index),
            datasets: [{
                label: "Disk Head Position",
                data: sequence,
                fill: false,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Step"
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "Disk Track Number"
                    }
                }
            }
        }
    });
}
