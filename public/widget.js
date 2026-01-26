/**
 * 🤖 RobovAI Nova - Embeddable Chat Widget
 * Version: 3.0.0
 * 
 * Usage:
 * <script src="https://your-domain.com/static/widget.js"></script>
 * <script>
 *   RobovAI.init({
 *     apiEndpoint: 'https://your-domain.com/webhook',
 *     theme: 'dark',
 *     position: 'bottom-right'
 *   });
 * </script>
 */

(function() {
    'use strict';

    // Widget Configuration
    const defaultConfig = {
        apiEndpoint: '/webhook',
        theme: 'dark',
        position: 'bottom-right',
        greeting: 'أهلاً! أنا RobovAI Nova 🤖 كيف ممكن أساعدك؟',
        placeholder: 'اكتب رسالتك هنا...',
        title: 'RobovAI Nova',
        primaryColor: '#00f0ff',
        secondaryColor: '#8b5cf6'
    };

    let config = {};
    let isOpen = false;
    let sessionId = 'widget_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Generate CSS
    function generateStyles() {
        return `
            .robovai-widget * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
            }

            .robovai-widget-button {
                position: fixed;
                ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
                bottom: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor});
                border: none;
                cursor: pointer;
                box-shadow: 0 5px 30px rgba(0, 240, 255, 0.4);
                z-index: 999998;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
            }

            .robovai-widget-button:hover {
                transform: scale(1.1);
                box-shadow: 0 10px 40px rgba(0, 240, 255, 0.6);
            }

            .robovai-widget-button.hidden { display: none; }

            .robovai-widget-container {
                position: fixed;
                ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
                bottom: 90px;
                width: 380px;
                height: 550px;
                background: #0a0a1a;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                z-index: 999999;
                display: none;
                flex-direction: column;
                overflow: hidden;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .robovai-widget-container.open { display: flex; }

            .robovai-widget-header {
                padding: 16px 20px;
                background: linear-gradient(135deg, rgba(0, 240, 255, 0.1), rgba(139, 92, 246, 0.1));
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .robovai-widget-header-left {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .robovai-widget-avatar {
                width: 40px;
                height: 40px;
                border-radius: 12px;
                background: linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor});
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
            }

            .robovai-widget-title {
                color: white;
                font-size: 16px;
                font-weight: 700;
            }

            .robovai-widget-status {
                color: #00ff88;
                font-size: 11px;
            }

            .robovai-widget-close {
                background: none;
                border: none;
                color: #888;
                font-size: 24px;
                cursor: pointer;
                transition: color 0.3s;
            }

            .robovai-widget-close:hover { color: white; }

            .robovai-widget-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }

            .robovai-widget-messages::-webkit-scrollbar { width: 4px; }
            .robovai-widget-messages::-webkit-scrollbar-thumb { 
                background: rgba(255, 255, 255, 0.2); 
                border-radius: 4px; 
            }

            .robovai-widget-message {
                max-width: 85%;
                padding: 12px 16px;
                border-radius: 16px;
                font-size: 14px;
                line-height: 1.6;
                animation: robovai-msg-in 0.3s ease;
            }

            @keyframes robovai-msg-in {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .robovai-widget-message.user {
                align-self: flex-end;
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(0, 240, 255, 0.2));
                color: white;
                border: 1px solid rgba(139, 92, 246, 0.3);
            }

            .robovai-widget-message.bot {
                align-self: flex-start;
                background: rgba(255, 255, 255, 0.05);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .robovai-widget-input-container {
                padding: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                gap: 10px;
            }

            .robovai-widget-input {
                flex: 1;
                padding: 12px 16px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: white;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }

            .robovai-widget-input:focus {
                border-color: ${config.primaryColor};
            }

            .robovai-widget-input::placeholder { color: #666; }

            .robovai-widget-send {
                width: 45px;
                height: 45px;
                border-radius: 12px;
                background: linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor});
                border: none;
                color: black;
                font-size: 18px;
                cursor: pointer;
                transition: transform 0.2s;
            }

            .robovai-widget-send:hover {
                transform: scale(1.05);
            }

            .robovai-widget-typing {
                display: flex;
                gap: 5px;
                padding: 12px 16px;
                align-self: flex-start;
            }

            .robovai-widget-typing span {
                width: 8px;
                height: 8px;
                background: ${config.primaryColor};
                border-radius: 50%;
                animation: robovai-typing 1.4s infinite ease-in-out;
            }

            .robovai-widget-typing span:nth-child(2) { animation-delay: 0.2s; }
            .robovai-widget-typing span:nth-child(3) { animation-delay: 0.4s; }

            @keyframes robovai-typing {
                0%, 100% { transform: translateY(0); opacity: 0.5; }
                50% { transform: translateY(-5px); opacity: 1; }
            }

            .robovai-widget-powered {
                text-align: center;
                padding: 8px;
                font-size: 10px;
                color: #555;
            }

            .robovai-widget-powered a {
                color: ${config.primaryColor};
                text-decoration: none;
            }

            @media (max-width: 420px) {
                .robovai-widget-container {
                    width: calc(100vw - 20px);
                    height: 70vh;
                    right: 10px;
                    left: 10px;
                    bottom: 80px;
                }
            }
                }
            }
            
            .robovai-image-card {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                overflow: hidden;
                margin-top: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .robovai-image-card img {
                width: 100%;
                height: auto;
                display: block;
                cursor: pointer;
                transition: transform 0.3s;
            }
            
            .robovai-image-card img:hover {
                transform: scale(1.02);
            }
            
            .robovai-card-content {
                padding: 12px;
                font-size: 0.9em;
                color: #ddd;
            }
        `;
    }

    // Create Widget DOM
    function createWidget() {
        // Inject styles
        const style = document.createElement('style');
        style.textContent = generateStyles();
        document.head.appendChild(style);

        // Create button
        const button = document.createElement('button');
        button.className = 'robovai-widget-button';
        button.innerHTML = '<img src="assets/logo.png" alt="Chat" style="width: 70%; height: 70%; object-fit: contain;">';
        button.onclick = toggleWidget;
        document.body.appendChild(button);

        // Create container
        const container = document.createElement('div');
        container.className = 'robovai-widget robovai-widget-container';
        container.innerHTML = `
            <div class="robovai-widget-header">
                <div class="robovai-widget-header-left">
                    <div class="robovai-widget-avatar"><img src="assets/logo.png" alt="Nova" style="width: 70%; height: 70%; object-fit: contain;"></div>
                    <div>
                        <div class="robovai-widget-title">${config.title}</div>
                        <div class="robovai-widget-status">● متصل الآن</div>
                    </div>
                </div>
                <button class="robovai-widget-close" onclick="RobovAI.toggle()">×</button>
            </div>
            <div class="robovai-widget-messages" id="robovai-messages"></div>
            <div class="robovai-widget-input-container">
                <input type="text" class="robovai-widget-input" id="robovai-input" 
                       placeholder="${config.placeholder}"
                       onkeydown="if(event.key==='Enter')RobovAI.send()">
                <button class="robovai-widget-send" onclick="RobovAI.send()">➜</button>
            </div>
            <div class="robovai-widget-powered">
                Powered by <a href="https://robovai.com" target="_blank">RobovAI Nova</a>
            </div>
        `;
        document.body.appendChild(container);

        // Add greeting
        addMessage(config.greeting, 'bot');
    }

    // Toggle widget
    function toggleWidget() {
        isOpen = !isOpen;
        const container = document.querySelector('.robovai-widget-container');
        const button = document.querySelector('.robovai-widget-button');
        
        if (isOpen) {
            container.classList.add('open');
            button.innerHTML = '×';
            document.getElementById('robovai-input').focus();
        } else {
            container.classList.remove('open');
            button.innerHTML = '<img src="assets/logo.png" alt="Chat" style="width: 70%; height: 70%; object-fit: contain;">';
        }
    }

    // Add message to chat
    function addMessage(text, sender) {
        const messages = document.getElementById('robovai-messages');
        const msg = document.createElement('div');
        msg.className = `robovai-widget-message ${sender}`;
        msg.innerHTML = formatText(text);
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    // Format text (basic markdown)
    function formatText(text) {
        // Check for generated image
        if (text.includes('![Generated Image]')) {
            const imgMatch = text.match(/!\[Generated Image\]\((.*?)\)/);
            const url = imgMatch ? imgMatch[1] : '';
            
            // Clean text
            let cleanText = text.replace(/!\[Generated Image\]\(.*?\)/, '').trim();
            cleanText = cleanText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                               .replace(/\*(.*?)\*/g, '<em>$1</em>')
                               .replace(/\n/g, '<br>');
            
            return `
                <div class="robovai-image-card">
                    <img src="${url}" onclick="window.open('${url}', '_blank')">
                    <div class="robovai-card-content">
                        ${cleanText}
                    </div>
                </div>
            `;
        }

        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 5px;border-radius:3px;">$1</code>');
    }

    // Show typing indicator
    function showTyping() {
        const messages = document.getElementById('robovai-messages');
        const typing = document.createElement('div');
        typing.id = 'robovai-typing';
        typing.className = 'robovai-widget-typing';
        typing.innerHTML = '<span></span><span></span><span></span>';
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    }

    // Hide typing indicator
    function hideTyping() {
        const typing = document.getElementById('robovai-typing');
        if (typing) typing.remove();
    }

    // Send message
    async function sendMessage() {
        const input = document.getElementById('robovai-input');
        const text = input.value.trim();
        
        if (!text) return;
        
        // Add user message
        addMessage(text, 'user');
        input.value = '';
        
        // Show typing
        showTyping();
        
        try {
            const response = await fetch(config.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: sessionId,
                    message: text,
                    platform: 'web_widget',
                    metadata: {
                        url: window.location.href,
                        referrer: document.referrer
                    }
                })
            });
            
            const data = await response.json();
            hideTyping();
            
            const reply = data.response || data.output || 'تم معالجة طلبك';
            addMessage(reply, 'bot');
            
        } catch (error) {
            hideTyping();
            addMessage('❌ حدث خطأ في الاتصال. حاول مرة أخرى.', 'bot');
        }
    }

    // Public API
    window.RobovAI = {
        init: function(userConfig) {
            config = { ...defaultConfig, ...userConfig };
            
            // Load Google Font
            const font = document.createElement('link');
            font.href = 'https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap';
            font.rel = 'stylesheet';
            document.head.appendChild(font);
            
            // Create widget when DOM ready
            if (document.readyState === 'complete') {
                createWidget();
            } else {
                window.addEventListener('load', createWidget);
            }
        },
        
        toggle: toggleWidget,
        send: sendMessage,
        
        open: function() {
            if (!isOpen) toggleWidget();
        },
        
        close: function() {
            if (isOpen) toggleWidget();
        },
        
        setConfig: function(newConfig) {
            config = { ...config, ...newConfig };
        }
    };
})();
