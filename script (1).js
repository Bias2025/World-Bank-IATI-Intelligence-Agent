// =========================================================
// World Bank IATI Intelligence Agent — Lightweight UI
// Dashboard + Chat (KB-first, placeholder fallback)
// Renders formatted text in the UI (no JSON UI contract required).
// =========================================================

// Global variables (fill in your DO values)
const DO_AGENT_ENDPOINT = 'hxxxxx';
const DO_AGENT_API_KEY = 'xxxxx';
const AGENT_ID = 'xxxx'; // reserved if you use it in your DO deployment

let currentSessionId = generateSessionId();
let isProcessing = false;
let dashboardProcessing = false;

// DOM elements (Chat)
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

// DOM elements (Dashboard)
const countryFilter = document.getElementById('countryFilter');
const yearFilter = document.getElementById('yearFilter');
const sectorFilter = document.getElementById('sectorFilter');
const refreshDashboardBtn = document.getElementById('refreshDashboardBtn');
const demoBanner = document.getElementById('demoBanner');
const dataModeBadge = document.getElementById('dataModeBadge');
const dashboardNarrative = document.getElementById('dashboardNarrative');
const copyDashboardBriefBtn = document.getElementById('copyDashboardBriefBtn');

// KPI elements
const kpiCommitments = document.getElementById('kpiCommitments');
const kpiDisbursements = document.getElementById('kpiDisbursements');
const kpiProjects = document.getElementById('kpiProjects');
const kpiRatio = document.getElementById('kpiRatio');
const kpiCommitmentsFoot = document.getElementById('kpiCommitmentsFoot');
const kpiDisbursementsFoot = document.getElementById('kpiDisbursementsFoot');
const kpiProjectsFoot = document.getElementById('kpiProjectsFoot');
const kpiRatioFoot = document.getElementById('kpiRatioFoot');

// Chart titles
const chartTitleTrend = document.getElementById('chartTitleTrend');
const chartTitleSectors = document.getElementById('chartTitleSectors');
const chartTitleTop = document.getElementById('chartTitleTop');
const chartTitleMix = document.getElementById('chartTitleMix');

// Chart instances
let trendChart, sectorChart, topChart, mixChart;

// Standard prompts mapping (World Bank IATI)
const STANDARD_PROMPTS = {
  portfolio_snapshot:
    "Using the World Bank IATI knowledge base, provide a portfolio snapshot for the current filter context. Format as: 6-10 bullets, then a short 'Evidence' list with IATI activity identifiers/titles, then a 3-bullet 'So what'.",

  top_sectors:
    "For the current filter context, summarize top sectors by commitments and disbursements, highlight the biggest shifts over time, and include 5-8 evidence items (IATI identifiers/titles).",

  top_projects:
    "List the top projects by disbursement for the current filter context. For each: title, IATI identifier, commitment, disbursement, and one sentence on results/outcomes if present in KB. Finish with a short narrative summary.",

  outcomes_evidence:
    "Identify projects with the strongest outcome/results evidence for the current filter context. Provide a ranked list with a one-line outcome statement each, and cite IATI identifiers/titles.",

  implementation_flags:
    "Flag implementation risks for the current filter context (e.g., low disbursement ratio, long gaps, cancellations, delays). Provide actionable mitigations and cite IATI identifiers/titles.",

  data_quality:
    "Assess data quality for the current filter context: missing dates, mismatched totals, unusual values, gaps, or inconsistent sector tagging. Provide practical remediation steps.",

  exec_brief:
    "Write a one-page executive brief for the current filter context: headline, 6 bullets, 3 risks, 3 opportunities, and an evidence appendix (IATI identifiers/titles). Make it copy-ready.",
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
  initializeEventListeners();
  updateCharCount();
  initializeWelcomeMessage();
  checkAgentConnection();
  initializeCharts();

  // Load an initial dashboard with placeholders so the page doesn't look empty
  applyDemoMode(true, 'Waiting for KB dashboard refresh');
  const initial = generatePlaceholderDashboard(getDashboardContext());
  renderDashboard(initial, { demo: true, reason: 'Initial placeholder' });
});

function initializeEventListeners() {
  // Chat input events
  messageInput.addEventListener('input', handleInputChange);
  messageInput.addEventListener('keypress', handleKeyPress);

  // Chat buttons
  sendBtn.addEventListener('click', handleSendMessage);
  clearBtn.addEventListener('click', handleClearChat);
  exportBtn.addEventListener('click', handleExportChat);
  debugBtn.addEventListener('click', handleDebugAPI);

  // Prompt dropdown events
  standardPrompts.addEventListener('change', handlePromptSelection);
  usePromptBtn.addEventListener('click', handleUsePrompt);

  // Auto-resize textarea
  messageInput.addEventListener('input', autoResizeTextarea);

  // Dashboard
  refreshDashboardBtn.addEventListener('click', handleRefreshDashboard);
  [countryFilter, yearFilter, sectorFilter].forEach((el) => {
    el.addEventListener('change', () => {
      // optional auto-refresh behavior: keep manual for control
      // handleRefreshDashboard();
    });
  });

  copyDashboardBriefBtn.addEventListener('click', copyDashboardBrief);
}

// -----------------------------
// Dashboard
// -----------------------------

function getDashboardContext() {
  return {
    country: countryFilter?.value || 'GLOBAL',
    years: yearFilter?.value || '2021-2024',
    sector: sectorFilter?.value || 'ALL',
  };
}

function contextToLabel(ctx) {
  const country = ctx.country === 'GLOBAL' ? 'Global' : ctx.country;
  const sector = ctx.sector === 'ALL' ? 'All sectors' : ctx.sector;
  return `${country} · ${ctx.years} · ${sector}`;
}

function dashboardPrompt(ctx) {
  // IMPORTANT: The UI renders formatted text, not JSON.
  // We ask the agent for a human-readable narrative AND a tiny data block that is NOT JSON.
  // The data block is easy to parse (pipe tables) and still readable.
  return (
    `You are the World Bank IATI Intelligence Agent. Use ONLY the World Bank IATI knowledge base available to you.\n\n` +
    `Dashboard context: Country=${ctx.country}, Years=${ctx.years}, Sector=${ctx.sector}.\n\n` +
    `Task: Produce (1) a short executive narrative that explains the portfolio and what the charts imply, and (2) a small, readable data appendix the UI can parse.\n\n` +
    `Formatting requirements (STRICT):\n` +
    `A) Start with: ## Dashboard Narrative\n` +
    `- 6–10 bullets\n` +
    `- then: ## Evidence (IATI) with 5–12 items (identifier + title)\n` +
    `- then: ## Caveats (1–3 bullets)\n\n` +
    `B) Then include a readable appendix with FOUR markdown tables EXACTLY in this order, using | pipes and a header row: \n` +
    `### KPI\n| metric | value | note |\n` +
    `### Trend\n| period | commitments | disbursements |\n` +
    `### Sectors\n| sector | amount |\n` +
    `### Mix\n| category | amount |\n\n` +
    `Notes: Use numbers as plain decimals (no commas). Use USD amounts. Keep periods like 2021-Q1, 2021-Q2, etc.\n` +
    `If the KB does not contain enough data for any table, write 'NA' for the value(s) in that table, but still include the table.\n`
  );
}

async function handleRefreshDashboard() {
  if (dashboardProcessing) return;

  const ctx = getDashboardContext();
  setDashboardProcessing(true);

  // UI: show that we're attempting KB
  applyDemoMode(false);
  dashboardNarrative.innerHTML = '<div class="notes-placeholder">Refreshing dashboard from the KB…</div>';

  try {
    const response = await callAgentAPI(dashboardPrompt(ctx));

    if (!response.success) {
      throw new Error(response.error || 'Dashboard request failed');
    }

    // We still render the narrative as formatted text
    const rawText = response.data;
    dashboardNarrative.innerHTML = formatMessage(rawText);

    // Parse tables for charts; if parsing fails or tables contain NA -> fallback
    const parsed = parseDashboardTables(rawText);

    const shouldFallback = !parsed.ok || parsed.hasNA;
    if (shouldFallback) {
      const placeholder = generatePlaceholderDashboard(ctx);
      renderDashboard(placeholder, { demo: true, reason: parsed.reason || 'KB missingness' });
      // keep narrative from KB (useful), but label demo mode
      applyDemoMode(true, parsed.reason || 'KB did not return enough metrics');
    } else {
      renderDashboard(parsed.data, { demo: false });
      applyDemoMode(false);
    }

  } catch (err) {
    console.error('Dashboard refresh error:', err);
    const placeholder = generatePlaceholderDashboard(ctx);
    renderDashboard(placeholder, { demo: true, reason: 'Error fetching KB dashboard' });
    applyDemoMode(true, 'Error fetching KB dashboard');
    dashboardNarrative.innerHTML = formatMessage(
      `## Dashboard Narrative\n- Unable to fetch KB dashboard data right now.\n\n## Caveats\n- Using demo data for charts.\n- Check agent endpoint/key and try again.\n`
    );
  } finally {
    setDashboardProcessing(false);
  }
}

function setDashboardProcessing(processing) {
  dashboardProcessing = processing;
  refreshDashboardBtn.disabled = processing;
}

function applyDemoMode(isDemo, reason = '') {
  if (isDemo) {
    demoBanner.hidden = false;
    dataModeBadge.innerHTML = '<i class="fas fa-flask"></i> Demo Data';
  } else {
    demoBanner.hidden = true;
    dataModeBadge.innerHTML = '<i class="fas fa-check-circle"></i> KB Data';
  }

  if (reason && demoBanner && !demoBanner.hidden) {
    // keep existing banner text but it’s fine to be subtle
    // (we don’t mutate innerHTML to avoid losing structure)
  }

  // Chart titles should clearly indicate demo mode
  const suffix = isDemo ? ' — DEMO' : '';
  chartTitleTrend.textContent = `Commitments vs Disbursements (Trend)${suffix}`;
  chartTitleSectors.textContent = `Top Sectors${suffix}`;
  chartTitleTop.textContent = `Top Recipients / Projects${suffix}`;
  chartTitleMix.textContent = `Funding Mix${suffix}`;
}

function initializeCharts() {
  // Create empty charts; data is injected later.
  const trendCtx = document.getElementById('trendChart');
  const sectorCtx = document.getElementById('sectorChart');
  const topCtx = document.getElementById('topChart');
  const mixCtx = document.getElementById('mixChart');

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true },
      tooltip: { enabled: true },
    },
    scales: {
      x: { grid: { display: false } },
      y: { ticks: { callback: (v) => v }, grid: { color: 'rgba(2,6,23,0.06)' } },
    },
  };

  trendChart = new Chart(trendCtx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Commitments', data: [] }, { label: 'Disbursements', data: [] }] },
    options: baseOptions,
  });

  sectorChart = new Chart(sectorCtx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'Amount', data: [] }] },
    options: baseOptions,
  });

  topChart = new Chart(topCtx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'Amount', data: [] }] },
    options: baseOptions,
  });

  mixChart = new Chart(mixCtx, {
    type: 'doughnut',
    data: { labels: [], datasets: [{ label: 'Amount', data: [] }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true }, tooltip: { enabled: true } },
    },
  });
}

function renderDashboard(d, meta = { demo: false }) {
  const ctx = getDashboardContext();
  const label = contextToLabel(ctx);

  // KPIs
  kpiCommitments.textContent = formatCurrency(d.kpi.commitments);
  kpiDisbursements.textContent = formatCurrency(d.kpi.disbursements);
  kpiProjects.textContent = String(d.kpi.projects);
  kpiRatio.textContent = `${Math.round(d.kpi.disbursement_ratio * 100)}%`;

  kpiCommitmentsFoot.textContent = label;
  kpiDisbursementsFoot.textContent = label;
  kpiProjectsFoot.textContent = meta.demo ? 'Demo estimate' : 'KB-derived';
  kpiRatioFoot.textContent = meta.demo ? 'Demo estimate' : 'KB-derived';

  // Trend chart
  trendChart.data.labels = d.trend.map((p) => p.period);
  trendChart.data.datasets[0].data = d.trend.map((p) => p.commitments);
  trendChart.data.datasets[1].data = d.trend.map((p) => p.disbursements);
  trendChart.update();

  // Sectors
  sectorChart.data.labels = d.sectors.map((s) => s.name);
  sectorChart.data.datasets[0].data = d.sectors.map((s) => s.amount);
  sectorChart.update();

  // Top
  topChart.data.labels = d.top.map((t) => t.name);
  topChart.data.datasets[0].data = d.top.map((t) => t.amount);
  topChart.update();

  // Mix
  mixChart.data.labels = d.mix.map((m) => m.name);
  mixChart.data.datasets[0].data = d.mix.map((m) => m.amount);
  mixChart.update();
}

function parseDashboardTables(text) {
  // Parses the four required markdown tables (KPI, Trend, Sectors, Mix)
  // and returns chart-ready arrays.
  try {
    const getSection = (heading) => {
      const idx = text.indexOf(heading);
      if (idx === -1) return '';
      const rest = text.substring(idx);
      // stop at next ### or end
      const next = rest.substring(heading.length).search(/\n###\s+/);
      return next === -1 ? rest : rest.substring(0, heading.length + next);
    };

    const kpiSec = getSection('### KPI');
    const trendSec = getSection('### Trend');
    const sectorsSec = getSection('### Sectors');
    const mixSec = getSection('### Mix');

    if (!kpiSec || !trendSec || !sectorsSec || !mixSec) {
      return { ok: false, hasNA: true, reason: 'Missing required markdown tables' };
    }

    const parseTableRows = (sec) => {
      const lines = sec.split('\n').map((l) => l.trim()).filter(Boolean);
      const rows = lines.filter((l) => l.startsWith('|') && l.endsWith('|'));
      // remove header + separator
      const body = rows.slice(2);
      return body.map((r) => r.split('|').map((c) => c.trim()).filter((c) => c.length > 0));
    };

    const kpiRows = parseTableRows(kpiSec);
    const trendRows = parseTableRows(trendSec);
    const sectorRows = parseTableRows(sectorsSec);
    const mixRows = parseTableRows(mixSec);

    const hasNA = [kpiRows, trendRows, sectorRows, mixRows].some((tbl) =>
      tbl.some((row) => row.some((cell) => String(cell).toUpperCase() === 'NA'))
    );

    // KPI map
    const kpiMap = {};
    kpiRows.forEach(([metric, value]) => {
      kpiMap[String(metric || '').toLowerCase()] = value;
    });

    const commitments = toNumber(kpiMap['total commitments'] || kpiMap['commitments'] || kpiMap['total_commitments']);
    const disbursements = toNumber(kpiMap['total disbursements'] || kpiMap['disbursements'] || kpiMap['total_disbursements']);
    const projects = toNumber(kpiMap['projects'] || kpiMap['project count'] || kpiMap['count']);

    // Trend
    const trend = trendRows
      .filter((r) => r.length >= 3)
      .map(([period, c, d]) => ({ period, commitments: toNumber(c), disbursements: toNumber(d) }))
      .filter((p) => p.period);

    // Sectors
    const sectors = sectorRows
      .filter((r) => r.length >= 2)
      .map(([name, amount]) => ({ name, amount: toNumber(amount) }))
      .filter((s) => s.name);

    // Mix
    const mix = mixRows
      .filter((r) => r.length >= 2)
      .map(([name, amount]) => ({ name, amount: toNumber(amount) }))
      .filter((m) => m.name);

    const ok =
      isFinite(commitments) &&
      isFinite(disbursements) &&
      isFinite(projects) &&
      trend.length >= 4 &&
      sectors.length >= 3 &&
      mix.length >= 3;

    if (!ok) {
      return { ok: false, hasNA: true, reason: 'Tables parsed but metrics are incomplete' };
    }

    const ratio = commitments > 0 ? disbursements / commitments : 0;

    return {
      ok: true,
      hasNA,
      data: {
        kpi: {
          commitments,
          disbursements,
          projects: Math.round(projects),
          disbursement_ratio: ratio,
        },
        trend: trend.map((p) => ({ period: p.period, commitments: p.commitments, disbursements: p.disbursements })),
        sectors,
        top: deriveTopFromSectors(sectors),
        mix,
      },
    };

  } catch (e) {
    return { ok: false, hasNA: true, reason: `Parsing error: ${e.message}` };
  }
}

function deriveTopFromSectors(sectors) {
  // If KB doesn't provide explicit top recipients/projects in the appendix,
  // we reuse sector values for a "Top" chart so the UI remains populated.
  // In a later iteration, add a separate "### Top" table.
  return sectors
    .slice(0, 6)
    .map((s, idx) => ({ name: s.name.length > 22 ? s.name.slice(0, 22) + '…' : s.name, amount: s.amount * (0.6 + idx * 0.05) }));
}

function generatePlaceholderDashboard(ctx) {
  // Generates coherent placeholder data using a seeded-ish approach so it feels stable.
  const seed = `${ctx.country}|${ctx.years}|${ctx.sector}`;
  const n = pseudoHash(seed);

  const baseC = 90000000 + (n % 70000000); // 90–160M
  const baseD = baseC * (0.35 + ((n % 30) / 100));
  const projects = 12 + (n % 38);

  const periods = ['2023-Q1', '2023-Q2', '2023-Q3', '2023-Q4', '2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4'];
  const trend = periods.map((p, i) => {
    const wave = Math.sin((i + 1) * 0.9) * 0.08;
    const commitments = Math.max(0, (baseC / periods.length) * (1 + wave));
    const disbursements = Math.max(0, (baseD / periods.length) * (1 + wave * 0.6));
    return { period: p, commitments: round2(commitments), disbursements: round2(disbursements) };
  });

  const sectorNames = ctx.sector !== 'ALL'
    ? [ctx.sector, 'Public Administration', 'Health', 'Education', 'Transport', 'Water']
    : ['Public Administration', 'Transport', 'Health', 'Education', 'Energy', 'Water'];

  const sectors = sectorNames.map((name, i) => {
    const amt = baseD * (0.26 - i * 0.03) + (n % 7000000);
    return { name, amount: round2(Math.max(0, amt)) };
  });

  const top = [
    { name: 'Project A', amount: round2(baseD * 0.18) },
    { name: 'Project B', amount: round2(baseD * 0.14) },
    { name: 'Project C', amount: round2(baseD * 0.11) },
    { name: 'Project D', amount: round2(baseD * 0.09) },
    { name: 'Project E', amount: round2(baseD * 0.07) },
  ];

  const mix = [
    { name: 'Investment', amount: round2(baseD * 0.48) },
    { name: 'Technical Assistance', amount: round2(baseD * 0.22) },
    { name: 'Policy / Reform', amount: round2(baseD * 0.18) },
    { name: 'Other', amount: round2(baseD * 0.12) },
  ];

  return {
    kpi: {
      commitments: round2(baseC),
      disbursements: round2(baseD),
      projects,
      disbursement_ratio: baseC > 0 ? baseD / baseC : 0,
    },
    trend,
    sectors,
    top,
    mix,
  };
}

function copyDashboardBrief() {
  const text = dashboardNarrative?.innerText || '';
  if (!text.trim()) return;
  navigator.clipboard.writeText(text).then(() => {
    addMessage('✅ Dashboard narrative copied to clipboard.', 'bot');
  }).catch(() => {
    addMessage('⚠️ Could not copy. Your browser may block clipboard access.', 'bot', true);
  });
}

// -----------------------------
// Chat (mostly preserved)
// -----------------------------

function handleInputChange() {
  updateCharCount();
  updateSendButton();
}

function handleKeyPress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isProcessing && messageInput.value.trim()) {
      handleSendMessage();
    }
  }
}

function updateCharCount() {
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

function updateSendButton() {
  const hasText = messageInput.value.trim().length > 0;
  sendBtn.disabled = !hasText || isProcessing;
}

function handlePromptSelection() {
  const selectedValue = standardPrompts.value;
  usePromptBtn.disabled = !selectedValue || isProcessing;
}

function handleUsePrompt() {
  const selectedValue = standardPrompts.value;
  if (selectedValue && STANDARD_PROMPTS[selectedValue]) {
    const ctx = getDashboardContext();
    const contextPrefix = `Context: Country=${ctx.country}, Years=${ctx.years}, Sector=${ctx.sector}.\n\n`;
    messageInput.value = contextPrefix + STANDARD_PROMPTS[selectedValue];

    standardPrompts.value = '';
    usePromptBtn.disabled = true;
    updateCharCount();
    updateSendButton();
    messageInput.focus();
  }
}

async function handleSendMessage() {
  const message = messageInput.value.trim();
  if (!message || isProcessing) return;

  addMessage(message, 'user');

  messageInput.value = '';
  updateCharCount();
  updateSendButton();

  setProcessingState(true);

  const thinkingMessage = addThinkingMessage();

  try {
    const response = await callAgentAPI(message);

    removeMessage(thinkingMessage);

    if (response.success) {
      addMessage(response.data, 'bot');
      updateConnectionStatus('connected');
    } else {
      addMessage(`I ran into an error: ${response.error}. Please try again.`, 'bot', true);
      updateConnectionStatus('error');
    }

  } catch (error) {
    removeMessage(thinkingMessage);
    addMessage(`I'm having trouble connecting right now. Please check your connection and try again.`, 'bot', true);
    updateConnectionStatus('error');
    console.error('Chat error:', error);
  } finally {
    setProcessingState(false);
    scrollToBottom();
    messageInput.focus();
  }
}

// Call DO Agent API
async function callAgentAPI(message) {
  try {
    updateConnectionStatus('connecting');

    const endpoint = `${DO_AGENT_ENDPOINT}/api/v1/chat/completions`;

    const requestBody = {
      messages: [
        {
          role: 'user',
          content: message,
        },
      ],
      stream: false,
      include_functions_info: true,
      include_retrieval_info: true,
      include_guardrails_info: true,
    };

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${DO_AGENT_API_KEY}`,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${response.statusText}\nDetails: ${errorText}`);
    }

    const data = await response.json();

    let responseText = '';

    if (data.choices && data.choices[0] && data.choices[0].message) {
      const msg = data.choices[0].message;
      if (msg.content && msg.content.trim()) {
        responseText = msg.content;
      } else if (msg.reasoning_content && msg.reasoning_content.trim()) {
        responseText = msg.reasoning_content;
      }
    } else if (data.message) {
      responseText = data.message;
    } else if (data.content) {
      responseText = data.content;
    } else if (data.response) {
      responseText = data.response;
    } else if (typeof data === 'string') {
      responseText = data;
    } else if (data.retrieval && data.retrieval.retrieved_data && data.retrieval.retrieved_data.length > 0) {
      responseText = formatRetrievalFallback(data.retrieval.retrieved_data);
    } else {
      responseText =
        'The agent responded, but the format was unexpected. If this persists, try the Test API button for diagnostics.';
    }

    if (data.guardrails && data.guardrails.triggered_guardrails && data.guardrails.triggered_guardrails.length > 0) {
      responseText += '\n\n**Content Moderation Notes:**\n';
      data.guardrails.triggered_guardrails.forEach((g) => {
        responseText += `- ${g.rule_name}: ${g.message}\n`;
      });
    }

    return { success: true, data: responseText };

  } catch (error) {
    console.error('Agent API call failed:', error);
    return {
      success: false,
      error: `API connection failed: ${error.message}\n\nPlease check:\n1. Agent endpoint: ${DO_AGENT_ENDPOINT}\n2. API key is valid\n3. Agent is running\n\nTry the "Test API" button for detailed diagnostics.`,
    };
  }
}

function formatRetrievalFallback(retrieved) {
  // Keep it simple: a brief list of sources.
  let out = '**Retrieved context from KB:**\n\n';
  retrieved.slice(0, 8).forEach((item, idx) => {
    const fn = item.filename || item.source || 'KB item';
    const score = typeof item.score === 'number' ? item.score.toFixed(1) : '—';
    const preview = (item.page_content || '').toString().trim().slice(0, 220);
    out += `${idx + 1}. **${fn}** (relevance: ${score})\n   - ${preview}${preview.length >= 220 ? '…' : ''}\n`;
  });
  out += '\nIf you want, ask a specific question about these retrieved items.';
  return out;
}

function addMessage(text, type, isError = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message${isError ? ' error-message' : ''}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

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

function addThinkingMessage() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message bot-message thinking';

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerHTML = '<i class="fas fa-robot"></i>';

  const content = document.createElement('div');
  content.className = 'message-content';

  const thinkingIndicator = document.createElement('div');
  thinkingIndicator.className = 'thinking-indicator';
  thinkingIndicator.innerHTML = `
      AI Agent is analyzing...
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

function removeMessage(messageElement) {
  if (messageElement && messageElement.parentNode) {
    messageElement.parentNode.removeChild(messageElement);
  }
}

function formatMessage(text) {
  // Convert markdown-like formatting to HTML (simple + safe-ish)
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^###\s+(.*$)/gim, '<h4>$1</h4>')
    .replace(/^##\s+(.*$)/gim, '<h3>$1</h3>')
    .replace(/^#\s+(.*$)/gim, '<h2>$1</h2>')
    .replace(/^\d+\.\s+(.*$)/gim, '<div class="numbered-item">$1</div>')
    .replace(/^\-\s+(.*$)/gim, '<div class="bullet-item">• $1</div>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

function handleClearChat() {
  if (confirm('Are you sure you want to clear the chat history?')) {
    chatMessages.innerHTML = '';
    initializeWelcomeMessage();
    currentSessionId = generateSessionId();
  }
}

function handleExportChat() {
  const messages = Array.from(chatMessages.querySelectorAll('.message:not(.thinking)'));
  let exportText = `World Bank IATI Intelligence Chat Export\n`;
  exportText += `Generated: ${new Date().toLocaleString()}\n`;
  exportText += `Session ID: ${currentSessionId}\n`;
  exportText += `\n${'='.repeat(50)}\n\n`;

  messages.forEach((message) => {
    const isUser = message.classList.contains('user-message');
    const messageText = message.querySelector('.message-text').textContent;
    const messageTime = message.querySelector('.message-time').textContent;

    exportText += `[${messageTime}] ${isUser ? 'User' : 'AI Agent'}:\n`;
    exportText += `${messageText}\n\n`;
  });

  const blob = new Blob([exportText], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `iati-chat-${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

function initializeWelcomeMessage() {
  const welcomeText = `Hello! I’m the <strong>World Bank IATI Intelligence Agent</strong>. I help you analyze and explain development finance using the IATI registry data and our knowledge base.

<strong>What I can do:</strong>
- Summarize portfolios (commitments, disbursements, trends)
- Highlight project effectiveness and outcomes (when evidence exists)
- Surface risks (low disbursement, delays, anomalies)
- Provide citations (IATI identifiers / project titles)

Tip: Use the <strong>Portfolio Dashboard</strong> above for charts, then ask follow-up questions here for deeper explanation.`;

  addMessage(welcomeText, 'bot');
}

function setProcessingState(processing) {
  isProcessing = processing;
  loadingOverlay.style.display = processing ? 'flex' : 'none';
  sendBtn.disabled = processing || !messageInput.value.trim();
  usePromptBtn.disabled = processing || !standardPrompts.value;
  messageInput.disabled = processing;
  standardPrompts.disabled = processing;

  if (processing) updateConnectionStatus('connecting');
}

function updateConnectionStatus(status) {
  statusDot.className = `status-dot ${status}`;

  switch (status) {
    case 'connected':
      statusText.textContent = 'Connected to AI Agent';
      break;
    case 'connecting':
      statusText.textContent = 'Connecting to AI Agent...';
      break;
    case 'error':
      statusText.textContent = 'Connection Error';
      break;
    default:
      statusText.textContent = 'AI Agent Status Unknown';
  }
}

async function checkAgentConnection() {
  try {
    updateConnectionStatus('connecting');

    const healthEndpoints = [
      `${DO_AGENT_ENDPOINT}/health`,
      `${DO_AGENT_ENDPOINT}/api/health`,
      `${DO_AGENT_ENDPOINT}/status`,
      `${DO_AGENT_ENDPOINT}/ping`,
      `${DO_AGENT_ENDPOINT}/`,
    ];

    let connected = false;

    for (const endpoint of healthEndpoints) {
      try {
        const response = await fetch(endpoint, {
          method: 'GET',
          headers: { Authorization: `Bearer ${DO_AGENT_API_KEY}` },
        });
        if (response.ok) {
          connected = true;
          break;
        }
      } catch (err) {
        continue;
      }
    }

    updateConnectionStatus(connected ? 'connected' : 'error');
  } catch (error) {
    updateConnectionStatus('error');
  }
}

function autoResizeTextarea() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

function scrollToBottom() {
  setTimeout(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }, 60);
}

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11);
}

function getCurrentTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function handleDebugAPI() {
  addMessage('🔧 **Testing DO Agent API**\n\nUsing DigitalOcean agent endpoint...', 'bot');

  const testConfigs = [
    {
      method: 'POST',
      endpoint: `${DO_AGENT_ENDPOINT}/api/v1/chat/completions`,
      body: {
        messages: [{ role: 'user', content: 'Hello! This is a test message to verify the API connection.' }],
        stream: false,
        include_functions_info: true,
        include_retrieval_info: true,
        include_guardrails_info: true,
      },
    },
    { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/docs`, body: null },
    { method: 'GET', endpoint: `${DO_AGENT_ENDPOINT}/openapi.json`, body: null },
  ];

  const results = [];

  for (const cfg of testConfigs) {
    try {
      const headers = { 'Content-Type': 'application/json' };
      headers['Authorization'] = `Bearer ${DO_AGENT_API_KEY}`;

      const opts = { method: cfg.method, headers };
      if (cfg.body) opts.body = JSON.stringify(cfg.body);

      const r = await fetch(cfg.endpoint, opts);
      results.push(`${r.ok ? '✅' : '⚠️'} **${cfg.method} ${cfg.endpoint}** — ${r.status} ${r.statusText}`);

      if (r.status !== 404) {
        const txt = await r.text();
        results.push(`   📋 Preview: ${txt.substring(0, 180)}${txt.length > 180 ? '…' : ''}`);
      }
    } catch (e) {
      results.push(`❌ **${cfg.method} ${cfg.endpoint}** — Error: ${e.message}`);
    }
  }

  addMessage(`🔍 **Debug Results**\n\n${results.join('\n')}\n\nIf you see 200/401/403 on the POST, your endpoint exists (auth may be the issue).`, 'bot');
}

// -----------------------------
// Helpers
// -----------------------------

function toNumber(x) {
  if (x === null || x === undefined) return NaN;
  const s = String(x).trim();
  if (!s) return NaN;
  const v = Number(s);
  return Number.isFinite(v) ? v : NaN;
}

function formatCurrency(n) {
  if (!Number.isFinite(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${(n / 1e3).toFixed(2)}K`;
  return `$${n.toFixed(0)}`;
}

function round2(x) {
  return Math.round(x * 100) / 100;
}

function pseudoHash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

// Export for global access
window.handleSendMessage = handleSendMessage;
window.handleClearChat = handleClearChat;
window.handleExportChat = handleExportChat;
window.handleDebugAPI = handleDebugAPI;
