let currentSection = 0;
const sections = document.querySelectorAll('.form-section');
const progressSteps = document.querySelectorAll('.progress-step');

function showSection(index) {
    sections.forEach(section => section.classList.remove('active'));
    progressSteps.forEach(step => step.classList.remove('active'));
    
    sections[index].classList.add('active');
    progressSteps[index].classList.add('active');
    currentSection = index;
}

function nextSection(current) {
    if (current < sections.length - 1) {
        showSection(current + 1);
    }
}

function prevSection(current) {
    if (current > 0) {
        showSection(current - 1);
    }
}

// Initialize first section when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    showSection(0);
    
    // Setup chat input enter key handler
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Setup form submission handler
    const form = document.getElementById('ipAnalysisForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                technology_description: formData.get('technology_description'),
                trademark_name: formData.get('trademark_name'),
                market_description: formData.get('market_description'),
                estimated_revenue: formData.get('estimated_revenue'),
                budget: formData.get('budget'),
                timeline: formData.get('timeline'),
                competitor_list: formData.get('competitor_list')
            };
            
            // Show loading state
            document.getElementById('resultsSection').style.display = 'block';
            document.getElementById('resultsContent').innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>🤖 Analyzing your IP portfolio with AI agents...</p>
                    <p style="margin-top: 10px; font-size: 0.9em; color: #6b7280;">This may take 30-60 seconds...</p>
                </div>
            `;
            
            // Scroll to results
            document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                // DEBUG: Log the response to console
                console.log("API Response:", result);
                console.log("Available result fields:", {
                    result_refined: result.result_refined,
                    result: result.result,
                    result_raw: result.result_raw,
                    response: result.response
                });
                
                if (result.success) {
                    displayResults(result);
                } else {
                    document.getElementById('resultsContent').innerHTML = `
                        <div class="error">
                            <h4>❌ Analysis Failed</h4>
                            <p>${result.error || 'An error occurred during analysis.'}</p>
                            <p style="font-size: 0.9em; color: #6b7280; margin-top: 10px;">
                                Method: ${result.method || 'N/A'} | Model: ${result.model_used || 'N/A'}
                            </p>
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('resultsContent').innerHTML = `
                    <div class="error">
                        <h4>❌ Network Error</h4>
                        <p>Please check your connection and try again.</p>
                        <p style="font-size: 0.9em; color: #6b7280; margin-top: 10px;">${error.message}</p>
                    </div>
                `;
            }
        });
    }
});

function displayResults(result) {
    const resultsContent = document.getElementById('resultsContent');
    
    // FIX: Check all possible result fields
    const resultText = result.result_refined || result.result || result.result_raw || result.response || "";
    
    // Format the result text with better styling
    const formattedResult = formatResultText(resultText);
    
    let html = `
        <div class="result-card">
            <div class="result-header">
                <h4>✅ IP Analysis Complete</h4>
                <span class="model-badge">Powered by ${result.model_used}</span>
            </div>
            <div class="result-content">
                ${formattedResult}
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

function formatResultText(text) {
    if (!text || text.trim() === '') return '<p>No results available.</p>';
    
    // Split by double newlines for paragraphs
    let formatted = text
        .split('\n\n')
        .map(paragraph => {
            // Check if it's a heading (starts with # or all caps)
            if (paragraph.match(/^#{1,3}\s+(.+)$/)) {
                const match = paragraph.match(/^#{1,3}\s+(.+)$/);
                return `<h5>${match[1]}</h5>`;
            } else if (paragraph === paragraph.toUpperCase() && paragraph.length < 100) {
                return `<h5>${paragraph}</h5>`;
            }
            
            // Format bullet points
            if (paragraph.match(/^[-*•]\s+/)) {
                const items = paragraph.split('\n')
                    .filter(line => line.trim())
                    .map(line => `<li>${line.replace(/^[-*•]\s+/, '')}</li>`)
                    .join('');
                return `<ul>${items}</ul>`;
            }
            
            // Format numbered lists
            if (paragraph.match(/^\d+\.\s+/)) {
                const items = paragraph.split('\n')
                    .filter(line => line.trim())
                    .map(line => `<li>${line.replace(/^\d+\.\s+/, '')}</li>`)
                    .join('');
                return `<ol>${items}</ol>`;
            }
            
            // Regular paragraph
            return `<p>${paragraph.replace(/\n/g, '<br>')}</p>`;
        })
        .join('');
    
    return formatted || '<p>Analysis completed successfully.</p>';
}

// Chat functionality
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingId = addMessage('Thinking...', 'bot', true);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const result = await response.json();
        
        // Remove typing indicator
        removeMessage(typingId);
        
        if (result.success) {
            addMessage(result.response, 'bot');
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        // Remove typing indicator
        removeMessage(typingId);
        addMessage('Sorry, I cannot respond at the moment. Please try again later.', 'bot');
    }
}

function addMessage(text, sender, isTyping = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message${isTyping ? ' typing' : ''}`;
    messageDiv.textContent = text;
    
    // Generate unique ID for typing messages
    if (isTyping) {
        messageDiv.id = 'typing-' + Date.now();
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return isTyping ? messageDiv.id : null;
}

function removeMessage(messageId) {
    if (messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
}

// Pre-fill with sample data for testing (uncomment to enable)
function fillSampleData() {
    document.querySelector('[name="technology_description"]').value = "A novel AI-powered system for real-time patent analysis using machine learning to identify infringement risks and opportunities in large patent databases.";
    document.querySelector('[name="trademark_name"]').value = "PatentGuard AI";
    document.querySelector('[name="market_description"]').value = "Enterprise legal tech market focusing on law firms and corporate legal departments. Total addressable market estimated at $5B with 15% annual growth.";
    document.querySelector('[name="estimated_revenue"]').value = "$2M in Year 1, growing to $10M by Year 3";
    document.querySelector('[name="budget"]').value = "$75,000";
    document.querySelector('[name="timeline"]').value = "9 months for comprehensive IP protection";
    document.querySelector('[name="competitor_list"]').value = "CPA Global, Anaqua, Clarivate, Patsnap, LexisNexis";
}

// Uncomment the line below to enable sample data filling for testing
fillSampleData();
