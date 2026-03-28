document.addEventListener("DOMContentLoaded", () => {
  // 1. Grab the parameters passed from the main dashboard URL
  const params = new URLSearchParams(window.location.search);
  const studyUid = params.get("uid");
  const accessId =
    params.get("access_id") || sessionStorage.getItem("access_id");
  const patientId = params.get("pid");
  let urgency = params.get("urgency");
  const flags = params.get("flags") || "";
  const parsedFlags = flags
    .split(/[,|]/)
    .map((f) => f.trim().toUpperCase())
    .filter(Boolean);
  const flagSet = new Set(parsedFlags);

  const metaContainer = document.getElementById("study-meta");
  const imgElement = document.getElementById("active-image");
  const loading = document.getElementById("loading-overlay");

  if (!metaContainer) return console.error("study-meta element missing");
  if (!imgElement) return console.error("active-image element missing");

  if (window.location.protocol === "file:") {
    metaContainer.innerHTML = `<p class="dim" style="color:#f59e0b">Serve this file over HTTP (e.g. VSCode Live Server). file:// will block backend requests.</p>`;
  }

  if (studyUid && patientId) {
    fetch("http://localhost:8000/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        access_id: accessId,
        action: "VIEW_STUDY",
        details: `Study UID: ${studyUid}`,
      }),
    }).catch(console.error);

    metaContainer.innerHTML = `
            <div class="meta-item">
                <label>PATIENT ID:</label> 
                <span style="font-weight: bold; font-size: 1.2rem; color: #4ade80;">${patientId}</span>
            </div>
            <div class="meta-item">
                <label>AI PRIORITY:</label> 
                <!-- ADDED id="sidebar-urgency" to the span below -->
                <span id="sidebar-urgency" style="font-weight: bold; color: ${urgency === "CRITICAL" ? "#f87171" : "#4ade80"};">${urgency}</span>
            </div>
            <div class="meta-item">
                <label>STUDY UID:</label> 
                <small style="word-wrap: break-word; color: #666;">${studyUid}</small>
            </div>
        `;

    if (loading) loading.style.display = "block";
    imgElement.style.visibility = "hidden";
    imgElement.removeAttribute("src");

    imgElement.onload = () => {
      if (loading) loading.style.display = "none";
      imgElement.style.visibility = "visible";
    };

    imgElement.onerror = () => {
      if (loading) loading.style.display = "none";
      metaContainer.innerHTML += `<p style="color: #f87171; margin-top: 15px;">ERR: Failed to render image. Check backend /api/render/${studyUid} and CORS.</p>`;
    };

    const backendUrl = `http://localhost:8000/api/render/${encodeURIComponent(studyUid)}?access_id=${accessId}`;
    fetch(backendUrl, { method: "GET", mode: "cors" })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        const objectUrl = URL.createObjectURL(blob);
        imgElement.src = objectUrl;
        imgElement.addEventListener(
          "load",
          () => {
            URL.revokeObjectURL(objectUrl);
          },
          { once: true },
        );
      })
      .catch((err) => {
        if (loading) loading.style.display = "none";
        console.error("Image fetch error:", err);
        metaContainer.innerHTML += `<p style="color: #f87171; margin-top: 15px;">ERR: Cannot fetch image from backend (${err.message}). Ensure FastAPI is running on localhost:8000 and CORS is enabled.</p>`;
      });

    const downloadBtn = document.getElementById("download-btn");
    if (downloadBtn) {
      downloadBtn.addEventListener("click", () => {
        const btn = downloadBtn;

        btn.innerText = "COMPILING PDF...";
        btn.style.backgroundColor = "#f59e0b"; // Yellow
        btn.disabled = true;

        document.getElementById("pdf-pid").innerText = patientId;
        document.getElementById("pdf-uid").innerText = studyUid;
        document.getElementById("pdf-urgency").innerText = urgency;
        document.getElementById("pdf-date").innerText =
          new Date().toLocaleString();
        const pdfUrgencyEl = document.getElementById("pdf-urgency");
        if (pdfUrgencyEl)
          pdfUrgencyEl.style.color = urgency === "CRITICAL" ? "red" : "green";

        document.getElementById("pdf-flags").innerText =
          parsedFlags.join(", ") || "None";

        const summaryBox = document.getElementById("pdf-ai-summary");
        if (summaryBox) {
          if (window.currentAiSummary) {
            summaryBox.innerHTML = `<strong>AI ENGINE FINDINGS:</strong><br/><br/>${window.currentAiSummary}`;
            summaryBox.style.borderLeftColor = "#8b5cf6"; // Purple
            summaryBox.style.backgroundColor = "#faf5ff";
          } else {
            let aiSummaryText = "";
            if (
              urgency === "CRITICAL" &&
              flagSet.has("PIXEL_ANOMALY") &&
              flagSet.has("METADATA_STAT")
            ) {
              aiSummaryText =
                "<strong>CRITICAL ALERT:</strong> High-density pixel anomaly (>5%) plus STAT/trauma metadata. Immediate radiologist review required.";
              summaryBox.style.borderLeftColor = "#ef4444";
              summaryBox.style.backgroundColor = "#fef2f2";
            } else if (flagSet.has("PIXEL_ANOMALY")) {
              aiSummaryText =
                "<strong>URGENT ALERT:</strong> Pixel analysis shows hyperdense regions above baseline thresholds. Inspect for hemorrhage, contrast pooling, or artifacts.";
              summaryBox.style.borderLeftColor = "#f59e0b";
              summaryBox.style.backgroundColor = "#fffbeb";
            } else if (flagSet.has("METADATA_STAT")) {
              aiSummaryText =
                "<strong>PRIORITY ROUTING:</strong> Clinical metadata marked STAT/trauma. No major pixel variance detected, but expedited review is recommended.";
              summaryBox.style.borderLeftColor = "#f59e0b";
              summaryBox.style.backgroundColor = "#fffbeb";
            } else {
              aiSummaryText =
                "<strong>ROUTINE FINDINGS:</strong> No significant pixel anomalies or critical metadata detected. Proceed with standard diagnostic workflow.";
              summaryBox.style.borderLeftColor = "#16a34a";
              summaryBox.style.backgroundColor = "#f0fdf4";
            }
            summaryBox.innerHTML = aiSummaryText;
          }
        }

        const activeImg = document.getElementById("active-image");
        if (activeImg && activeImg.naturalWidth > 0) {
          const canvas = document.createElement("canvas");
          canvas.width = activeImg.naturalWidth;
          canvas.height = activeImg.naturalHeight;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(activeImg, 0, 0);
          document.getElementById("pdf-image").src =
            canvas.toDataURL("image/jpeg");
        } else {
          document.getElementById("pdf-image").src = "";
        }

        // Step C: Bypass the Popup Blocker
        const pdfWindow = window.open("", "_blank");
        if (!pdfWindow) {
          alert("Please allow pop-ups to view the AI Report.");
          btn.innerText = "GENERATE AI REPORT";
          btn.style.backgroundColor = "";
          btn.disabled = false;
          return;
        }
        pdfWindow.document.write(
          "<body style='background:#111;color:#4ade80;font-family:monospace;text-align:center;padding-top:100px;'><h2>COMPILING DIAGNOSTIC REPORT</h2></body>",
        );

        const reportElement = document.getElementById("report-template");
        if (reportElement) reportElement.style.display = "block";

        const opt = {
          margin: 0.5,
          filename: `Sentinel_Triage_${patientId}.pdf`,
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2 },
          jsPDF: { unit: "in", format: "letter", orientation: "portrait" },
        };

        html2pdf()
          .set(opt)
          .from(reportElement)
          .output("bloburl")
          .then((pdfUrl) => {
            pdfWindow.location.href = pdfUrl;
            if (reportElement) reportElement.style.display = "none";
            btn.innerText = "REPORT GENERATED";
            btn.style.backgroundColor = "#16a34a"; // Green
            btn.disabled = false;

            fetch("http://localhost:8000/api/audit", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                access_id: accessId,
                action: "DOWNLOAD_REPORT",
                details: `Generated AI PDF for study: ${studyUid} (${urgency})`,
              }),
            });

            setTimeout(() => {
              btn.innerText = "GENERATE AI REPORT";
              btn.style.backgroundColor = "";
            }, 3000);
          })
          .catch((err) => {
            console.error("PDF generation error:", err);
            alert("Failed to generate PDF.");
            if (reportElement) reportElement.style.display = "none";
            btn.innerText = "GENERATE AI REPORT";
            btn.style.backgroundColor = "";
            btn.disabled = false;
          });
      });
    }

    const runAiBtn = document.getElementById("run-ai-btn");
    const geminiResults = document.getElementById("gemini-results");

    if (runAiBtn && studyUid) {
      runAiBtn.addEventListener("click", () => {
        runAiBtn.innerText = "ANALYZING...";
        runAiBtn.disabled = true;
        geminiResults.style.display = "block";
        geminiResults.innerHTML =
          "<span style='color: #fbbf24;'>Sending scan to AI...</span>";

        const aiUrl = `http://localhost:8000/api/ai-analyze/${encodeURIComponent(studyUid)}?access_id=${encodeURIComponent(accessId)}`;

        fetch(aiUrl)
          .then(async (res) => {
            if (!res.ok) {
              const errText = await res.text();
              throw new Error(`HTTP ${res.status}: ${errText}`);
            }
            return res.json();
          })
          .then((data) => {
            if (data.status === "success" && data.analysis) {
              const formattedAnalysis = data.analysis.replace(/\n/g, "<br/>");

              window.currentAiSummary = formattedAnalysis;

              let oldUrgency = urgency;
              if (
                data.ai_priority === "CRITICAL" ||
                (data.ai_priority === "URGENT" && urgency === "ROUTINE")
              ) {
                urgency = data.ai_priority;

                const urgencySpan = document.getElementById("sidebar-urgency");
                if (urgencySpan) {
                  urgencySpan.innerText = urgency;
                  urgencySpan.style.color =
                    urgency === "CRITICAL" ? "#f87171" : "#f59e0b";
                }
              }

              geminiResults.innerHTML = `<strong>AI ANALYSIS (Priority: ${data.ai_priority}):</strong><br/>${formattedAnalysis}`;
            } else {
              geminiResults.innerHTML = `<span style="color: #ef4444;">Analysis failed.</span>`;
            }
          })
          .catch((err) => {
            console.error("Gemini Fetch Error:", err);
            geminiResults.innerHTML = `<span style="color: #ef4444;">Error: ${err.message}</span>`;
          })
          .finally(() => {
            runAiBtn.innerText = "REQUEST AI ANALYSIS";
            runAiBtn.disabled = false;
          });
      });
    }
  } else {
    metaContainer.innerHTML = `<p class="dim">No study selected. Open from the dashboard with ?uid=...&pid=...&urgency=...</p>`;
  }
});
