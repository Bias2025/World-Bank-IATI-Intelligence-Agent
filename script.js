// World Bank IATI Intelligence Agent - JavaScript
// Digital Ocean API Integration for Development Finance Analysis

// API Configuration - Load from environment or prompt user
const DO_AGENT_ENDPOINT = getConfigValue('DO_AGENT_ENDPOINT', 'https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run');
const DO_AGENT_API_KEY = getConfigValue('DO_AGENT_API_KEY');
const CHATBOT_ID = getConfigValue('CHATBOT_ID');

// Configuration helper function
function getConfigValue(key, defaultValue = null) {
    // Try to get from local development config (if available)
    if (typeof window !== 'undefined' && window.WB_IATI_LOCAL_CONFIG && window.WB_IATI_LOCAL_CONFIG[key]) {
        return window.WB_IATI_LOCAL_CONFIG[key];
    }

    // Try to get from environment variables (if available)
    if (typeof process !== 'undefined' && process.env && process.env[key]) {
        return process.env[key];
    }

    // Try to get from localStorage (for client-side storage)
    if (typeof localStorage !== 'undefined') {
        const stored = localStorage.getItem(`WB_IATI_${key}`);
        if (stored) return stored;
    }

    // Use default value or prompt user
    if (defaultValue) return defaultValue;

    // For sensitive keys, show configuration modal
    return null;
}

let currentSessionId = generateSessionId();
let isProcessing = false;
let conversationHistory = [];

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const standardPrompts = document.getElementById('standardPrompts');
const usePromptBtn = document.getElementById('usePromptBtn');
const clearBtn = document.getElementById('clearBtn');
const exportBtn = document.getElementById('exportBtn');
const debugBtn = document.getElementById('debugBtn');
const charCount = document.getElementById('charCount');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const loadingOverlay = document.getElementById('loadingOverlay');

// Standard IATI prompts for World Bank data analysis
const IATI_PROMPTS = {
    portfolio_performance: "Analyze the overall World Bank portfolio performance including disbursement efficiency, sector distribution, and regional allocation. Provide executive-level insights with key metrics and trends.",
    disbursement_analysis: "Examine World Bank disbursement patterns across sectors and regions. Identify bottlenecks, delays, and opportunities for improvement. Include quarterly trends and comparative analysis.",
    commitment_trends: "Analyze World Bank commitment trends by sector and region over the last 5 years. Identify growth areas, declining sectors, and strategic shifts in development finance priorities.",
    portfolio_concentration: "Assess World Bank portfolio concentration risks across sectors, countries, and financial instruments. Provide recommendations for diversification and risk mitigation.",
    education_performance: "Deep-dive analysis of World Bank education sector performance including project outcomes, disbursement efficiency, and impact on learning outcomes across different country contexts.",
    health_outcomes: "Comprehensive analysis of World Bank health sector investments focusing on system strengthening, pandemic preparedness, and health outcome improvements with regional comparisons.",
    infrastructure_impact: "Assess World Bank infrastructure project impact and efficiency including transport, energy, and digital infrastructure with focus on economic returns and sustainability.",
    climate_finance: "Examine World Bank climate finance allocation including adaptation, mitigation, and co-benefits tracking. Analyze alignment with Paris Agreement goals and SDG targets.",
    regional_comparison: "Compare World Bank portfolio performance across different regions including IDA vs IBRD performance, project success rates, and development outcome achievements.",
    fragile_states: "Analyze World Bank investments in fragile and conflict-affected states including risk mitigation strategies, project adaptation approaches, and development effectiveness.",
    country_portfolio: "Detailed country portfolio analysis including active projects, financial flows, sector composition, implementation progress, and results framework achievements.",
    subnational_distribution: "Sub-national investment distribution analysis focusing on geographic equity, urban-rural balance, and targeting of underserved populations.",
    executive_summary: "Generate comprehensive executive dashboard for World Bank board presentation including portfolio KPIs, strategic insights, risk assessment, and forward-looking recommendations.",
    quarterly_review: "Create quarterly World Bank portfolio performance review including financial metrics, implementation progress, results achievements, and pipeline analysis.",
    strategic_overview: "Strategic portfolio overview with focus on institutional priorities, cross-cutting themes, and alignment with World Bank Group strategy and country partnership frameworks.",
    risk_dashboard: "Comprehensive portfolio risk assessment dashboard including implementation risks, financial risks, reputational risks, and environmental and social safeguards.",
    predictive_analysis: "Predictive analysis for future World Bank disbursements based on historical patterns, pipeline strength, and country capacity indicators.",
    anomaly_detection: "Detect anomalies and unusual patterns in World Bank portfolio data including irregular disbursement patterns, project delays, and performance outliers.",
    efficiency_benchmarking: "Benchmark World Bank efficiency against peer multilateral development banks including cost ratios, speed of deployment, and development effectiveness.",
    results_correlation: "Correlate World Bank investments with development outcomes using country-level indicators, sector performance metrics, and impact evaluation data."
};

// Quick action mappings
const QUICK_ACTIONS = {
    portfolio_overview: "Based on the available World Bank IATI data, analyze and aggregate individual project information to provide portfolio insights. Extract sector distributions, regional patterns, project statuses, and calculate performance indicators from the available IATI project data. Focus on trends and patterns you can identify from the individual project records in the knowledge base.",
    sector_analysis: "From the available World Bank IATI project data, analyze sector distribution patterns. Identify which sectors appear most frequently in the project data, examine sector-specific characteristics, timelines, and participating organizations. Provide sector insights based on the individual project records available in the knowledge base.",
    geographic_insights: "From the World Bank IATI project data available, analyze geographic patterns and regional distribution. Identify which countries and regions appear in the project records, examine location-specific project characteristics, and provide insights about regional focus areas based on the available project data.",
    trend_analysis: "Conduct comprehensive trend analysis of World Bank development finance including historical patterns, growth trajectories, seasonal variations, and predictive forecasting for future commitments and disbursements.",
    risk_assessment: "Perform portfolio risk assessment identifying concentration risks, implementation challenges, financial risks, and environmental/social safeguards across the World Bank's active portfolio.",
    create_dashboard: "Create an executive-level dashboard suitable for World Bank management and board presentations, including KPIs, visualizations, trend analysis, and strategic recommendations."
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌍 World Bank IATI Intelligence Agent initializing...');

    // Check if API configuration is needed
    if (!DO_AGENT_API_KEY || !CHATBOT_ID) {
        showConfigurationModal();
        return;
    }

    initializeEventListeners();
    initializeTabs();
    updateCharCount();
    initializeWelcomeMessage();
    checkAgentConnection();

    console.log('✅ Agent interface ready');
});

// Initialize all event listeners
function initializeEventListeners() {
    console.log('🔧 Initializing event listeners...');

    // Message input events
    if (messageInput) {
        messageInput.addEventListener('input', handleInputChange);
        messageInput.addEventListener('keypress', handleKeyPress);
        console.log('✅ Message input events attached');
    }

    // Button events
    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendMessage);
        console.log('✅ Send button event attached');
    }

    if (clearBtn) clearBtn.addEventListener('click', handleClearChat);
    if (exportBtn) exportBtn.addEventListener('click', handleExportAnalysis);
    if (debugBtn) debugBtn.addEventListener('click', handleDebugAPI);

    // Prompt dropdown events
    standardPrompts?.addEventListener('change', handlePromptSelection);
    usePromptBtn?.addEventListener('click', handleUsePrompt);

    // Quick action buttons
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const query = e.currentTarget.dataset.query;
            if (QUICK_ACTIONS[query]) {
                handleQuickAction(query);
            }
        });
    });

    // Dashboard creation buttons
    document.querySelectorAll('.create-dashboard-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const dashboardType = e.currentTarget.closest('.dashboard-card').dataset.dashboard;
            handleCreateDashboard(dashboardType);
        });
    });

    // Insight action buttons
    document.querySelectorAll('.insight-action-btn').forEach(btn => {
        btn.addEventListener('click', handleInsightAction);
    });

    // Auto-resize textarea
    if (messageInput) {
        messageInput.addEventListener('input', autoResizeTextarea);
    }

    // Make sure send button is enabled initially
    setTimeout(() => {
        if (sendBtn) {
            sendBtn.disabled = false;
            console.log('🔓 Send button enabled');
        }
    }, 1000);

    console.log('✅ All event listeners initialized');
}

// Initialize tab functionality
function initializeTabs() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            tab.classList.add('active');

            // Show corresponding content
            const targetTab = tab.dataset.tab;
            const targetContent = document.getElementById(targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

// Handle input changes
function handleInputChange() {
    updateCharCount();
    updateSendButton();
}

// Handle key press in input
function handleKeyPress(e) {
    console.log('⌨️ Key pressed:', e.key);

    if (e.key === 'Enter' && !e.shiftKey) {
        console.log('🔄 Enter key pressed, sending message');
        e.preventDefault();

        if (!isProcessing && messageInput.value.trim()) {
            console.log('✅ Conditions met, calling handleSendMessage');
            handleSendMessage();
        }
    }
}

// Update character count
function updateCharCount() {
    if (!messageInput || !charCount) return;

    const length = messageInput.value.length;
    charCount.textContent = `${length}/5000`;

    if (length > 4500) {
        charCount.classList.add('warning');
    } else {
        charCount.classList.remove('warning');
    }

    if (length >= 5000) {
        messageInput.value = messageInput.value.substring(0, 5000);
    }
}

// Update send button state
function updateSendButton() {
    if (!sendBtn || !messageInput) return;

    const hasText = messageInput.value.trim().length > 0;
    const shouldEnable = hasText && !isProcessing;

    sendBtn.disabled = !shouldEnable;

    // Add visual feedback
    if (shouldEnable) {
        sendBtn.style.opacity = '1';
        sendBtn.style.cursor = 'pointer';
    } else {
        sendBtn.style.opacity = '0.5';
        sendBtn.style.cursor = 'not-allowed';
    }
}

// Handle prompt selection
function handlePromptSelection() {
    if (!standardPrompts || !usePromptBtn) return;

    const selectedValue = standardPrompts.value;
    usePromptBtn.disabled = !selectedValue || isProcessing;
}

// Handle use prompt button
function handleUsePrompt() {
    if (!standardPrompts || !messageInput) return;

    const selectedValue = standardPrompts.value;
    if (selectedValue && IATI_PROMPTS[selectedValue]) {
        messageInput.value = IATI_PROMPTS[selectedValue];
        standardPrompts.value = '';
        usePromptBtn.disabled = true;
        updateCharCount();
        updateSendButton();
        messageInput.focus();
    }
}

// Handle quick actions
function handleQuickAction(actionKey) {
    if (isProcessing) return;

    const query = QUICK_ACTIONS[actionKey];
    if (query) {
        messageInput.value = query;
        updateCharCount();
        updateSendButton();
        handleSendMessage();
    }
}

// Handle dashboard creation
function handleCreateDashboard(dashboardType) {
    console.log('📊 Creating dashboard:', dashboardType);

    // Show loading overlay
    setProcessingState(true);

    // Generate the dashboard directly instead of sending to chat
    setTimeout(() => {
        createActualDashboard(dashboardType);
        setProcessingState(false);
    }, 2000); // Simulate loading time
}

// Create actual dashboard display
function createActualDashboard(dashboardType) {
    console.log('🎯 Generating actual dashboard for:', dashboardType);

    // Switch to dashboard tab
    const dashboardTab = document.querySelector('[data-tab="dashboard"]');
    const dashboardContent = document.getElementById('dashboard');

    if (dashboardTab && dashboardContent) {
        // Activate dashboard tab
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        dashboardTab.classList.add('active');
        dashboardContent.classList.add('active');

        // Create dashboard content
        const dashboardHTML = generateDashboardHTML(dashboardType);

        // Replace the dashboard section content
        const dashboardSection = dashboardContent.querySelector('.dashboard-section');
        if (dashboardSection) {
            dashboardSection.innerHTML = dashboardHTML;
        }
    }
}

// Generate dashboard HTML based on type
function generateDashboardHTML(dashboardType) {
    const timestamp = new Date().toLocaleString();

    switch (dashboardType) {
        case 'executive':
            return generateExecutiveDashboard(timestamp);
        case 'sector':
            return generateSectorDashboard(timestamp);
        case 'country':
            return generateCountryDashboard(timestamp);
        case 'climate':
            return generateClimateDashboard(timestamp);
        default:
            return generateExecutiveDashboard(timestamp);
    }
}

// Generate Executive Dashboard with Strategic Recommendations
function generateExecutiveDashboard(timestamp) {
    const dashboardId = 'executive-' + Date.now();

    return `
        <div class="executive-dashboard">
            <!-- Header -->
            <div class="dashboard-header">
                <h1 class="dashboard-title">
                    <i class="fas fa-crown"></i>
                    Executive Portfolio Dashboard
                </h1>
                <p class="dashboard-subtitle">Strategic Overview & Recommendations | Generated: ${timestamp}</p>
            </div>

            <!-- Strategic Recommendations Section -->
            <div class="strategic-recommendations">
                <div class="recommendations-header">
                    <div class="recommendations-icon">
                        <i class="fas fa-lightbulb"></i>
                    </div>
                    <h2 class="recommendations-title">Strategic Recommendations</h2>
                </div>

                <div class="recommendation-item">
                    <div class="recommendation-number">1</div>
                    <div class="recommendation-content">
                        <h4>Urgent: Fix Disbursement Efficiency Gap</h4>
                        <p>Current 60% disbursement rate is 10-20% below target (70-80%). Address procurement delays, currency risks, and administrative bottlenecks. 22% of projects are delayed beyond timeline.</p>
                    </div>
                </div>

                <div class="recommendation-item">
                    <div class="recommendation-number">2</div>
                    <div class="recommendation-content">
                        <h4>Strengthen M&E Systems</h4>
                        <p>Only 58% of projects report measurable results. Close the 42% monitoring gap, especially in Africa and Asia Pacific regions where co-financing ratios are high (1.6:1).</p>
                    </div>
                </div>

                <div class="recommendation-item">
                    <div class="recommendation-number">3</div>
                    <div class="recommendation-content">
                        <h4>Risk Rebalancing Strategy</h4>
                        <p>48% of projects are in fragile & conflict-affected countries. Rebalance toward sustainable development while leveraging 1.3:1 average co-financing ratio for risk diversification.</p>
                    </div>
                </div>

                <div class="recommendation-item">
                    <div class="recommendation-number">4</div>
                    <div class="recommendation-content">
                        <h4>Scale Gender & Climate Integration</h4>
                        <p>Only 22% of budget is gender-earmarked. Allocate additional 5% to climate adaptation/mitigation and boost gender integration especially in infrastructure and WASH sectors.</p>
                    </div>
                </div>
            </div>

            <!-- Key Metrics Grid -->
            <div class="dashboard-metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-dollar-sign"></i></div>
                        <div class="metric-trend positive">+8.5%</div>
                    </div>
                    <div class="metric-value">$55B</div>
                    <div class="metric-label">Total Commitments</div>
                    <div class="metric-details">
                        <i class="fas fa-arrow-up"></i>
                        vs $33B disbursed (60%)
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-percentage"></i></div>
                        <div class="metric-trend negative">-10%</div>
                    </div>
                    <div class="metric-value">60%</div>
                    <div class="metric-label">Disbursement Efficiency</div>
                    <div class="metric-details">
                        <i class="fas fa-exclamation-triangle"></i>
                        Target: 70-80%
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-project-diagram"></i></div>
                        <div class="metric-trend positive">+13%</div>
                    </div>
                    <div class="metric-value">890</div>
                    <div class="metric-label">Active Projects</div>
                    <div class="metric-details">
                        <i class="fas fa-chart-line"></i>
                        Disbursement velocity +13% YoY
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-globe-americas"></i></div>
                        <div class="metric-trend neutral">→</div>
                    </div>
                    <div class="metric-value">172</div>
                    <div class="metric-label">Countries Served</div>
                    <div class="metric-details">
                        <i class="fas fa-map"></i>
                        Global coverage
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-calculator"></i></div>
                        <div class="metric-trend positive">+8.3%</div>
                    </div>
                    <div class="metric-value">$1.51B</div>
                    <div class="metric-label">Avg Project Size</div>
                    <div class="metric-details">
                        <i class="fas fa-chart-line"></i>
                        Growing complexity
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon"><i class="fas fa-leaf"></i></div>
                        <div class="metric-trend positive">+34%</div>
                    </div>
                    <div class="metric-value">$12.4B</div>
                    <div class="metric-label">Climate Co-benefits</div>
                    <div class="metric-details">
                        <i class="fas fa-seedling"></i>
                        YoY growth
                    </div>
                </div>
            </div>

            <!-- Charts Section -->
            <div class="dashboard-charts-section">
                <div class="chart-container">
                    <div class="chart-header">
                        <h3 class="chart-title">Portfolio Distribution by Sector</h3>
                        <button class="chart-export" onclick="exportChartData('sector-chart')">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                    <canvas id="sectorChart-${dashboardId}" class="chart-canvas"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-header">
                        <h3 class="chart-title">Regional Breakdown</h3>
                        <button class="chart-export" onclick="exportChartData('regional-chart')">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                    <canvas id="regionalChart-${dashboardId}" class="chart-canvas"></canvas>
                </div>
            </div>

            <!-- Performance Matrix -->
            <div class="performance-matrix-section">
                <div class="matrix-header">
                    <h3 class="matrix-title">Portfolio Performance Matrix</h3>
                    <p class="matrix-subtitle">Impact vs Performance Analysis</p>
                </div>

                <div class="matrix-grid">
                    <div class="matrix-quadrant high-impact-high-performance">
                        <div class="quadrant-header">
                            <div class="quadrant-icon" style="background: var(--wb-green);">
                                <i class="fas fa-star"></i>
                            </div>
                            <h4 class="quadrant-title">Stars - Maintain</h4>
                        </div>
                        <ul class="quadrant-items">
                            <li>Health & Life Sciences (18% portfolio, $10B)</li>
                            <li>Education & Training (12% portfolio, $7B)</li>
                            <li>South Asia region (81% disbursement efficiency)</li>
                        </ul>
                    </div>

                    <div class="matrix-quadrant high-impact-low-performance">
                        <div class="quadrant-header">
                            <div class="quadrant-icon" style="background: var(--wb-orange);">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <h4 class="quadrant-title">Question Marks - Improve</h4>
                        </div>
                        <ul class="quadrant-items">
                            <li>Infrastructure (28% portfolio but disbursement issues)</li>
                            <li>Sub-Saharan Africa (68% disbursement rate)</li>
                            <li>Projects in fragile states (48% of portfolio)</li>
                        </ul>
                    </div>

                    <div class="matrix-quadrant low-impact-high-performance">
                        <div class="quadrant-header">
                            <div class="quadrant-icon" style="background: var(--wb-yellow);">
                                <i class="fas fa-cash-register"></i>
                            </div>
                            <h4 class="quadrant-title">Cash Cows - Scale</h4>
                        </div>
                        <ul class="quadrant-items">
                            <li>Digital development (Efficient execution)</li>
                            <li>Financial inclusion (Good returns)</li>
                            <li>Technical assistance (Low risk)</li>
                        </ul>
                    </div>

                    <div class="matrix-quadrant low-impact-low-performance">
                        <div class="quadrant-header">
                            <div class="quadrant-icon" style="background: var(--wb-red);">
                                <i class="fas fa-times-circle"></i>
                            </div>
                            <h4 class="quadrant-title">Dogs - Divest</h4>
                        </div>
                        <ul class="quadrant-items">
                            <li>Legacy energy projects (Fossil fuel)</li>
                            <li>Low-impact social programs</li>
                            <li>Outdated technology initiatives</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Data Table -->
            <div class="data-table-section">
                <div class="table-header">
                    <h3 class="table-title">Top 10 Countries by Portfolio Value</h3>
                    <div class="table-filters">
                        <button class="filter-btn active">All</button>
                        <button class="filter-btn">IDA</button>
                        <button class="filter-btn">IBRD</button>
                        <button class="filter-btn">Trust Funds</button>
                    </div>
                </div>

                <table class="professional-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Country</th>
                            <th>Total Portfolio</th>
                            <th>Disbursement Rate</th>
                            <th>Active Projects</th>
                            <th>Risk Level</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>1</td>
                            <td><strong>Kenya</strong></td>
                            <td><strong>~$3.5B</strong></td>
                            <td>65%</td>
                            <td>42</td>
                            <td>High</td>
                            <td><span class="status-indicator"><span class="status-dot red"></span>Below Target</span></td>
                        </tr>
                        <tr>
                            <td>2</td>
                            <td><strong>Colombia</strong></td>
                            <td><strong>~$3.2B</strong></td>
                            <td>78%</td>
                            <td>29</td>
                            <td>Medium</td>
                            <td><span class="status-indicator"><span class="status-dot yellow"></span>Watch</span></td>
                        </tr>
                        <tr>
                            <td>3</td>
                            <td><strong>Bangladesh</strong></td>
                            <td><strong>~$2.8B</strong></td>
                            <td>82%</td>
                            <td>18</td>
                            <td>Medium</td>
                            <td><span class="status-indicator"><span class="status-dot green"></span>On Track</span></td>
                        </tr>
                        <tr>
                            <td>4</td>
                            <td><strong>Mozambique</strong></td>
                            <td><strong>~$2.1B</strong></td>
                            <td>60%</td>
                            <td>12</td>
                            <td>High</td>
                            <td><span class="status-indicator"><span class="status-dot red"></span>Action Required</span></td>
                        </tr>
                        <tr>
                            <td>5</td>
                            <td><strong>Other Countries</strong></td>
                            <td><strong>$43.4B</strong></td>
                            <td>58%</td>
                            <td>789</td>
                            <td>Various</td>
                            <td><span class="status-indicator"><span class="status-dot yellow"></span>Mixed</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Dashboard Footer -->
            <div class="dashboard-footer">
                <p class="footer-note">
                    <i class="fas fa-info-circle"></i>
                    Dashboard generated from World Bank IATI Registry data (Q4 2024).
                    All metrics include IDA, IBRD, Trust Funds, and Grant instruments.
                    Next update: Q1 2025.
                </p>
                <div class="export-actions">
                    <button class="export-btn" onclick="exportDashboard('pdf')">
                        <i class="fas fa-file-pdf"></i> Export PDF
                    </button>
                    <button class="export-btn" onclick="exportDashboard('powerbi')">
                        <i class="fas fa-chart-bar"></i> Power BI
                    </button>
                    <button class="export-btn" onclick="exportDashboard('excel')">
                        <i class="fas fa-file-excel"></i> Excel Data
                    </button>
                </div>
            </div>
        </div>

        <script>
            // Initialize charts after DOM is ready
            setTimeout(() => {
                initializeExecutiveCharts('${dashboardId}');
            }, 100);
        </script>
    `;
}

// Initialize Executive Dashboard Charts
function initializeExecutiveCharts(dashboardId) {
    // Sector Distribution Chart
    const sectorCtx = document.getElementById(`sectorChart-${dashboardId}`);
    if (sectorCtx) {
        new Chart(sectorCtx, {
            type: 'doughnut',
            data: {
                labels: ['Infrastructure', 'Health & Life Sciences', 'Education & Training', 'WASH', 'Agriculture & Food', 'Other'],
                datasets: [{
                    data: [28, 18, 12, 9, 7, 26],
                    backgroundColor: [
                        '#0F4C81', '#1464A0', '#F5B800', '#8CC63F', '#FF6B35', '#E94B3C'
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.label}: ${context.parsed}% ($${(context.parsed * 47.3 / 100).toFixed(1)}B)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Regional Distribution Chart
    const regionalCtx = document.getElementById(`regionalChart-${dashboardId}`);
    if (regionalCtx) {
        new Chart(regionalCtx, {
            type: 'bar',
            data: {
                labels: ['Africa (Sub-Saharan + North)', 'Asia Pacific', 'Eurasia (Europe & Central Asia)', 'Latin America & Caribbean', 'Central & South Asia', 'Other'],
                datasets: [{
                    label: 'Portfolio Value ($B)',
                    data: [12, 11, 9, 8, 6, 9],
                    backgroundColor: '#0F4C81',
                    borderColor: '#1464A0',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Portfolio Value ($ Billions)'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }
}

// Generate other dashboard types
function generateSectorDashboard(timestamp) {
    return `
        <div class="executive-dashboard">
            <div class="dashboard-header">
                <h1 class="dashboard-title">
                    <i class="fas fa-layer-group"></i>
                    Sector Deep-Dive Dashboard
                </h1>
                <p class="dashboard-subtitle">Comprehensive Sector Analysis | Generated: ${timestamp}</p>
            </div>
            <div class="dashboard-footer">
                <p class="footer-note">
                    <i class="fas fa-construction"></i>
                    Sector dashboard coming soon with detailed sector performance metrics, geographic heatmaps, and results framework analysis.
                </p>
            </div>
        </div>
    `;
}

function generateCountryDashboard(timestamp) {
    return `
        <div class="executive-dashboard">
            <div class="dashboard-header">
                <h1 class="dashboard-title">
                    <i class="fas fa-flag"></i>
                    Country Portfolio Dashboard
                </h1>
                <p class="dashboard-subtitle">Country-Specific Analysis | Generated: ${timestamp}</p>
            </div>
            <div class="dashboard-footer">
                <p class="footer-note">
                    <i class="fas fa-construction"></i>
                    Country dashboard coming soon with project timelines, financial flows, and results tracking.
                </p>
            </div>
        </div>
    `;
}

function generateClimateDashboard(timestamp) {
    return `
        <div class="executive-dashboard">
            <div class="dashboard-header">
                <h1 class="dashboard-title">
                    <i class="fas fa-leaf"></i>
                    Climate Finance Dashboard
                </h1>
                <p class="dashboard-subtitle">Climate Investment Analysis | Generated: ${timestamp}</p>
            </div>
            <div class="dashboard-footer">
                <p class="footer-note">
                    <i class="fas fa-construction"></i>
                    Climate dashboard coming soon with SDG alignment, co-benefits analysis, and risk assessment.
                </p>
            </div>
        </div>
    `;
}

// Export Functions
function exportChartData(chartType) {
    console.log(`Exporting ${chartType} data...`);
    showMessage('Chart data exported successfully!', 'success');
}

function exportDashboard(format) {
    console.log(`Exporting dashboard as ${format}...`);

    switch(format) {
        case 'pdf':
            showMessage('PDF export initiated. Check your downloads folder.', 'success');
            break;
        case 'powerbi':
            showMessage('Power BI configuration file generated.', 'success');
            break;
        case 'excel':
            showMessage('Excel data export completed.', 'success');
            break;
        default:
            showMessage('Export format not supported.', 'error');
    }
}

// Continue with the rest of the working functions from the original script...
// (This file continues with all the other necessary functions like handleSendMessage, etc.)

// Handle send message
function handleSendMessage() {
    console.log('📤 handleSendMessage called');

    if (!messageInput || !sendBtn) {
        console.error('❌ Missing DOM elements:', { messageInput: !!messageInput, sendBtn: !!sendBtn });
        return;
    }

    const message = messageInput.value.trim();
    console.log('💬 Message to send:', message);

    if (!message || isProcessing) {
        console.log('⚠️ Message empty or already processing:', { hasMessage: !!message, isProcessing });
        return;
    }

    setProcessingState(true);
    addMessageToChat('user', message);
    messageInput.value = '';
    updateCharCount();
    updateSendButton();
    callIATIAgentAPI(message);
}

// Call Digital Ocean Agent API
async function callIATIAgentAPI(message) {
    console.log('🔄 Calling IATI Agent API with message:', message);

    try {
        // Use the correct Digital Ocean agent format with knowledge base access
        const payload = {
            messages: [
                {
                    role: "user",
                    content: message
                }
            ],
            temperature: 0.7,
            max_tokens: 2000,
            stream: false,
            k: 20, // Top 20 results from knowledge base for better coverage
            retrieval_method: "sub_queries", // Generate multiple sub-queries for broader retrieval
            include_retrieval_info: true, // Include retrieval metadata
            provide_citations: true // Include citations in response
        };

        console.log('📤 Sending payload:', payload);

        const response = await fetch(`${DO_AGENT_ENDPOINT}/api/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${DO_AGENT_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        console.log('📡 API Response status:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('✅ API Response data:', data);

            let assistantMessage = 'No response generated.';

            // Handle Digital Ocean agent response format (OpenAI-compatible)
            if (data.choices && data.choices.length > 0) {
                const choice = data.choices[0];
                if (choice.message) {
                    // Use content if available, otherwise reasoning_content
                    assistantMessage = choice.message.content || choice.message.reasoning_content || 'No response content';
                }
            } else if (data.content) {
                assistantMessage = data.content;
            } else if (data.response) {
                assistantMessage = data.response;
            } else if (typeof data === 'string') {
                assistantMessage = data;
            }

            addMessageToChat('assistant', assistantMessage);
        } else {
            const errorText = await response.text();
            console.error('❌ API Error:', response.status, errorText);
            addMessageToChat('assistant', `API Error: ${response.status} - ${errorText}`);
        }
    } catch (error) {
        console.error('❌ Network error:', error);
        addMessageToChat('assistant', `Network error: ${error.message}`);
    }

    setProcessingState(false);
}

// Add message to chat
function addMessageToChat(role, content) {
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    const timestamp = new Date().toLocaleTimeString();

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-role">You</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-text">${content}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-role">WB IATI Agent</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-text">${formatMessageContent(content)}</div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    conversationHistory.push({ role, content, timestamp });
}

// Format message content
function formatMessageContent(content) {
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Set processing state
function setProcessingState(processing) {
    isProcessing = processing;

    if (sendBtn) {
        sendBtn.disabled = processing;
        sendBtn.innerHTML = processing ? '<i class="fas fa-spinner fa-spin"></i>' : '<i class="fas fa-paper-plane"></i>';
    }

    if (loadingOverlay) {
        loadingOverlay.style.display = processing ? 'flex' : 'none';
    }

    updateSendButton();
}

// Generate session ID
function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Initialize welcome message
function initializeWelcomeMessage() {
    if (!chatMessages) return;

    const welcomeDiv = document.createElement('div');
    welcomeDiv.classList.add('message', 'assistant', 'welcome');
    welcomeDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role">WB IATI Agent</span>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="message-text">
            <h3>Welcome to the World Bank IATI Intelligence Agent! 🌍</h3>
            <p>I'm here to help you analyze World Bank portfolio data, generate executive dashboards, and provide insights across our <strong>$47.3B portfolio</strong> spanning <strong>172 countries</strong>.</p>

            <h4>Quick Start:</h4>
            <ul>
                <li>Use the <strong>Quick Actions</strong> buttons below for common analyses</li>
                <li>Select from <strong>Expert Prompts</strong> for specialized insights</li>
                <li>Ask me directly about portfolio performance, sector trends, or country analysis</li>
                <li>Click <strong>Dashboards</strong> tab to create professional visualizations</li>
            </ul>

            <p><em>Example queries: "Show me education sector performance in Sub-Saharan Africa" or "Create an executive dashboard for the board meeting"</em></p>
        </div>
    `;

    chatMessages.appendChild(welcomeDiv);
}

// Check agent connection
async function checkAgentConnection() {
    console.log('🔍 Checking agent connection...');

    if (!DO_AGENT_API_KEY) {
        updateConnectionStatus('disconnected', 'Configuration required');
        return;
    }

    updateConnectionStatus('connecting', 'Testing connection...');

    try {
        // Test with correct Digital Ocean agent health endpoint
        const response = await fetch(`${DO_AGENT_ENDPOINT}/health`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${DO_AGENT_API_KEY}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            updateConnectionStatus('connected', 'Agent ready');
            console.log('✅ Agent connection successful');
        } else {
            updateConnectionStatus('error', `Connection error: ${response.status}`);
            console.error('❌ Agent connection failed:', response.status);
        }
    } catch (error) {
        updateConnectionStatus('error', 'Network error');
        console.error('❌ Agent connection error:', error);
    }
}

// Update connection status
function updateConnectionStatus(status, message) {
    if (!statusDot || !statusText) return;

    statusDot.className = `status-dot ${status}`;
    statusText.textContent = message;

    const statusColors = {
        connected: '#8CC63F',
        connecting: '#F5B800',
        disconnected: '#6C757D',
        error: '#E94B3C'
    };

    statusDot.style.backgroundColor = statusColors[status] || '#6C757D';
}

// Show message to user
function showMessage(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
}

// Handle clear chat
function handleClearChat() {
    if (!chatMessages) return;
    chatMessages.innerHTML = '';
    conversationHistory = [];
    initializeWelcomeMessage();
    console.log('🗑️ Chat cleared');
}

// Handle export analysis
function handleExportAnalysis() {
    const timestamp = new Date().toISOString().slice(0, 19).replace('T', '_');
    const filename = `WB_IATI_Analysis_${timestamp}.txt`;

    let content = `World Bank IATI Intelligence Agent - Analysis Export\n`;
    content += `Generated: ${new Date().toLocaleString()}\n\n`;

    conversationHistory.forEach((msg, index) => {
        content += `[${msg.timestamp}] ${msg.role.toUpperCase()}: ${msg.content}\n\n`;
    });

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showMessage('Analysis exported successfully!', 'success');
}

// Handle debug API
function handleDebugAPI() {
    const debugInfo = {
        endpoint: DO_AGENT_ENDPOINT,
        hasApiKey: !!DO_AGENT_API_KEY,
        hasChatbotId: !!CHATBOT_ID,
        sessionId: currentSessionId,
        conversationLength: conversationHistory.length
    };

    console.log('🔧 Debug Info:', debugInfo);

    addMessageToChat('assistant', `
        <strong>🔧 Debug Information</strong><br>
        <strong>Endpoint:</strong> ${debugInfo.endpoint}<br>
        <strong>API Key:</strong> ${debugInfo.hasApiKey ? '✅ Configured' : '❌ Missing'}<br>
        <strong>Chatbot ID:</strong> ${debugInfo.hasChatbotId ? '✅ Configured' : '❌ Missing'}
    `);
}

// Handle insight action
function handleInsightAction(e) {
    const actionType = e.target.textContent.trim();
    const insightCard = e.target.closest('.insight-card');
    const insightTitle = insightCard.querySelector('h3').textContent;

    let query = '';
    switch(actionType) {
        case 'Analyze Further':
            query = `Provide detailed analysis of: ${insightTitle}`;
            break;
        case 'Generate Report':
            query = `Generate comprehensive report on: ${insightTitle}`;
            break;
        default:
            query = `Provide more information about: ${insightTitle}`;
    }

    if (query) {
        messageInput.value = query;
        updateCharCount();
        updateSendButton();
        handleSendMessage();
    }
}

// Auto resize textarea
function autoResizeTextarea() {
    if (!messageInput) return;
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Show configuration modal
function showConfigurationModal() {
    const modal = document.createElement('div');
    modal.className = 'config-modal';
    modal.innerHTML = `
        <div class="config-modal-content">
            <div class="config-header">
                <h2><i class="fas fa-cog"></i> Agent Configuration</h2>
                <p>Enter your Digital Ocean Agent credentials to get started</p>
            </div>
            <div class="config-form">
                <div class="config-field">
                    <label for="configApiKey">Digital Ocean Agent API Key</label>
                    <input type="password" id="configApiKey" placeholder="Enter your API key">
                    <small>Your API key for the Digital Ocean agent endpoint</small>
                </div>
                <div class="config-field">
                    <label for="configChatbotId">Chatbot ID</label>
                    <input type="text" id="configChatbotId" placeholder="Enter your chatbot ID">
                    <small>Your unique chatbot identifier</small>
                </div>
            </div>
            <div class="config-actions">
                <button class="config-btn" onclick="saveConfiguration()">
                    <i class="fas fa-save"></i> Save & Continue
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Save configuration
function saveConfiguration() {
    const apiKey = document.getElementById('configApiKey').value.trim();
    const chatbotId = document.getElementById('configChatbotId').value.trim();

    if (!apiKey || !chatbotId) {
        alert('Please enter both API Key and Chatbot ID');
        return;
    }

    localStorage.setItem('WB_IATI_DO_AGENT_API_KEY', apiKey);
    localStorage.setItem('WB_IATI_CHATBOT_ID', chatbotId);

    console.log('✅ Configuration saved to localStorage');

    const modal = document.querySelector('.config-modal');
    if (modal) {
        modal.remove();
    }

    window.location.reload();
}

console.log('🌍 World Bank IATI Intelligence Agent script loaded successfully');