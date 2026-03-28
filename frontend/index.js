document.addEventListener("DOMContentLoaded", () => {
    const clientSelect = document.getElementById("client-select");
    const generateBtn = document.getElementById("generate-btn");
    const bqSummary = document.getElementById("bq-summary");
    const lossSummary = document.getElementById("loss-summary");
    const synthesisOutput = document.getElementById("synthesis-output");
    const synthesisBadge = document.getElementById("synthesis-badge");

    let currentClient = null;

    // Fetch clients on load
    fetch("/api/clients")
        .then(res => res.json())
        .then(clients => {
            clients.forEach(client => {
                const opt = document.createElement("option");
                opt.value = client.id;
                opt.textContent = client.name;
                clientSelect.appendChild(opt);
            });
        })
        .catch(err => console.error("Error fetching clients:", err));

    // Handle Client Selection
    clientSelect.addEventListener("change", (e) => {
        const clientId = e.target.value;
        if (!clientId) {
            resetUI();
            return;
        }

        generateBtn.disabled = false;
        
        // Fetch client details (BQ and Loss runs preview)
        fetch(`/api/clients/${clientId}`)
            .then(res => res.json())
            .then(data => {
                currentClient = data;
                renderPreviews(data);
            })
            .catch(err => console.error("Error fetching client details:", err));
    });

    // Handle Generate Summary
    generateBtn.addEventListener("click", () => {
        if (!clientSelect.value) return;

        setLoadingState(true);

        fetch("/api/generate-summary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ clientId: clientSelect.value })
        })
        .then(res => res.json())
        .then(data => {
            renderSynthesis(data.summary);
        })
        .catch(err => {
            console.error("Error generating summary:", err);
            renderSynthesis("Error generating summary. Please check logs.");
        })
        .finally(() => {
            setLoadingState(false);
        });
    });

    function resetUI() {
        generateBtn.disabled = true;
        bqSummary.innerHTML = `<div class="placeholder-text">Select a client to view BigQuery data.</div>`;
        lossSummary.innerHTML = `<div class="placeholder-text">Select a client to view loss run summaries.</div>`;
        synthesisOutput.innerHTML = `
            <div class="empty-state">
                <i data-lucide="sparkles" class="empty-icon pulse"></i>
                <h3>Ready for Synthesis</h3>
                <p>Click **Generate Risk Summary** to synthesize structured BQ data and unstructured Loss Runs using Gemini context windows.</p>
            </div>
        `;
        lucide.createIcons();
        synthesisBadge.textContent = "Awaiting data...";
        synthesisBadge.className = "badge badge-purple";
    }

    function renderPreviews(data) {
        // Render BQ Mock data
        bqSummary.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-label">Premium History (3Y)</span>
                    <span class="metric-value">$${data.bq_data.premium_3y.toLocaleString()}</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Loss Ratio (YTD)</span>
                    <span class="metric-value ${data.bq_data.loss_ratio > 0.70 ? 'danger-text' : 'success-text'}">${(data.bq_data.loss_ratio * 100).toFixed(1)}%</span>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Claims Frequency</span>
                    <span class="metric-value">${data.bq_data.claims_frequency} / year</span>
                </div>
            </div>
            <div class="data-block">
                <h4>Recent Large Claims</h4>
                <ul>
                    ${data.bq_data.large_claims.map(claim => `<li>${claim}</li>`).join('')}
                </ul>
            </div>
        `;

        // Render Loss Runs preview
        lossSummary.innerHTML = `
            <div class="narrative-container">
                <h4>Narrative Excerpts (Vertex Retreived Context)</h4>
                <p>${data.loss_runs.narrative}</p>
                <div class="bullet-list">
                    <h5>Key Incidents Identified:</h5>
                    <ul>
                        ${data.loss_runs.key_incidents.map(inc => `<li>${inc}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    function setLoadingState(isLoading) {
        if (isLoading) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = `<span class="spinner"></span> Synthesizing Knowledge...`;
            synthesisOutput.innerHTML = `
                <div class="loading-state">
                    <div class="ai-loader"></div>
                    <h3>Consulting Gemini 2.5 Flash</h3>
                    <p>Blending structured claims tables with unstructured loss run telemetry...</p>
                </div>
            `;
            synthesisBadge.textContent = "Generating...";
            synthesisBadge.className = "badge badge-purple pulse";
        } else {
            generateBtn.disabled = false;
            generateBtn.innerHTML = `<i data-lucide="sparkles"></i> Generate Risk Summary`;
            lucide.createIcons();
            synthesisBadge.className = "badge badge-green";
            synthesisBadge.textContent = "AI Synthsized";
        }
    }

    function renderSynthesis(markdownText) {
        // Since we don't have a full markdown renderer in client-side without libraries,
        // we'll do some basic replacement for bold/headers or just use innerHTML with backticks
        // if the model returns simple format. Or we can just use pre-wrap for now.
        
        const html = convertSimpleMarkdown(markdownText);
        
        synthesisOutput.innerHTML = `
            <div class="ai-response">
                ${html}
            </div>
        `;
    }

    function convertSimpleMarkdown(md) {
        if (!md) return "";
        let html = md;
        
        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
        
        // Lists
        html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
        html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
        
        // Wrap lists
        html = html.replace(/<li>(.*?)<\/li>/gim, '<ul><li>$1</li></ul>');
        html = html.replace(/<\/ul>\s*<ul>/gim, ''); // Merge consecutive lists

        // Line breaks
        html = html.replace(/\n$/gim, '<br>');
        html = html.replace(/\n/gim, '<br>');

        return html;
    }
});
