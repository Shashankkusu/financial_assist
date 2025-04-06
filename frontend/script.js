// DOM Elements
const themeToggle = document.getElementById('themeToggle');
const stockTicker = document.getElementById('stockTicker');
const searchBtn = document.getElementById('searchBtn');
const suggestionBtns = document.querySelectorAll('.suggestion-btn');
const refreshBtn = document.getElementById('refreshOverview');
const loadingOverlay = document.getElementById('loadingOverlay');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');
const chatMessages = document.getElementById('chatMessages');
const chatTips = document.querySelectorAll('.chat-tip');

// Chart Variables
let priceChart = null;
let currentTicker = '';
let currentPeriod = '1d';

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing QuantumStocks...');
    
    try {
        // Load components
        loadAnimations();
        setupEventListeners();
        initTheme();
        
        // Load sample data if no errors
        loadSampleData();
        console.log('Initialization complete');
    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize application');
    }
});

function loadAnimations() {
    console.log('Loading animations...');
    if (document.getElementById('loadingAnimation')) {
        bodymovin.loadAnimation({
            container: document.getElementById('loadingAnimation'),
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'assets/loading-animation.json'
        });
    }
}

function setupEventListeners() {
    console.log('Setting up event listeners...');
    
    // Theme toggle
    if (themeToggle) {
        themeToggle.addEventListener('change', toggleTheme);
    }

    // Search functionality
    if (searchBtn) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            searchStock();
        });
    }
    
    if (stockTicker) {
        stockTicker.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchStock();
            }
        });
    }

    // Suggestion buttons
    if (suggestionBtns.length > 0) {
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                stockTicker.value = this.dataset.ticker;
                searchStock();
            });
        });
    }

    // Refresh button
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            searchStock();
        });
    }

    // Chat functionality
    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sendChatMessage();
        });
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Chat tips
    if (chatTips.length > 0) {
        chatTips.forEach(tip => {
            tip.addEventListener('click', function() {
                chatInput.value = this.dataset.tip;
                chatInput.focus();
            });
        });
    }

    // Chart period buttons
    document.querySelectorAll('.chart-period').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.chart-period').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.dataset.period;
            updateChartPeriod(currentPeriod);
        });
    });
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (themeToggle) {
        themeToggle.checked = savedTheme === 'dark';
    }
}

function toggleTheme() {
    const newTheme = themeToggle.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Recreate chart with new theme colors
    if (priceChart && currentTicker) {
        initChart(currentTicker, currentPeriod);
    }
}

function loadSampleData() {
    // For demo purposes, load AAPL data initially
    if (stockTicker) {
        stockTicker.value = 'AAPL';
        searchStock();
    }
}

async function searchStock() {
    const ticker = stockTicker.value.trim().toUpperCase();
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    currentTicker = ticker;
    showLoading();
    
    try {
        // Fetch all data in parallel
        const [stockData, riskData, predictionData] = await Promise.all([
            fetchData(`/stock?ticker=${ticker}`),
            fetchData(`/risk?ticker=${ticker}`),
            fetchData(`/predict?ticker=${ticker}`)
        ]);

        // Update UI with fetched data
        updateStockOverview(stockData);
        updateRiskAssessment(riskData);
        updatePrediction(predictionData);
        
        // Initialize chart
        initChart(ticker, currentPeriod);
        
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to fetch stock data');
    } finally {
        hideLoading();
    }
}

async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

function updateStockOverview(data) {
    if (!data || !data.ticker) return;
    
    document.getElementById('stockSymbol').textContent = data.ticker;
    document.getElementById('stockPrice').textContent = `$${data.price || '0.00'}`;
    
    const changeElement = document.getElementById('stockChange');
    if (changeElement) {
        const changeAmount = parseFloat(data.change || 0);
        changeElement.querySelector('.change-amount').textContent = data.change || '+0.00';
        changeElement.querySelector('.change-percent').textContent = `(${data.percent_change || '0.00%'})`;
        changeElement.className = `stock-change ${changeAmount >= 0 ? 'positive' : 'negative'}`;
    }
    
    document.getElementById('stockOpen').textContent = `$${data.open || '0.00'}`;
    document.getElementById('stockHigh').textContent = `$${data.high || '0.00'}`;
    document.getElementById('stockLow').textContent = `$${data.low || '0.00'}`;
    document.getElementById('stockVolume').textContent = formatVolume(data.volume);
    
    const now = new Date();
    document.getElementById('lastUpdated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

function formatVolume(volume) {
    if (!volume) return 'N/A';
    const num = parseInt(volume);
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toString();
}

function updateRiskAssessment(data) {
    if (!data) return;
    
    const riskLevelElement = document.getElementById('riskLevel');
    if (riskLevelElement) {
        riskLevelElement.textContent = data.risk_level || '--';
        riskLevelElement.className = `risk-level ${data.risk_level || 'medium'}`;
    }

    const riskMeterFill = document.getElementById('riskMeterFill');
    if (riskMeterFill) {
        riskMeterFill.className = 'meter-fill';
        setTimeout(() => {
            riskMeterFill.classList.add(data.risk_level || 'medium');
        }, 100);
    }

    document.getElementById('volatilityValue').textContent = data.volatility ? data.volatility.toFixed(2) : '--';
    document.getElementById('riskDescription').textContent = data.description || 'Risk data not available';
}

function updatePrediction(data) {
    if (!data) return;
    
    document.getElementById('currentPrice').textContent = `$${data.current_price || '0.00'}`;
    document.getElementById('predictedPrice').textContent = `$${data.predicted_price || '0.00'}`;
    document.getElementById('confidenceValue').textContent = `${data.confidence || '0'}%`;
    document.getElementById('predictionDate').textContent = data.prediction_date || '--';

    const trendElement = document.getElementById('predictionTrend');
    if (trendElement) {
        const trendText = trendElement.querySelector('.trend-text');
        const trendIcon = trendElement.querySelector('.trend-icon');
        
        trendIcon.querySelectorAll('i').forEach(icon => icon.style.display = 'none');
        
        if (data.trend === 'upward') {
            trendText.textContent = 'Bullish trend predicted';
            trendIcon.querySelector('.trend-up').style.display = 'block';
        } else if (data.trend === 'downward') {
            trendText.textContent = 'Bearish trend predicted';
            trendIcon.querySelector('.trend-down').style.display = 'block';
        } else {
            trendText.textContent = 'Neutral trend predicted';
            trendIcon.querySelector('.trend-neutral').style.display = 'block';
        }
    }
}

async function initChart(ticker, period) {
    if (!ticker) return;
    
    showLoading();
    try {
        const data = await fetchData(`/stock_graph?ticker=${ticker}&period=${period}`);
        renderChart(data, ticker, period);
    } catch (error) {
        console.error('Chart error:', error);
        showError('Failed to load chart data');
    } finally {
        hideLoading();
    }
}

function renderChart(data, ticker, period) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';

    // Prepare labels based on period
    const labels = data.data.map(item => {
        const date = new Date(item.time);

        const options = {
            timeZone: 'America/New_York',
            hour: '2-digit',
            minute: '2-digit',
            month: 'short',
            day: 'numeric'
        };

        if (period === '1d') {
            return date.toLocaleString('en-US', {
                ...options,
                month: undefined,
                day: undefined
            });
        } else if (period === '7d') {
            return date.toLocaleString('en-US', {
                ...options,
                hour: '2-digit'
            });
        } else {
            return date.toLocaleString('en-US', {
                ...options,
                hour: undefined,
                minute: undefined
            });
        }
    });

    // Destroy previous chart if exists
    if (priceChart) {
        priceChart.destroy();
    }

    // Create new chart
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${ticker} Price`,
                data: data.data.map(item => item.price),
                borderColor: '#ffffff', // White color for the line
                backgroundColor: 'rgba(255, 255, 255, 0.1)', // White with slight transparency
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true, // Display legend
                    labels: {
                        color: '#ffffff', // White color for legend labels
                        generateLabels: function(chart) {
                            const original = Chart.defaults.plugins.legend.labels.generateLabels.apply(this, [chart]);
                            if (period === '1d') {
                                const now = new Date();
                                const nyTime = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
                                const nyHour = nyTime.getHours();
                                const nyDay = nyTime.getDay(); // 0 (Sunday) to 6 (Saturday)

                                if (nyDay === 0 || nyDay === 6) { // Sunday or Saturday
                                    original[0].text += " (Weekend - Yesterday's Data)";
                                } else if (nyHour < 9) {
                                    original[0].text += " (Market Not Opened Yet - Yesterday's Data)";
                                } else if (nyHour >= 16) {
                                    original[0].text += " (Market Closed - Yesterday's Data)";
                                }
                            }
                            return original;
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(30, 39, 46, 0.9)', // Dark background for tooltip
                    titleColor: '#ffffff', // White color for tooltip title
                    bodyColor: '#ffffff', // White color for tooltip body
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: context => `Price: $${context.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: {
                        color: '#ffffff', // White color for x-axis ticks
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#ffffff', // White color for y-axis ticks
                        callback: value => '$' + value
                    }
                }
            },
            interaction: { mode: 'nearest', axis: 'x', intersect: false }
        }
    });
}

async function updateChartPeriod(period) {
    if (!currentTicker) return;
    await initChart(currentTicker, period);
}

async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';
    
    // Show loading state
    const loadingId = 'loading-' + Date.now();
    const loadingMessage = `
        <div class="message bot-message" id="${loadingId}">
            <div class="message-content">
                <i class="fas fa-circle-notch fa-spin"></i> Analyzing your question...
            </div>
        </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', loadingMessage);
    scrollChatToBottom();
    
    try {
        // Send to chatbot API
        const response = await fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query: message,
                ticker: currentTicker // Include current ticker if available
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();
        
        // Add bot response
        if (data.status === 'success') {
            if (data.is_stock_response) {
                // Format stock insights response
                const insightsHTML = `
                    <div class="message bot-message stock-insights">
                        <div class="message-header">
                            <span class="stock-ticker">${data.ticker}</span>
                            <span class="company-name">${data.company_name || data.ticker}</span>
                        </div>
                        <div class="message-content">
                            <h4>Key Insights:</h4>
                            <ol class="insights-list">
                                ${data.insights.map(insight => `<li>${insight}</li>`).join('')}
                            </ol>
                        </div>
                        <div class="message-timestamp">Just now</div>
                    </div>
                `;
                chatMessages.insertAdjacentHTML('beforeend', insightsHTML);
            } else {
                // Regular financial response
                addChatMessage(data.response, 'bot');
            }
        } else {
            addChatMessage("Sorry, I couldn't process your request. Please try again.", 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();
        addChatMessage("Sorry, I'm having trouble connecting. Please try again later.", 'bot');
    }
    scrollChatToBottom();
}

function addChatMessage(text, sender) {
    const messageHTML = `
        <div class="message ${sender}-message">
            <div class="message-content">
                ${text}
                <div class="message-timestamp">Just now</div>
            </div>
        </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', messageHTML);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoading() {
    if (loadingOverlay) loadingOverlay.classList.add('active');
}

function hideLoading() {
    if (loadingOverlay) loadingOverlay.classList.remove('active');
}

function showError(message) {
    let errorElement = document.getElementById('errorNotification');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'errorNotification';
        errorElement.className = 'error-notification';
        document.body.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    errorElement.classList.add('show');
    
    setTimeout(() => {
        errorElement.classList.remove('show');
    }, 5000);
}
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
    
    setTimeout(() => {
        errorContainer.innerHTML = '';
    }, 5000);
}
// Utility function to handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    showError('Service temporarily unavailable. Please try again later.');
    return { error: error.message };
}


