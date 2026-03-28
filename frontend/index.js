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
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.error || data.detail) {
                    throw new Error(data.error || data.detail);
                }
                currentClient = data;
                renderPreviews(data);
            })
            .catch(err => {
                console.error("Error fetching client details:", err);
                resetUI();
                bqSummary.innerHTML = `<div class="placeholder-text" style="color:#ff6b6b">Error: Failed to load profile data.<br/>Please refresh the page.</div>`;
            });
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
        const bqEntries = Object.entries(data.bq_data);
        
        // Render BQ Mock data
        bqSummary.innerHTML = `
            <div class="metrics-grid">
                ${bqEntries.map(([key, value]) => `
                <div class="metric-card">
                    <span class="metric-label">${key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
                    <span class="metric-value">${typeof value === 'number' && key.includes('revenue') ? '$' + value.toLocaleString() : value}</span>
                </div>`).join('')}
            </div>
        `;

        // Render Loss Runs preview as PDF iframe with cache buster to force reload
        lossSummary.innerHTML = `
            <div class="pdf-container" style="height: 100%; min-height: 500px; width: 100%; border-radius: 8px; overflow: hidden;">
                <iframe src="/reports/${data.id}_loss_runs.pdf#view=FitH&t=${Date.now()}" width="100%" height="100%" style="border: none;"></iframe>
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
