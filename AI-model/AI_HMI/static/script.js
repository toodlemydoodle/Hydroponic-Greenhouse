// Grab document elements for lettuce AI
const statusChip = document.getElementById("lettuce-status-chip");
const probEl = document.getElementById("lettuce-prob");
const lastCheckEl = document.getElementById("lettuce-last-check");
const checkBtn = document.getElementById("lettuce-check-btn");
const errorEl = document.getElementById("lettuce-error");
const lettuceImg = document.getElementById("lettuce-image");

// Checking lettuce NPK status from backend
async function checkLettuce() {
  if (!checkBtn || !statusChip || !probEl || !lastCheckEl || !errorEl) {
    console.warn("Some lettuce AI elements are missing from the DOM");
    return;
  }

  // Reset UI state
  errorEl.textContent = "";
  checkBtn.disabled = true;

  // Print loading status
  statusChip.textContent = "Checking...";
  statusChip.className = "status status-checking";
  probEl.textContent = "--";

  try {
    // Call the Windows backend, which proxies to the Pi's /check_lettuce
    const res = await fetch("/check_lettuce");
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || "HTTP " + res.status);
    }

    // Extract data from new NPK JSON
    const label = data.status || "Unknown";
    const isHealthy = !!data.is_healthy;
    const message = data.message || label || "No message";
    const probs = data.probs || {};
    const classFolder = data.class_folder;

    // Determine confidence of predicted class
    let confidence = null;
    if (classFolder && probs && Object.prototype.hasOwnProperty.call(probs, classFolder)) {
      confidence = Number(probs[classFolder]);
    }

    // Update probability display (top-class confidence)
    if (confidence !== null && !Number.isNaN(confidence)) {
      probEl.textContent = confidence.toFixed(2);
    } else {
      probEl.textContent = "--";
    }

    // Update status chip
    statusChip.textContent = message;
    if (isHealthy) {
      statusChip.className = "status status-ok";
    } else {
      statusChip.className = "status status-bad";
    }

    // Update last check time
    const now = new Date();
    lastCheckEl.textContent = "Last check: " + now.toLocaleTimeString();

    // Update snapshot image from base64
    if (lettuceImg && data.image_b64) {
      lettuceImg.src = "data:image/jpeg;base64," + data.image_b64;
    } else if (lettuceImg) {
      console.warn("No image_b64 field in response");
    }
  } catch (err) {
    console.error("Error in checkLettuce:", err);
    statusChip.textContent = "Error";
    statusChip.className = "status status-bad";
    probEl.textContent = "--";
    errorEl.textContent = "Failed to contact AI server: " + err.message;
  } finally {
    checkBtn.disabled = false;
  }
}

// Wire up button
if (checkBtn) {
  checkBtn.addEventListener("click", checkLettuce);
} else {
  console.warn("Check button not found in DOM");
}