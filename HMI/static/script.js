console.log("script.js loaded");

const socket = io();

const ambEl = document.getElementById("ambient");
const uvEl = document.getElementById("uv");
const tempEl = document.getElementById("temp");
const flowEl = document.getElementById("flow");

const ambStatus = document.getElementById("ambient-status");
const tempStatus = document.getElementById("temp-status");
const flowStatus = document.getElementById("flow-status");
const lastUpdate = document.getElementById("last-update");

socket.on("connect", () => {
  console.log("Connected to Socket.IO");
});

socket.on("disconnect", () => {
  console.log("Disconnected from Socket.IO");
});

socket.on("sensor_data", (data) => {
  console.log("Sensor data:", data);

  if (ambEl) ambEl.textContent = data.ambient.toFixed(2) + " %";
  if (uvEl) uvEl.textContent = data.uv.toFixed(2) + " %";
  if (tempEl) tempEl.textContent = data.temp.toFixed(2) + " °C";
  if (flowEl) flowEl.textContent = data.flow.toFixed(2) + " L/min";

  // ambient status
  if (ambStatus) {
    if (data.ambient < 5) {
      ambStatus.textContent = "Low light";
      ambStatus.className = "status status-warn";
    } else {
      ambStatus.textContent = "OK";
      ambStatus.className = "status status-ok";
    }
  }

  // temp status
  if (tempStatus) {
    if (data.temp < 15 || data.temp > 30) {
      tempStatus.textContent = "High Temperature";
      tempStatus.className = "status status-bad";
    } else {
      tempStatus.textContent = "OK";
      tempStatus.className = "status status-ok";
    }
  }

  // flow status
  if (flowStatus) {
    if (data.flow <= 0.1) {
      flowStatus.textContent = "No flow";
      flowStatus.className = "status status-bad";
    } else {
      flowStatus.textContent = "Flowing";
      flowStatus.className = "status status-ok";
    }
  }

  if (lastUpdate) {
    const now = new Date();
    lastUpdate.textContent = "Last update: " + now.toLocaleTimeString();
  }
});

// feed button (same as before)
const feedBtn = document.getElementById("feed-btn");
const feedStatus = document.getElementById("feed-status");

if (feedBtn && feedStatus) {
  feedBtn.addEventListener("click", async () => {
    feedStatus.textContent = "Sending feed command...";
    try {
      const res = await fetch("/servo/feed", { method: "POST" });
      const data = await res.json();
      if (data.status === "ok") {
        feedStatus.textContent = "Feed command sent!";
      } else {
        feedStatus.textContent =
          "Error: " + (data.error || "Unknown error");
      }
    } catch (err) {
      console.error(err);
      feedStatus.textContent = "Network/server error.";
    }
  });
}
