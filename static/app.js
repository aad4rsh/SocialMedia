/* ═══════════════════════════════════════════════
   PolitiScope — App Controller
   ═══════════════════════════════════════════════ */

(() => {
    'use strict';

    // ─── State ───
    let selectedFile = null;
    let analysisData = null;
    let currentSection = 'sectionUpload';

    // ─── DOM References ───
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const dropZone = $('#dropZone');
    const fileInput = $('#fileInput');
    const fileInfo = $('#fileInfo');
    const fileName = $('#fileName');
    const fileSize = $('#fileSize');
    const removeFileBtn = $('#removeFile');
    const analyzeBtn = $('#analyzeBtn');
    const loadingOverlay = $('#loadingOverlay');
    const newAnalysisBtn = $('#newAnalysisBtn');
    const printReportBtn = $('#printReportBtn');

    const navLinks = {
        upload: $('#navUpload'),
        overview: $('#navOverview'),
        insights: $('#navInsights'),
        charts: $('#navCharts'),
        report: $('#navReport'),
    };

    const sections = {
        upload: $('#sectionUpload'),
        overview: $('#sectionOverview'),
        insights: $('#sectionInsights'),
        charts: $('#sectionCharts'),
        report: $('#sectionReport'),
    };

    // ─── Navigation ───
    function showSection(name) {
        Object.values(sections).forEach(s => s.classList.remove('active'));
        Object.values(navLinks).forEach(n => n.classList.remove('active'));

        sections[name].classList.add('active');
        navLinks[name].classList.add('active');
        currentSection = name;

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function enableNav() {
        Object.values(navLinks).forEach(n => n.classList.remove('disabled'));
        newAnalysisBtn.classList.remove('hidden');
    }

    // Nav click handlers
    Object.entries(navLinks).forEach(([name, el]) => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            if (el.classList.contains('disabled')) return;
            showSection(name);
        });
    });

    newAnalysisBtn.addEventListener('click', () => {
        location.reload();
    });

    printReportBtn.addEventListener('click', () => {
        window.print();
    });

    // ─── File Upload ───
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        dropZone.classList.remove('hidden');
        analyzeBtn.classList.add('hidden');
    });

    function handleFile(file) {
        if (!file.name.endsWith('.csv')) {
            showToast('Please upload a .csv file', 'error');
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        dropZone.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        analyzeBtn.classList.remove('hidden');
    }

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        await analyzeFile();
    });

    // ─── API Call ───
    async function analyzeFile() {
        loadingOverlay.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const resp = await fetch('/api/analyze', {
                method: 'POST',
                body: formData,
            });

            const data = await resp.json();
            if (!resp.ok || data.error) {
                throw new Error(data.error || 'Analysis failed');
            }

            analysisData = data;
            renderAll(data);
            enableNav();
            showSection('overview');
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }

    // ─── Render All ───
    function renderAll(data) {
        renderOverview(data);
        renderInsights(data);
        renderCharts(data);
        renderReport(data);
    }

    // ═══════════════════════════════════════════════
    //  OVERVIEW
    // ═══════════════════════════════════════════════

    function renderOverview(data) {
        const { overview, summary } = data;

        // Subtitle
        $('#overviewSubtitle').textContent =
            `${summary.filename} — ${summary.total_posts.toLocaleString()} posts from ${summary.unique_channels} channels`;

        // Stat cards
        const eng = overview.engagement;
        const statCards = [
            {
                label: 'Total Posts',
                value: overview.total_posts.toLocaleString(),
                detail: `Across ${Object.keys(overview.platform_distribution).length} platforms`,
                accent: '#6366f1'
            },
            {
                label: 'Total Likes',
                value: eng.LikesCount ? eng.LikesCount.total.toLocaleString() : '0',
                detail: eng.LikesCount ? `Avg: ${eng.LikesCount.mean.toLocaleString()}` : '',
                accent: '#f472b6'
            },
            {
                label: 'Total Shares',
                value: eng.SharesCount ? eng.SharesCount.total.toLocaleString() : '0',
                detail: eng.SharesCount ? `Avg: ${eng.SharesCount.mean.toLocaleString()}` : '',
                accent: '#22d3ee'
            },
            {
                label: 'Total Comments',
                value: eng.CommentsCount ? eng.CommentsCount.total.toLocaleString() : '0',
                detail: eng.CommentsCount ? `Avg: ${eng.CommentsCount.mean.toLocaleString()}` : '',
                accent: '#fbbf24'
            },
            {
                label: 'Total Views',
                value: eng.ViewsCount ? eng.ViewsCount.total.toLocaleString() : '0',
                detail: eng.ViewsCount ? `Avg: ${eng.ViewsCount.mean.toLocaleString()}` : '',
                accent: '#34d399'
            },
            {
                label: 'Date Span',
                value: overview.date_range.span_days ? `${overview.date_range.span_days} days` : 'N/A',
                detail: overview.date_range.earliest ? `${formatDate(overview.date_range.earliest)} → ${formatDate(overview.date_range.latest)}` : '',
                accent: '#a78bfa'
            }
        ];

        $('#overviewCards').innerHTML = statCards.map(c => `
            <div class="stat-card" style="--card-accent: ${c.accent}">
                <div class="stat-label">${c.label}</div>
                <div class="stat-value">${c.value}</div>
                <div class="stat-detail">${c.detail}</div>
            </div>
        `).join('');

        // Platform mini-chart
        if (Object.keys(overview.platform_distribution).length > 0) {
            const pLabels = Object.keys(overview.platform_distribution);
            const pValues = Object.values(overview.platform_distribution);
            Plotly.newPlot('overviewPlatformChart', [{
                labels: pLabels,
                values: pValues,
                type: 'pie',
                hole: 0.5,
                marker: { colors: ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#818cf8'] },
                textinfo: 'label+percent',
                textfont: { size: 12 },
            }], {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                margin: { t: 10, b: 10, l: 10, r: 10 },
                showlegend: false,
            }, { responsive: true, displayModeBar: false });
        }

        // Post type mini-chart
        if (Object.keys(overview.post_type_distribution).length > 0) {
            const ptLabels = Object.keys(overview.post_type_distribution);
            const ptValues = Object.values(overview.post_type_distribution);
            Plotly.newPlot('overviewPostTypeChart', [{
                x: ptValues,
                y: ptLabels,
                type: 'bar',
                orientation: 'h',
                marker: { color: '#6366f1', opacity: 0.8 },
                text: ptValues,
                textposition: 'outside',
                textfont: { size: 11, color: '#cbd5e1' },
            }], {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#cbd5e1' },
                xaxis: { color: '#94a3b8', gridcolor: 'rgba(148,163,184,0.1)' },
                yaxis: { color: '#94a3b8', autorange: 'reversed' },
                margin: { t: 10, b: 30, l: 100, r: 50 },
            }, { responsive: true, displayModeBar: false });
        }

        // Channels table
        const channels = overview.channel_distribution;
        if (Object.keys(channels).length > 0) {
            const maxVal = Math.max(...Object.values(channels));
            let tableHTML = `
                <table class="data-table">
                    <thead>
                        <tr><th>#</th><th>Channel</th><th>Posts</th><th>Volume</th></tr>
                    </thead>
                    <tbody>
            `;
            Object.entries(channels).forEach(([name, count], i) => {
                const pct = (count / maxVal * 100).toFixed(0);
                tableHTML += `
                    <tr>
                        <td class="channel-rank">${i + 1}</td>
                        <td>${name}</td>
                        <td>${count.toLocaleString()}</td>
                        <td>
                            <div class="engagement-bar-container">
                                <div class="engagement-bar">
                                    <div class="engagement-bar-fill" style="width: ${pct}%"></div>
                                </div>
                                <span style="font-size:0.78rem; color: var(--text-muted)">${pct}%</span>
                            </div>
                        </td>
                    </tr>
                `;
            });
            tableHTML += '</tbody></table>';
            $('#overviewChannelsTable').innerHTML = tableHTML;
        }
    }

    // ═══════════════════════════════════════════════
    //  INSIGHTS
    // ═══════════════════════════════════════════════

    function renderInsights(data) {
        const { insights, tag_analysis } = data;

        // Insight cards
        $('#insightsGrid').innerHTML = insights.map(ins => `
            <div class="insight-card severity-${ins.severity}">
                <div class="insight-header">
                    <div class="insight-icon">${ins.icon}</div>
                    <div class="insight-meta">
                        <div class="insight-category">${ins.category}</div>
                        <div class="insight-title">${ins.title}</div>
                    </div>
                </div>
                <div class="insight-detail">${ins.detail}</div>
            </div>
        `).join('');

        // Tag breakdown
        let tagHTML = '';
        Object.entries(tag_analysis).forEach(([catName, labels]) => {
            const total = Object.values(labels).reduce((a, b) => a + b, 0);
            if (total === 0) return;

            tagHTML += `
                <div class="tag-category">
                    <div class="tag-category-title">${catName} <span style="color:var(--text-muted);font-weight:400;font-size:0.78rem">(${total} total)</span></div>
            `;
            Object.entries(labels)
                .sort((a, b) => b[1] - a[1])
                .forEach(([label, count]) => {
                    tagHTML += `
                        <div class="tag-item">
                            <span class="tag-name">${label}</span>
                            <span class="tag-count">${count}</span>
                        </div>
                    `;
                });
            tagHTML += '</div>';
        });
        $('#tagBreakdownContainer').innerHTML = tagHTML;
    }

    // ═══════════════════════════════════════════════
    //  CHARTS
    // ═══════════════════════════════════════════════

    function renderCharts(data) {
        const { charts } = data;
        const container = $('#chartsContainer');
        container.innerHTML = '';

        charts.forEach((chart, idx) => {
            const card = document.createElement('div');
            card.className = 'chart-card';
            card.innerHTML = `
                <div class="chart-title">${chart.title}</div>
                <div class="chart-plot" id="chartPlot_${idx}"></div>
            `;
            container.appendChild(card);

            // Render plotly chart
            setTimeout(() => {
                const plotDiv = document.getElementById(`chartPlot_${idx}`);
                if (plotDiv && chart.data) {
                    Plotly.newPlot(plotDiv, chart.data.data, chart.data.layout, {
                        responsive: true,
                        displayModeBar: true,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                        displaylogo: false,
                    });
                }
            }, 100 * idx);
        });
    }

    // ═══════════════════════════════════════════════
    //  REPORT
    // ═══════════════════════════════════════════════

    function renderReport(data) {
        const { overview, insights, tag_analysis, summary, charts } = data;
        const eng = overview.engagement;

        let html = `
            <div class="report-title-block">
                <h1>📊 Social Media Analysis Report</h1>
                <div class="report-meta">
                    File: ${summary.filename} &middot; 
                    Generated: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} &middot;
                    ${summary.total_posts.toLocaleString()} posts analyzed
                </div>
            </div>

            <div class="report-section">
                <h3>1. Dataset Summary</h3>
                <div class="report-stat-grid">
                    <div class="report-stat">
                        <div class="label">Total Posts</div>
                        <div class="value">${summary.total_posts.toLocaleString()}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Channels</div>
                        <div class="value">${summary.unique_channels}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Platforms</div>
                        <div class="value">${summary.platforms.length}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Date Span</div>
                        <div class="value">${overview.date_range.span_days || 'N/A'}d</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Total Likes</div>
                        <div class="value">${eng.LikesCount ? eng.LikesCount.total.toLocaleString() : '0'}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Total Shares</div>
                        <div class="value">${eng.SharesCount ? eng.SharesCount.total.toLocaleString() : '0'}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Total Comments</div>
                        <div class="value">${eng.CommentsCount ? eng.CommentsCount.total.toLocaleString() : '0'}</div>
                    </div>
                    <div class="report-stat">
                        <div class="label">Total Views</div>
                        <div class="value">${eng.ViewsCount ? eng.ViewsCount.total.toLocaleString() : '0'}</div>
                    </div>
                </div>
            </div>

            <div class="report-section">
                <h3>2. Key Findings</h3>
                <ul class="report-insight-list">
        `;

        insights.forEach(ins => {
            html += `
                <li class="report-insight-item">
                    <span class="icon">${ins.icon}</span>
                    <div class="content">
                        <strong>${ins.title}</strong>
                        <p>${ins.detail}</p>
                    </div>
                </li>
            `;
        });

        html += `
                </ul>
            </div>

            <div class="report-section">
                <h3>3. Tag Distribution Summary</h3>
        `;

        Object.entries(tag_analysis).forEach(([catName, labels]) => {
            const total = Object.values(labels).reduce((a, b) => a + b, 0);
            if (total === 0) return;

            const sorted = Object.entries(labels).sort((a, b) => b[1] - a[1]);
            const top3 = sorted.slice(0, 3).map(([l, c]) => `${l} (${c})`).join(', ');

            html += `
                <div style="margin-bottom:1rem; padding:1rem; background:var(--bg-secondary); border-radius:var(--radius-sm); border:1px solid var(--border)">
                    <strong style="color:var(--accent-primary)">${catName}</strong>
                    <span style="color:var(--text-muted);font-size:0.85rem"> — ${total} total tags</span>
                    <p style="color:var(--text-secondary);font-size:0.88rem;margin-top:0.4rem">Top: ${top3}</p>
                </div>
            `;
        });

        html += `
            </div>

            <div class="report-section">
                <h3>4. Visualizations</h3>
                <p style="color:var(--text-secondary);margin-bottom:1rem">Charts are rendered in the Charts tab. Use the Print button to capture them in the report.</p>
        `;

        // Add chart placeholders with IDs for rendering
        charts.forEach((chart, idx) => {
            html += `
                <div class="report-chart-placeholder">
                    <div style="font-weight:600;margin-bottom:0.75rem;color:var(--accent-primary)">${chart.title}</div>
                    <div id="reportChart_${idx}" style="width:100%;min-height:300px"></div>
                </div>
            `;
        });

        html += '</div>';

        // Recommendations section
        html += `
            <div class="report-section">
                <h3>5. Recommendations</h3>
                <ul class="report-insight-list">
        `;

        // Generate recommendations based on insights
        const recommendations = generateRecommendations(insights, tag_analysis, overview);
        recommendations.forEach(rec => {
            html += `
                <li class="report-insight-item">
                    <span class="icon">${rec.icon}</span>
                    <div class="content">
                        <strong>${rec.title}</strong>
                        <p>${rec.detail}</p>
                    </div>
                </li>
            `;
        });

        html += '</ul></div>';

        $('#reportContent').innerHTML = html;

        // Render charts in report
        charts.forEach((chart, idx) => {
            setTimeout(() => {
                const plotDiv = document.getElementById(`reportChart_${idx}`);
                if (plotDiv && chart.data) {
                    Plotly.newPlot(plotDiv, chart.data.data, {
                        ...chart.data.layout,
                        height: 350,
                    }, {
                        responsive: true,
                        displayModeBar: false,
                    });
                }
            }, 200 + 100 * idx);
        });
    }

    function generateRecommendations(insights, tagAnalysis, overview) {
        const recs = [];

        const misinfo = tagAnalysis['Misinformation & Disinformation'] || {};
        const misinfoTotal = Object.values(misinfo).reduce((a, b) => a + b, 0);
        if (misinfoTotal > 0) {
            recs.push({
                icon: '🛡️',
                title: 'Implement Misinformation Counter-measures',
                detail: `${misinfoTotal} posts flagged for misinformation. Consider deploying fact-checking response teams and partnering with media literacy organizations.`
            });
        }

        const hate = tagAnalysis['Hate Speech & Polarization'] || {};
        const hateTotal = Object.values(hate).reduce((a, b) => a + b, 0);
        if (hateTotal > 0) {
            recs.push({
                icon: '⚖️',
                title: 'Address Hate Speech Patterns',
                detail: `${hateTotal} posts contain hate speech or polarization. Recommend monitoring targeted groups and engaging civil society stakeholders.`
            });
        }

        const toneData = tagAnalysis['Tone'] || {};
        const negCount = (toneData['Negative'] || 0) + (toneData['Aggressive'] || 0) + (toneData['Fear-based'] || 0);
        const totalTone = Object.values(toneData).reduce((a, b) => a + b, 0);
        if (totalTone > 0 && negCount / totalTone > 0.3) {
            recs.push({
                icon: '🤝',
                title: 'Promote Constructive Discourse',
                detail: `${(negCount/totalTone*100).toFixed(0)}% of the discourse is negative, aggressive or fear-based. Public awareness campaigns on constructive dialogue are recommended.`
            });
        }

        const electoralData = tagAnalysis['Electoral Integrity'] || {};
        if (Object.values(electoralData).reduce((a, b) => a + b, 0) > 0) {
            recs.push({
                icon: '🗳️',
                title: 'Safeguard Electoral Process',
                detail: 'Posts challenging electoral integrity detected. Recommend strengthening election commission communications and transparency measures.'
            });
        }

        recs.push({
            icon: '📱',
            title: 'Platform-Specific Monitoring',
            detail: `Focus monitoring efforts across ${Object.keys(overview.platform_distribution).join(', ')} platforms with tailored detection strategies for each.`
        });

        recs.push({
            icon: '📊',
            title: 'Longitudinal Analysis',
            detail: 'Conduct ongoing analysis to track trends over time and detect emerging narratives before they gain traction.'
        });

        return recs;
    }

    // ─── Toast notification ───
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; bottom: 24px; right: 24px; z-index: 10000;
            padding: 14px 24px; border-radius: 12px;
            background: ${type === 'error' ? '#7f1d1d' : '#1e3a5f'};
            border: 1px solid ${type === 'error' ? '#991b1b' : '#2563eb'};
            color: white; font-size: 0.9rem; font-family: 'Inter', sans-serif;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            animation: fadeSlideIn 0.3s ease;
            max-width: 400px;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    // ─── Helpers ───
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatDate(dateStr) {
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        } catch {
            return dateStr;
        }
    }

})();
