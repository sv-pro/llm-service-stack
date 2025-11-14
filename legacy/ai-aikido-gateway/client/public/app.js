/**
 * AI Aikido Gateway - Reference Client
 * Simple client to test the gateway functionality
 */

const GATEWAY_URL = 'http://localhost:8000';

// Check gateway health on load
window.addEventListener('load', () => {
    checkHealth();
    loadModels();

    // Allow Enter key to send (with Shift+Enter for newlines)
    document.getElementById('message-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

/**
 * Load models from the gateway
 */
async function loadModels() {
    const modelSelect = document.getElementById('model-select');
    const supportedOnlyCheckbox = document.getElementById('supported-only');
    const supportedOnly = supportedOnlyCheckbox.checked;

    try {
        // Fetch models from the API
        const url = `${GATEWAY_URL}/v1/models${supportedOnly ? '?available_only=true' : ''}`;
        const response = await fetch(url);
        const data = await response.json();

        // Clear existing options
        modelSelect.innerHTML = '';

        if (!data.data || data.data.length === 0) {
            modelSelect.innerHTML = '<option value="">No models available</option>';
            return;
        }

        // Sort models: available first, then by provider
        const models = data.data.sort((a, b) => {
            if (a.available && !b.available) return -1;
            if (!a.available && b.available) return 1;
            return a.provider.localeCompare(b.provider);
        });

        // Populate dropdown with models
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;

            // Format the label
            let label = model.name;
            if (!model.available) {
                label += ' (Not Available)';
                option.disabled = true;
            }

            option.textContent = label;
            option.title = model.description + (model.unavailable_reason ? ` - ${model.unavailable_reason}` : '');

            modelSelect.appendChild(option);
        });

        console.log(`Loaded ${models.length} models (supported only: ${supportedOnly})`);

    } catch (error) {
        console.error('Error loading models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
    }
}

/**
 * Check gateway health status
 */
async function checkHealth() {
    const statusEl = document.getElementById('gateway-status');
    const indicatorEl = document.getElementById('connection-status');
    
    try {
        statusEl.textContent = 'Checking...';
        indicatorEl.style.color = '#ffc107'; // yellow
        
        const response = await fetch(`${GATEWAY_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusEl.textContent = `✅ ${data.service} v${data.version}`;
            indicatorEl.style.color = '#28a745'; // green
        } else {
            statusEl.textContent = '⚠️ Gateway responded but status unknown';
            indicatorEl.style.color = '#ffc107'; // yellow
        }
    } catch (error) {
        statusEl.textContent = '❌ Gateway not reachable';
        indicatorEl.style.color = '#dc3545'; // red
        console.error('Health check failed:', error);
    }
}

/**
 * Send message to the gateway
 */
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const modelSelect = document.getElementById('model-select');
    const sendBtn = document.getElementById('send-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const responseDisplay = document.getElementById('response-display');
    const metadataDisplay = document.getElementById('metadata-display');
    
    const message = messageInput.value.trim();
    const model = modelSelect.value;
    
    if (!message) {
        alert('Please enter a message');
        return;
    }
    
    // Disable button and show spinner
    sendBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';
    
    // Clear previous response
    responseDisplay.innerHTML = '<p class="placeholder">Waiting for response...</p>';
    responseDisplay.classList.remove('has-content', 'error');
    
    // Build request payload
    const payload = {
        model: model,
        messages: [
            {
                role: 'user',
                content: message
            }
        ],
        temperature: 0.7,
        max_tokens: 1000
    };
    
    // Record start time
    const startTime = Date.now();
    
    try {
        const response = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Display response
        const content = data.choices?.[0]?.message?.content || 'No content in response';
        responseDisplay.innerHTML = `<p>${escapeHtml(content)}</p>`;
        responseDisplay.classList.add('has-content');
        
        // Display metadata
        const metadata = {
            model: data.model || model,
            latency_ms: latency,
            usage: data.usage || 'Not provided',
            finish_reason: data.choices?.[0]?.finish_reason || 'unknown',
            timestamp: new Date().toISOString()
        };
        
        metadataDisplay.textContent = JSON.stringify(metadata, null, 2);
        
    } catch (error) {
        console.error('Error sending message:', error);
        responseDisplay.innerHTML = `<p><strong>Error:</strong> ${escapeHtml(error.message)}</p>`;
        responseDisplay.classList.add('error');
        
        metadataDisplay.textContent = JSON.stringify({
            error: error.message,
            timestamp: new Date().toISOString()
        }, null, 2);
    } finally {
        // Re-enable button
        sendBtn.disabled = false;
        btnText.style.display = 'inline';
        btnSpinner.style.display = 'none';
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
