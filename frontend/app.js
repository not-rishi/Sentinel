let userAccessId = sessionStorage.getItem("access_id");
let userName = sessionStorage.getItem("user_name");

// Protection Guard: If no session exists, send them to login immediately
if (!userAccessId) {
  window.location.href = "login.html";
  // Stop further execution of the script
  throw new Error("Unauthorized: Redirecting to login.");
}

// If session exists, set the UI
setWelcomeMessage(userName || userAccessId);

function setWelcomeMessage(name) {
  const welcomeEl = document.getElementById("welcome-message");
  if (welcomeEl) welcomeEl.innerText = `Welcome, ${name}`;
}

function handleLogout() {
  fetch("http://localhost:8000/api/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_id: userAccessId }),
  })
    .then(() => {
      sessionStorage.clear();
      // Redirect to login instead of reloading the current page
      window.location.href = "login.html";
    })
    .catch(() => {
      // Even if the server call fails, clear local session and kick to login
      sessionStorage.clear();
      window.location.href = "login.html";
    });
}

const ws = new WebSocket("ws://localhost:8000/ws/dashboard");
let studies = [];

const statusEl = document.getElementById("connection-status");

ws.onopen = () => {
  if (statusEl) {
    statusEl.innerHTML = "GATEWAY CONNECTED";
    statusEl.style.color = "var(--primary)";
    statusEl.style.borderColor = "var(--primary)";
  }
};

ws.onclose = () => {
  if (statusEl) {
    statusEl.innerText = "● DISCONNECTED";
    statusEl.style.color = "var(--danger)";
    statusEl.style.borderColor = "var(--danger)";
  }
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "METRICS") {
    updateMetrics(data);
    return;
  }

  studies = studies.filter((s) => s.study_uid !== data.study_uid);
  studies.push(data);

  const rank = { CRITICAL: 0, URGENT: 1, ROUTINE: 2 };
  studies.sort(
    (a, b) => (rank[a.urgency_level] ?? 9) - (rank[b.urgency_level] ?? 9),
  );

  updateUI();
};

// Add this helper function anywhere in app.js
function formatUptime(totalSeconds) {
  if (!totalSeconds || isNaN(totalSeconds)) return "00:00:00";

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);

  // Pads with leading zeros (e.g., 5 becomes "05")
  const h = hours.toString().padStart(2, "0");
  const m = minutes.toString().padStart(2, "0");
  const s = seconds.toString().padStart(2, "0");

  return `${h}:${m}:${s}`;
}

// Update your existing updateMetrics function
function updateMetrics(m) {
  const uptime = document.getElementById("stat-uptime");
  const uptimeTime = document.getElementById("stat-uptime-time"); // Grab the new element
  const delivery = document.getElementById("stat-delivery");
  const uptimeBar = document.getElementById("bar-uptime");
  const deliveryBar = document.getElementById("bar-delivery");

  let finalDeliveryPct = m.deliverability_pct;
  if (m.delivered > 0 && m.delivered >= m.attempts - m.failed) {
    finalDeliveryPct = 100.0;
  }

  if (uptime) uptime.innerText = `${Number(m.uptime_pct).toFixed(2)}%`;
  if (delivery) delivery.innerText = `${Number(finalDeliveryPct).toFixed(2)}%`;

  // NEW: Format and display the time if the backend sends it
  if (uptimeTime && m.uptime_seconds !== undefined) {
    uptimeTime.innerText = formatUptime(m.uptime_seconds);
  }

  if (uptimeBar) {
    uptimeBar.style.width = `${m.uptime_pct}%`;
    uptimeBar.className = `progress-fill ${m.uptime_pct < 98 ? "status-yellow" : "status-green"}`;
  }

  if (deliveryBar) {
    deliveryBar.style.width = `${finalDeliveryPct}%`;
    deliveryBar.className = `progress-fill ${finalDeliveryPct < 100 ? "status-yellow" : "status-green"}`;
  }
}

function updateUI() {
  const body = document.getElementById("queue-body");
  if (!body) return;
  body.innerHTML = "";

  let criticalCount = 0;

  studies.forEach((s) => {
    if (s.urgency_level === "CRITICAL") criticalCount++;

    const tr = document.createElement("tr");
    if (s.urgency_level === "CRITICAL") tr.className = "critical-row";

    // Generate a fallback time if the backend doesn't send one
    const timeReceived = s.time || new Date().toLocaleTimeString();

    // Fallback display if AI flags array is empty
    const flagsDisplay =
      s.flags && s.flags.length > 0 ? s.flags.join(" | ") : "NONE";

    // Now pushing all 6 required columns to match index.html
    tr.innerHTML = `
      <td>${timeReceived}</td>
      <td>${s.patient_id}</td>
      <td style="font-size: 0.8rem;">${s.study_uid}</td>
      <td class="status-${s.urgency_level.toLowerCase()}">${s.urgency_level}</td>
      <td>${flagsDisplay}</td>
      <td><button class="view-btn" onclick="openViewer('${s.study_uid}', '${s.patient_id}', '${s.urgency_level}', '${s.flags.join(",")}')">LAUNCH VIEWER</button></td>
    `;
    body.appendChild(tr);
  });

  const statTotal = document.getElementById("stat-total");
  const statCritical = document.getElementById("stat-critical");

  if (statTotal) statTotal.innerText = studies.length;
  if (statCritical) statCritical.innerText = criticalCount;
}

function openViewer(uid, pid, urgency, flags) {
  const url = `viewer.html?uid=${encodeURIComponent(uid)}&pid=${encodeURIComponent(pid)}&urgency=${encodeURIComponent(urgency)}&flags=${encodeURIComponent(flags)}&access_id=${encodeURIComponent(userAccessId)}`;
  window.open(url, "_blank", "width=1200,height=800");
}
