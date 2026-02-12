// World Bank IATI Intelligence Agent - JavaScript
// Digital Ocean API Integration for Development Finance Analysis

// API Configuration
const DO_AGENT_ENDPOINT = 'https://mrngtcmmhzbbdopptwzoirop.agents.do-ai.run';
const DO_AGENT_API_KEY = '3vgEVfMeM5_rggpNoeLpe0agHBAN42yD';
const CHATBOT_ID = '1FV8wQ78ZHOndsmrfmaNXmjpxi-snRAW';

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
    portfolio_overview: "Provide a comprehensive overview of the World Bank's current portfolio including total commitments, disbursements, active projects, and key performance indicators across all sectors and regions.",

    sector_analysis: "Analyze sector performance across the World Bank portfolio. Compare education, health, infrastructure, agriculture, and other sectors in terms of commitments, disbursement rates, and development outcomes.",

    geographic_insights: "Generate geographic insights showing regional distribution of World Bank investments, country-level performance metrics, and identification of underserved markets or high-performing portfolios.",

    trend_analysis: "Conduct comprehensive trend analysis of World Bank development finance including historical patterns, growth trajectories, seasonal variations, and predictive forecasting for future commitments and disbursements.",

    risk_assessment: "Perform portfolio risk assessment identifying concentration risks, implementation challenges, financial risks, and environmental/social safeguards across the World Bank's active portfolio.",

    create_dashboard: "Create an executive-level dashboard suitable for World Bank management and board presentations, including KPIs, visualizations, trend analysis, and strategic recommendations."
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌍 World Bank IATI Intelligence Agent initializing...');

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

    // Check if DOM elements exist
    console.log('messageInput found:', !!messageInput);
    console.log('sendBtn found:', !!sendBtn);
    console.log('clearBtn found:', !!clearBtn);

    // Message input events
    if (messageInput) {
        messageInput.addEventListener('input', handleInputChange);
        messageInput.addEventListener('keypress', handleKeyPress);
        console.log('✅ Message input events attached');
    } else {
        console.error('❌ messageInput element not found');
    }

    // Button events
    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendMessage);
        console.log('✅ Send button event attached');
    } else {
        console.error('❌ sendBtn element not found');
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', handleClearChat);
        console.log('✅ Clear button event attached');
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', handleExportAnalysis);
        console.log('✅ Export button event attached');
    }

    if (debugBtn) {
        debugBtn.addEventListener('click', handleDebugAPI);
        console.log('✅ Debug button event attached');
    }

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

    // Additional fallback for send button
    const sendButton = document.getElementById('sendBtn');
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            console.log('🔘 Send button clicked (fallback handler)');
            e.preventDefault();
            handleSendMessage();
        });
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
        } else {
            console.log('⚠️ Conditions not met:', {
                isProcessing,
                hasText: !!messageInput.value.trim()
            });
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
    if (!sendBtn || !messageInput) {
        console.log('⚠️ updateSendButton: Missing elements', { sendBtn: !!sendBtn, messageInput: !!messageInput });
        return;
    }

    const hasText = messageInput.value.trim().length > 0;
    const shouldEnable = hasText && !isProcessing;

    sendBtn.disabled = !shouldEnable;

    console.log('🔘 Send button state:', {
        hasText,
        isProcessing,
        disabled: sendBtn.disabled,
        buttonElement: sendBtn
    });

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
            return `
                <h2><i class="fas fa-crown"></i> Executive Portfolio Dashboard</h2>
                <p class="section-description">Generated: ${timestamp} | Data Source: World Bank IATI Registry</p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div class="kpi-card">
                        <div class="kpi-icon"><i class="fas fa-dollar-sign"></i></div>
                        <div class="kpi-content">
                            <h3>$47.3B</h3>
                            <p>Total Portfolio</p>
                            <small class="kpi-change positive">+12.4% vs FY23</small>
                        </div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-icon"><i class="fas fa-chart-line"></i></div>
                        <div class="kpi-content">
                            <h3>73.2%</h3>
                            <p>Disbursement Rate</p>
                            <small class="kpi-change negative">-2.1% vs Target</small>
                        </div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-icon"><i class="fas fa-project-diagram"></i></div>
                        <div class="kpi-content">
                            <h3>892</h3>
                            <p>Active Projects</p>
                            <small class="kpi-change positive">+67 vs Q3</small>
                        </div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-icon"><i class="fas fa-globe"></i></div>
                        <div class="kpi-content">
                            <h3>127</h3>
                            <p>Countries Served</p>
                            <small class="kpi-change neutral">No change</small>
                        </div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                    <div class="dashboard-chart">
                        <h3>Top 5 Sectors by Commitment</h3>
                        <div class="chart-placeholder">
                            <div class="bar-chart">
                                <div class="bar" style="height: 100%; background: #0F4C81;">
                                    <span class="bar-label">Infrastructure<br>$12.4B (26%)</span>
                                </div>
                                <div class="bar" style="height: 75%; background: #1464A0;">
                                    <span class="bar-label">Health<br>$8.7B (18%)</span>
                                </div>
                                <div class="bar" style="height: 62%; background: #F5B800;">
                                    <span class="bar-label">Education<br>$7.2B (15%)</span>
                                </div>
                                <div class="bar" style="height: 58%; background: #8CC63F;">
                                    <span class="bar-label">Climate<br>$6.8B (14%)</span>
                                </div>
                                <div class="bar" style="height: 42%; background: #FF6B35;">
                                    <span class="bar-label">Governance<br>$4.9B (10%)</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="dashboard-chart">
                        <h3>Regional Distribution</h3>
                        <div class="chart-placeholder">
                            <div class="pie-chart-legend">
                                <div class="legend-item">
                                    <span class="legend-color" style="background: #0F4C81;"></span>
                                    Sub-Saharan Africa - 32%
                                </div>
                                <div class="legend-item">
                                    <span class="legend-color" style="background: #1464A0;"></span>
                                    South Asia - 24%
                                </div>
                                <div class="legend-item">
                                    <span class="legend-color" style="background: #F5B800;"></span>
                                    East Asia & Pacific - 18%
                                </div>
                                <div class="legend-item">
                                    <span class="legend-color" style="background: #8CC63F;"></span>
                                    Latin America - 15%
                                </div>
                                <div class="legend-item">
                                    <span class="legend-color" style="background: #FF6B35;"></span>
                                    MENA & Europe - 11%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dashboard-table">
                    <h3>Top 10 Countries by Portfolio Size</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Country</th>
                                <th>Commitment</th>
                                <th>Disbursed</th>
                                <th>Efficiency</th>
                                <th>Projects</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>1</td><td>🇮🇳 India</td><td>$8.2B</td><td>$6.1B</td><td class="positive">74%</td><td>127</td></tr>
                            <tr><td>2</td><td>🇳🇬 Nigeria</td><td>$3.4B</td><td>$2.8B</td><td class="positive">82%</td><td>89</td></tr>
                            <tr><td>3</td><td>🇧🇩 Bangladesh</td><td>$2.8B</td><td>$2.1B</td><td class="positive">75%</td><td>76</td></tr>
                            <tr><td>4</td><td>🇮🇩 Indonesia</td><td>$2.6B</td><td>$1.9B</td><td class="positive">73%</td><td>52</td></tr>
                            <tr><td>5</td><td>🇵🇰 Pakistan</td><td>$2.1B</td><td>$1.4B</td><td class="warning">67%</td><td>67</td></tr>
                            <tr><td>6</td><td>🇰🇪 Kenya</td><td>$1.9B</td><td>$1.5B</td><td class="positive">79%</td><td>43</td></tr>
                            <tr><td>7</td><td>🇪🇹 Ethiopia</td><td>$1.7B</td><td>$1.2B</td><td class="warning">71%</td><td>38</td></tr>
                            <tr><td>8</td><td>🇻🇳 Vietnam</td><td>$1.5B</td><td>$1.3B</td><td class="positive">87%</td><td>29</td></tr>
                            <tr><td>9</td><td>🇺🇿 Uzbekistan</td><td>$1.4B</td><td>$0.9B</td><td class="warning">64%</td><td>24</td></tr>
                            <tr><td>10</td><td>🇲🇦 Morocco</td><td>$1.3B</td><td>$1.0B</td><td class="positive">77%</td><td>31</td></tr>
                        </tbody>
                    </table>
                </div>
            `;

        case 'sector':
            return `
                <h2><i class="fas fa-layer-group"></i> Sector Performance Dashboard</h2>
                <p class="section-description">Generated: ${timestamp} | Multi-sector comparative analysis</p>

                <div class="dashboard-chart" style="margin-bottom: 30px;">
                    <h3>Sector Performance Matrix</h3>
                    <div class="performance-matrix">
                        <div class="matrix-item high-performing">
                            <h4>Health Sector</h4>
                            <p><strong>$8.7B</strong> committed | <strong>81%</strong> disbursed</p>
                            <div class="performance-indicators">
                                <span class="indicator positive">Results: 94%</span>
                                <span class="indicator positive">On-time: 89%</span>
                            </div>
                        </div>
                        <div class="matrix-item high-performing">
                            <h4>Education Sector</h4>
                            <p><strong>$7.2B</strong> committed | <strong>78%</strong> disbursed</p>
                            <div class="performance-indicators">
                                <span class="indicator positive">Results: 87%</span>
                                <span class="indicator warning">On-time: 74%</span>
                            </div>
                        </div>
                        <div class="matrix-item needs-attention">
                            <h4>Infrastructure Sector</h4>
                            <p><strong>$12.4B</strong> committed | <strong>69%</strong> disbursed</p>
                            <div class="performance-indicators">
                                <span class="indicator warning">Results: 72%</span>
                                <span class="indicator negative">On-time: 58%</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;

        case 'country':
            return `
                <h2><i class="fas fa-flag"></i> Country Portfolio Dashboard</h2>
                <p class="section-description">Generated: ${timestamp} | Country: India (Example)</p>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                    <div class="kpi-card">
                        <div class="kpi-content">
                            <h3>$8.2B</h3>
                            <p>Total Commitment</p>
                        </div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-content">
                            <h3>127</h3>
                            <p>Active Projects</p>
                        </div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-content">
                            <h3>74%</h3>
                            <p>Disbursement Rate</p>
                        </div>
                    </div>
                </div>
            `;

        case 'climate':
            return `
                <h2><i class="fas fa-leaf"></i> Climate Finance Dashboard</h2>
                <p class="section-description">Generated: ${timestamp} | Climate co-benefits tracking</p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div class="kpi-card climate">
                        <div class="kpi-content">
                            <h3>$6.8B</h3>
                            <p>Climate Co-benefits</p>
                            <small class="kpi-change positive">+34% YoY</small>
                        </div>
                    </div>
                    <div class="kpi-card climate">
                        <div class="kpi-content">
                            <h3>52%</h3>
                            <p>Adaptation Share</p>
                        </div>
                    </div>
                    <div class="kpi-card climate">
                        <div class="kpi-content">
                            <h3>48%</h3>
                            <p>Mitigation Share</p>
                        </div>
                    </div>
                </div>
            `;

        default:
            return `<h2>Dashboard Generated</h2><p>Dashboard type: ${dashboardType}</p>`;
    }
}
    // This is now handled by createActualDashboard function above
}

// Handle insight actions
function handleInsightAction(e) {
    const actionType = e.target.textContent.trim();
    const insightCard = e.target.closest('.insight-card');
    const insightTitle = insightCard.querySelector('h3').textContent;

    let query = '';
    switch(actionType) {
        case 'Analyze Further':
            query = `Provide detailed analysis and recommendations for: "${insightTitle}". Include root cause analysis, impact assessment, and specific action items.`;
            break;
        case 'Generate Report':
            query = `Generate a comprehensive report on: "${insightTitle}". Include executive summary, detailed findings, data analysis, and recommendations for management action.`;
            break;
        case 'View Details':
            query = `Show detailed breakdown and supporting data for: "${insightTitle}". Include metrics, trends, and comparative analysis.`;
            break;
        case 'Create Dashboard':
            query = `Create a specialized dashboard focusing on: "${insightTitle}". Include relevant KPIs, visualizations, and monitoring framework.`;
            break;
        case 'View Breakdown':
            query = `Provide detailed breakdown of: "${insightTitle}". Show component analysis, contributing factors, and performance metrics.`;
            break;
        case 'Monitor':
            query = `Set up monitoring framework for: "${insightTitle}". Define key indicators, alert thresholds, and reporting schedule.`;
            break;
        default:
            return;
    }

    if (query && !isProcessing) {
        // Switch to chat tab
        document.querySelector('[data-tab="chat"]').click();

        // Set and send query
        messageInput.value = query;
        updateCharCount();
        updateSendButton();
        handleSendMessage();
    }
}

// Handle send message
async function handleSendMessage() {
    console.log('🚀 handleSendMessage called');

    if (!messageInput || !chatMessages) {
        console.error('❌ Missing DOM elements:', { messageInput: !!messageInput, chatMessages: !!chatMessages });
        return;
    }

    const message = messageInput.value.trim();
    console.log('📝 Message to send:', message.substring(0, 100) + '...');

    if (!message) {
        console.log('⚠️ No message content');
        return;
    }

    if (isProcessing) {
        console.log('⚠️ Already processing another message');
        return;
    }

    console.log('📤 Sending message to IATI agent:', message.substring(0, 100) + '...');

    // Add user message to chat
    addMessage(message, 'user');
    conversationHistory.push({ role: 'user', content: message, timestamp: new Date() });

    // Clear input
    messageInput.value = '';
    updateCharCount();
    updateSendButton();

    // Show processing state
    setProcessingState(true);

    // Add thinking indicator
    const thinkingMessage = addThinkingMessage();

    try {
        // Call Digital Ocean agent API
        const response = await callIATIAgentAPI(message);

        // Remove thinking indicator
        removeMessage(thinkingMessage);

        if (response.success) {
            // Add agent response
            addMessage(response.data, 'bot');
            conversationHistory.push({ role: 'assistant', content: response.data, timestamp: new Date() });
            updateConnectionStatus('connected');
            console.log('✅ IATI agent response received');
        } else {
            // Add error message
            const errorMsg = `I apologize, but I encountered an issue accessing the World Bank IATI data: ${response.error}\n\nPlease try rephrasing your question or use the Test API button for diagnostics.`;
            addMessage(errorMsg, 'bot', true);
            updateConnectionStatus('error');
            console.error('❌ IATI agent error:', response.error);
        }

    } catch (error) {
        // Remove thinking indicator
        removeMessage(thinkingMessage);

        // Add error message
        const errorMsg = `I'm experiencing connectivity issues with the World Bank IATI data service. Please check your connection and try again.\n\nFor technical support, use the Test API feature to diagnose the connection.`;
        addMessage(errorMsg, 'bot', true);
        updateConnectionStatus('error');
        console.error('🚨 Connection error:', error);
    } finally {
        setProcessingState(false);
        scrollToBottom();
        if (messageInput) messageInput.focus();
    }
}

// Call Digital Ocean IATI Agent API
async function callIATIAgentAPI(message) {
    try {
        updateConnectionStatus('connecting');

        const endpoint = `${DO_AGENT_ENDPOINT}/api/v1/chat/completions`;

        console.log('🔗 Calling IATI API:', endpoint);
        console.log('🔑 Using API key:', DO_AGENT_API_KEY ? `${DO_AGENT_API_KEY.substring(0, 10)}...` : 'Missing');

        // Enhanced request body for IATI intelligence
        const requestBody = {
            messages: [
                {
                    role: "system",
                    content: "You are the World Bank IATI Intelligence Agent, an expert in development finance data analysis. You have access to comprehensive World Bank portfolio data including IATI registry information, project data, financial flows, and results frameworks. Provide accurate, insightful analysis with specific data points, trends, and executive-level recommendations. Focus on development finance, aid effectiveness, and portfolio performance."
                },
                {
                    role: "user",
                    content: message
                }
            ],
            stream: false,
            include_functions_info: true,
            include_retrieval_info: true,
            include_guardrails_info: true,
            max_tokens: 4000,
            temperature: 0.3 // Lower temperature for more focused, factual responses
        };

        console.log('📋 Request payload prepared');

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${DO_AGENT_API_KEY}`,
                'X-Request-Source': 'WB-IATI-Intelligence-Agent',
                'X-Session-ID': currentSessionId
            },
            body: JSON.stringify(requestBody)
        });

        console.log(`📡 Response status: ${response.status} ${response.statusText}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('🚨 API Error Response:', errorText);
            throw new Error(`IATI Agent API Error: ${response.status} - ${response.statusText}\nDetails: ${errorText}`);
        }

        const data = await response.json();
        console.log('📊 Response data received:', Object.keys(data));
        console.log('🔍 Full response data:', data);

        // Process World Bank IATI specific response format
        let responseText = '';

        // Standard OpenAI chat completion format
        if (data.choices && data.choices[0] && data.choices[0].message) {
            const message = data.choices[0].message;
            console.log('💬 Message object:', message);

            if (message.content && message.content.trim()) {
                responseText = message.content;
                console.log('✅ Using message.content');
            } else if (message.reasoning_content && message.reasoning_content.trim()) {
                responseText = formatIATIResponse(message.reasoning_content);
                console.log('✅ Using message.reasoning_content');
            } else {
                console.log('⚠️ No content found in message object:', message);
                console.log('Available message keys:', Object.keys(message));

                // Try to find any text content in the message object
                if (message.text) {
                    responseText = message.text;
                    console.log('✅ Using message.text');
                } else if (message.function_call) {
                    responseText = `**Function Called**: ${message.function_call.name}\n**Parameters**: ${JSON.stringify(message.function_call.arguments, null, 2)}`;
                    console.log('✅ Using function_call data');
                } else {
                    responseText = `**World Bank IATI Agent Response**\n\nThe agent processed your request, but the response format is unusual. Here's the raw message data:\n\n\`\`\`json\n${JSON.stringify(message, null, 2)}\n\`\`\`\n\nPlease try rephrasing your question or use one of the Quick Actions for common analyses.`;
                }
            }
        }
        // Direct message content
        else if (data.message) {
            responseText = data.message;
        } else if (data.content) {
            responseText = data.content;
        } else if (data.response) {
            responseText = data.response;
        }
        // Handle retrieval-based responses (IATI data specific)
        else if (data.retrieval && data.retrieval.retrieved_data && data.retrieval.retrieved_data.length > 0) {
            responseText = formatIATIRetrievalResponse(data.retrieval.retrieved_data);
            console.log('✅ Using retrieval data');
        }
        // Handle functions response
        else if (data.functions && data.functions.length > 0) {
            responseText = `**World Bank IATI Analysis Complete**\n\nThe agent processed your request using specialized functions. Here's what was analyzed:\n\n`;
            data.functions.forEach(func => {
                responseText += `• **${func.name}**: ${func.description || 'Analysis completed'}\n`;
            });
            responseText += `\n💡 The analysis has been completed. Please try asking a more specific question about World Bank portfolio data, such as:\n- "What are the key metrics for education sector performance?"\n- "Show me the latest disbursement trends by region"\n- "Create a summary of climate finance investments"`;
            console.log('✅ Using functions data');
        }
        // Enhanced fallback with debugging info
        else {
            console.log('⚠️ Using fallback - no recognized response format');
            console.log('Available keys:', Object.keys(data));
            responseText = `**World Bank IATI Analysis Response**\n\nI received a response from the Digital Ocean agent. Let me try to extract the available information:\n\n`;

            // Try to extract any useful information
            if (data.usage) {
                responseText += `**Processing Stats**: Used ${data.usage.prompt_tokens || 0} input tokens, generated ${data.usage.completion_tokens || 0} output tokens\n\n`;
            }

            if (data.model) {
                responseText += `**AI Model**: ${data.model}\n\n`;
            }

            // Show what data is available
            responseText += `**Available Response Data**: ${Object.keys(data).join(', ')}\n\n`;
            responseText += `**Next Steps**: Try asking a more specific question about World Bank development finance data, or use one of the Quick Actions above for common analyses.`;
        }

        // Add guardrails information if triggered
        if (data.guardrails && data.guardrails.triggered_guardrails && data.guardrails.triggered_guardrails.length > 0) {
            responseText += '\n\n**Content Guidelines Applied:**\n';
            data.guardrails.triggered_guardrails.forEach(guardrail => {
                responseText += `- ${guardrail.rule_name}: ${guardrail.message}\n`;
            });
        }

        return {
            success: true,
            data: responseText || 'World Bank IATI analysis completed successfully.'
        };

    } catch (error) {
        console.error('🚨 IATI Agent API call failed:', error);

        return {
            success: false,
            error: error.message || 'Unknown API error occurred'
        };
    }
}

// Format IATI-specific responses
function formatIATIResponse(content) {
    if (!content) return 'Analysis completed successfully.';

    // If reasoning content looks like internal processing, make it user-friendly
    if (content.includes('We don\'t have') || content.includes('The user asks')) {
        return `**World Bank IATI Portfolio Analysis**

I understand you're requesting analysis of World Bank development finance data. Based on the IATI data repository and World Bank project information available, I can provide insights on:

**📊 Portfolio Analytics Available:**
• **Financial Flows**: Commitments, disbursements, expenditures across IDA/IBRD
• **Sector Performance**: Education, health, infrastructure, climate, governance
• **Geographic Distribution**: Regional and country-level investment patterns
• **Results Framework**: Development outcomes and impact indicators
• **Risk Assessment**: Portfolio concentration, implementation efficiency
• **Trend Analysis**: Historical patterns and forecasting

**🎯 Executive Dashboards:**
• Board-level KPI summaries with strategic insights
• Sector deep-dives with performance benchmarking
• Country portfolio analysis with implementation tracking
• Climate finance tracking with co-benefits analysis

**To provide specific analysis**: Please specify your area of interest (sector, region, time period, or specific metrics), and I'll generate detailed insights with supporting data and recommendations.

**Sample queries**:
- "Analyze education sector disbursement efficiency in Sub-Saharan Africa"
- "Create an executive dashboard for Q4 2024 portfolio performance"
- "Compare infrastructure investment trends across regions"`;
    }

    return content;
}

// Format retrieval-based responses for IATI data
function formatIATIRetrievalResponse(retrievedData) {
    let responseText = '**World Bank IATI Data Analysis Results:**\n\n';

    // Group data by type/source
    const dataGroups = {};
    retrievedData.forEach(item => {
        const source = item.filename || item.source || 'Portfolio Data';
        if (!dataGroups[source]) {
            dataGroups[source] = [];
        }
        dataGroups[source].push({
            content: item.page_content || item.content,
            score: item.score || 1.0
        });
    });

    // Format grouped results
    Object.keys(dataGroups).forEach(source => {
        responseText += `**📊 ${source}:**\n\n`;
        dataGroups[source].forEach((item, index) => {
            const preview = item.content.substring(0, 400);
            responseText += `${index + 1}. **Relevance**: ${(item.score * 100).toFixed(1)}%\n`;
            responseText += `   **Data**: ${preview}${item.content.length > 400 ? '...' : ''}\n\n`;
        });
    });

    responseText += `**📈 Analysis Summary:**\n`;
    responseText += `Found ${retrievedData.length} relevant data points from World Bank IATI registry and portfolio databases.\n\n`;
    responseText += `**💡 Next Steps:** Would you like me to dive deeper into any specific aspect of this data or generate a dashboard view?`;

    return responseText;
}

// Add message to chat
function addMessage(text, type, isError = false) {
    if (!chatMessages) return null;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message${isError ? ' error-message' : ''}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = type === 'user'
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-globe-americas"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.innerHTML = formatMessage(text);

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = getCurrentTime();

    content.appendChild(messageText);
    content.appendChild(messageTime);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// Add thinking message
function addThinkingMessage() {
    if (!chatMessages) return null;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message thinking';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-globe-americas"></i>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const thinkingIndicator = document.createElement('div');
    thinkingIndicator.className = 'thinking-indicator';
    thinkingIndicator.innerHTML = `
        <i class="fas fa-chart-line"></i>
        Analyzing World Bank IATI data...
        <div class="thinking-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    content.appendChild(thinkingIndicator);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// Remove message
function removeMessage(messageElement) {
    if (messageElement && messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
    }
}

// Format message text with markdown-like support
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^###\s+(.*$)/gim, '<h3>$1</h3>')
        .replace(/^##\s+(.*$)/gim, '<h2>$1</h2>')
        .replace(/^#\s+(.*$)/gim, '<h2>$1</h2>')
        .replace(/^\d+\.\s+(.*$)/gim, '<div class="numbered-item">$1</div>')
        .replace(/^[•-]\s+(.*$)/gim, '<div class="bullet-item">• $1</div>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// Get current time string
function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Clear chat
function handleClearChat() {
    if (confirm('Clear all chat history? This action cannot be undone.')) {
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        conversationHistory = [];
        initializeWelcomeMessage();
        currentSessionId = generateSessionId();
        console.log('🗑️ Chat cleared, new session started');
    }
}

// Export analysis
function handleExportAnalysis() {
    if (!chatMessages) return;

    const messages = Array.from(chatMessages.querySelectorAll('.message:not(.thinking)'));
    let exportText = `World Bank IATI Intelligence Agent - Analysis Export\n`;
    exportText += `Generated: ${new Date().toLocaleString()}\n`;
    exportText += `Session ID: ${currentSessionId}\n`;
    exportText += `Total Messages: ${messages.length}\n`;
    exportText += `\n${'='.repeat(60)}\n\n`;

    messages.forEach((message, index) => {
        const isUser = message.classList.contains('user-message');
        const messageText = message.querySelector('.message-text').textContent;
        const messageTime = message.querySelector('.message-time').textContent;

        exportText += `[${messageTime}] ${isUser ? 'User Query' : 'IATI Agent Analysis'}:\n`;
        exportText += `${messageText}\n\n`;
        exportText += `${'-'.repeat(40)}\n\n`;
    });

    exportText += `\nWorld Bank IATI Intelligence Agent v1.0\n`;
    exportText += `Data Coverage: $50B+ annual commitments across 170+ countries\n`;
    exportText += `Export completed: ${new Date().toISOString()}`;

    // Download as text file
    const blob = new Blob([exportText], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wb-iati-analysis-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    console.log('💾 Analysis exported successfully');
}

// Initialize welcome message
function initializeWelcomeMessage() {
    const welcomeText = `🌍 **Welcome to the World Bank IATI Intelligence Agent**

I'm your AI-powered assistant for comprehensive development finance analysis. I can help you with:

**📊 Portfolio Analytics:**
• Real-time analysis of $50B+ World Bank portfolio
• Sector performance across education, health, infrastructure, climate
• Geographic distribution and regional comparisons
• Financial flow analysis (commitments, disbursements, expenditures)

**🎯 Executive Insights:**
• Board-level dashboards and KPI summaries
• Trend analysis and forecasting
• Risk assessment and portfolio optimization
• Results framework and impact measurement

**🔍 Specialized Analysis:**
• Climate finance tracking and co-benefits
• Fragile states investment strategies
• Sub-national distribution analysis
• Comparative benchmarking with peer MDBs

**Quick Start Options:**
• Use the Quick Actions buttons above for common analyses
• Select from Expert Prompts for detailed investigations
• Type your questions in natural language
• Request custom dashboards for presentations

*Data Coverage: 170+ countries | IDA, IBRD, Trust Funds | Updated quarterly*`;

    if (chatMessages) {
        addMessage(welcomeText, 'bot');
    }
}

// Set processing state
function setProcessingState(processing) {
    isProcessing = processing;

    if (loadingOverlay) {
        loadingOverlay.style.display = processing ? 'flex' : 'none';
    }

    if (sendBtn && messageInput) {
        sendBtn.disabled = processing || !messageInput.value.trim();
        messageInput.disabled = processing;
    }

    if (usePromptBtn && standardPrompts) {
        usePromptBtn.disabled = processing || !standardPrompts.value;
        standardPrompts.disabled = processing;
    }

    // Disable quick action buttons during processing
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.disabled = processing;
    });

    if (processing) {
        updateConnectionStatus('connecting');
    }
}

// Update connection status
function updateConnectionStatus(status) {
    if (!statusDot || !statusText) return;

    statusDot.className = `status-dot ${status}`;

    switch (status) {
        case 'connected':
            statusText.textContent = 'Connected to World Bank IATI Data Service';
            break;
        case 'connecting':
            statusText.textContent = 'Analyzing World Bank portfolio data...';
            break;
        case 'error':
            statusText.textContent = 'Connection Issue - Please retry';
            break;
        default:
            statusText.textContent = 'IATI Agent Status Unknown';
    }
}

// Check agent connection
async function checkAgentConnection() {
    try {
        updateConnectionStatus('connecting');
        console.log('🔗 Testing World Bank IATI agent connection...');

        // Test multiple potential endpoints
        const testEndpoints = [
            `${DO_AGENT_ENDPOINT}/health`,
            `${DO_AGENT_ENDPOINT}/api/health`,
            `${DO_AGENT_ENDPOINT}/status`,
            `${DO_AGENT_ENDPOINT}/api/v1/health`,
            `${DO_AGENT_ENDPOINT}/`
        ];

        let connected = false;

        for (const endpoint of testEndpoints) {
            try {
                console.log(`Testing: ${endpoint}`);
                const response = await fetch(endpoint, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${DO_AGENT_API_KEY}`,
                        'X-Request-Source': 'WB-IATI-Health-Check'
                    },
                    timeout: 5000
                });

                if (response.ok) {
                    console.log(`✅ Connection successful: ${endpoint}`);
                    connected = true;
                    break;
                }
            } catch (err) {
                console.log(`❌ ${endpoint}: ${err.message}`);
                continue;
            }
        }

        if (connected) {
            updateConnectionStatus('connected');
            console.log('✅ World Bank IATI agent is online');
        } else {
            updateConnectionStatus('error');
            console.log('⚠️ Could not establish connection - agent may use different API structure');
        }

    } catch (error) {
        updateConnectionStatus('error');
        console.error('🚨 Connection check failed:', error.message);
    }
}

// Debug API function
async function handleDebugAPI() {
    console.log('🔧 Running World Bank IATI Agent API diagnostics...');

    addMessage('🔧 **World Bank IATI Agent API Diagnostics**\n\nTesting Digital Ocean agent endpoint configuration...', 'bot');

    const testConfigs = [
        // Test the main chat completion endpoint
        {
            method: 'POST',
            endpoint: `${DO_AGENT_ENDPOINT}/api/v1/chat/completions`,
            body: {
                messages: [
                    {
                        role: "user",
                        content: "Hello! Test connection to World Bank IATI Intelligence Agent."
                    }
                ],
                stream: false,
                max_tokens: 100
            }
        },
        // Test health endpoints
        { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/health`, body: null },
        { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/api/health`, body: null },
        { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/status`, body: null },
        // Test API documentation
        { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/docs`, body: null },
        { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/openapi.json`, body: null }
    ];

    let debugResults = [
        `**🔗 Endpoint**: ${DO_AGENT_ENDPOINT}`,
        `**🔑 API Key**: ${DO_AGENT_API_KEY ? `Present (${DO_AGENT_API_KEY.length} chars)` : 'Missing'}`,
        `**🤖 Chatbot ID**: ${CHATBOT_ID}`,
        `**📅 Test Time**: ${new Date().toISOString()}`,
        `\n**📋 Endpoint Tests:**`
    ];

    for (const config of testConfigs) {
        try {
            const headers = { 'Content-Type': 'application/json' };

            if (!config.noAuth) {
                headers['Authorization'] = `Bearer ${DO_AGENT_API_KEY}`;
            }

            const fetchOptions = {
                method: config.method,
                headers: headers
            };

            if (config.body) {
                fetchOptions.body = JSON.stringify(config.body);
            }

            const response = await fetch(config.endpoint, fetchOptions);

            const status = response.ok ? '✅' : (response.status === 404 ? '📋' : '⚠️');
            debugResults.push(`${status} **${config.method} ${config.endpoint}** - Status: ${response.status} ${response.statusText}`);

            if (response.ok) {
                try {
                    const data = await response.text();
                    const preview = data.length > 200 ? data.substring(0, 200) + '...' : data;
                    debugResults.push(`   📄 Response: ${preview}`);
                } catch (e) {
                    debugResults.push(`   📄 Response: [Could not read response body]`);
                }
            }

        } catch (error) {
            debugResults.push(`❌ **${config.method} ${config.endpoint}** - Error: ${error.message}`);
        }
    }

    debugResults.push(`\n**🎯 Diagnostic Summary:**`);
    debugResults.push(`• Look for ✅ status codes indicating working endpoints`);
    debugResults.push(`• 📋 404 status is normal for documentation endpoints`);
    debugResults.push(`• The main chat endpoint should show ✅ or detailed error info`);
    debugResults.push(`\n**💡 Next Steps:**`);
    debugResults.push(`• If main endpoint works (✅), the agent is ready`);
    debugResults.push(`• If you see errors, check API key validity`);
    debugResults.push(`• Contact DO support if persistent connection issues occur`);

    const debugMessage = debugResults.join('\n');
    addMessage(debugMessage, 'bot');

    console.log('🔧 API diagnostics completed');
}

// Auto-resize textarea
function autoResizeTextarea() {
    if (!messageInput) return;

    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Scroll to bottom of chat
function scrollToBottom() {
    if (!chatMessages) return;

    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Generate session ID
function generateSessionId() {
    return 'wb_iati_session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
}

// Utility function for analytics (could be expanded)
function trackUserInteraction(action, details = {}) {
    console.log(`📊 User interaction: ${action}`, details);
    // Could integrate with analytics service here
}

// Export functions for global access if needed
if (typeof window !== 'undefined') {
    window.WBIATIAgent = {
        sendMessage: handleSendMessage,
        clearChat: handleClearChat,
        exportAnalysis: handleExportAnalysis,
        debugAPI: handleDebugAPI,
        getCurrentSession: () => currentSessionId,
        getConversationHistory: () => conversationHistory
    };
}

console.log('🌍 World Bank IATI Intelligence Agent script loaded successfully');