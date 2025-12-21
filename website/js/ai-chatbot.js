/**
 * 🤖 Recrut'der - Agent IA Multilingue
 * ====================================
 * Chatbot intelligent pour assistance utilisateur
 */

class RecrutderAIChatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.currentLang = localStorage.getItem('recrutder_lang') || 'en';
        this.apiUrl = 'http://localhost:8000/api/support/chatbot';
        this.init();
    }

    init() {
        this.createChatbotUI();
        this.attachEventListeners();
        this.loadWelcomeMessage();
    }

    createChatbotUI() {
        const chatbotHTML = `
            <div id="ai-chatbot" class="ai-chatbot">
                <!-- Bouton flottant -->
                <button id="chatbot-toggle" class="chatbot-toggle" aria-label="Open AI Assistant">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
                    </svg>
                    <span class="chatbot-badge">AI</span>
                </button>

                <!-- Fenêtre de chat -->
                <div id="chatbot-window" class="chatbot-window">
                    <!-- Header -->
                    <div class="chatbot-header">
                        <div class="chatbot-header-info">
                            <div class="chatbot-avatar">🤖</div>
                            <div>
                                <h3 data-i18n="chatbot.title">Recrut'der Assistant</h3>
                                <p class="chatbot-status" data-i18n="chatbot.status">Online - AI powered</p>
                            </div>
                        </div>
                        <button id="chatbot-close" class="chatbot-close" aria-label="Close">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </button>
                    </div>

                    <!-- Messages -->
                    <div id="chatbot-messages" class="chatbot-messages">
                        <!-- Messages seront ajoutés ici -->
                    </div>

                    <!-- Suggestions rapides -->
                    <div id="chatbot-suggestions" class="chatbot-suggestions">
                        <!-- Suggestions seront ajoutées ici -->
                    </div>

                    <!-- Input -->
                    <div class="chatbot-input">
                        <input 
                            type="text" 
                            id="chatbot-input-field" 
                            placeholder="Type your message..." 
                            data-i18n-placeholder="chatbot.placeholder"
                            autocomplete="off"
                        />
                        <button id="chatbot-send" class="chatbot-send" aria-label="Send message">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    attachEventListeners() {
        const toggle = document.getElementById('chatbot-toggle');
        const close = document.getElementById('chatbot-close');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input-field');

        toggle.addEventListener('click', () => this.toggleChatbot());
        close.addEventListener('click', () => this.closeChatbot());
        send.addEventListener('click', () => this.sendMessage());

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleChatbot() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');

        if (this.isOpen) {
            window.classList.add('active');
            toggle.classList.add('active');
        } else {
            window.classList.remove('active');
            toggle.classList.remove('active');
        }
    }

    closeChatbot() {
        this.isOpen = false;
        document.getElementById('chatbot-window').classList.remove('active');
        document.getElementById('chatbot-toggle').classList.remove('active');
    }

    loadWelcomeMessage() {
        const welcomeMessages = {
            en: "👋 Hello! I'm your Recrut'der AI assistant. How can I help you today?",
            fr: "👋 Bonjour! Je suis votre assistant IA Recrut'der. Comment puis-je vous aider aujourd'hui?",
            es: "👋 ¡Hola! Soy tu asistente de IA Recrut'der. ¿Cómo puedo ayudarte hoy?",
            de: "👋 Hallo! Ich bin Ihr Recrut'der KI-Assistent. Wie kann ich Ihnen heute helfen?",
            ar: "👋 مرحبا! أنا مساعد الذكاء الاصطناعي Recrut'der. كيف يمكنني مساعدتك اليوم؟",
            zh: "👋 你好！我是您的 Recrut'der AI 助手。今天我能帮您什么？",
            pt: "👋 Olá! Sou seu assistente de IA Recrut'der. Como posso ajudá-lo hoje?",
            ru: "👋 Здравствуйте! Я ваш AI-помощник Recrut'der. Чем могу вам помочь сегодня?",
            hi: "👋 नमस्ते! मैं आपका Recrut'der AI सहायक हूं। आज मैं आपकी कैसे मदद कर सकता हूं?",
            bn: "👋 হ্যালো! আমি আপনার Recrut'der AI সহায়ক। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
        };

        const suggestions = {
            en: ["How does matching work?", "Pricing plans", "Register as candidate", "I'm a recruiter"],
            fr: ["Comment fonctionne le matching?", "Plans tarifaires", "S'inscrire comme candidat", "Je suis recruteur"],
            es: ["¿Cómo funciona el matching?", "Planes de precios", "Registrarse como candidato", "Soy reclutador"],
            de: ["Wie funktioniert das Matching?", "Preispläne", "Als Kandidat registrieren", "Ich bin Recruiter"],
            ar: ["كيف يعمل التطابق؟", "خطط التسعير", "التسجيل كمرشح", "أنا موظف توظيف"],
            zh: ["匹配如何工作？", "价格计划", "注册为候选人", "我是招聘人员"],
            pt: ["Como funciona o matching?", "Planos de preços", "Registrar como candidato", "Sou recrutador"],
            ru: ["Как работает сопоставление?", "Тарифные планы", "Зарегистрироваться как кандидат", "Я рекрутер"],
            hi: ["मैचिंग कैसे काम करती है?", "मूल्य निर्धारण योजनाएं", "उम्मीदवार के रूप में पंजीकरण करें", "मैं एक रिक्रूटर हूं"],
            bn: ["ম্যাচিং কিভাবে কাজ করে?", "মূল্য পরিকল্পনা", "প্রার্থী হিসাবে নিবন্ধন করুন", "আমি একজন নিয়োগকর্তা"]
        };

        this.addMessage('bot', welcomeMessages[this.currentLang] || welcomeMessages.en);
        this.showSuggestions(suggestions[this.currentLang] || suggestions.en);
    }

    showSuggestions(suggestions) {
        const container = document.getElementById('chatbot-suggestions');
        container.innerHTML = suggestions.map(suggestion =>
            `<button class="suggestion-btn" data-suggestion="${suggestion}">${suggestion}</button>`
        ).join('');

        // Attach click handlers
        container.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const suggestion = btn.dataset.suggestion;
                document.getElementById('chatbot-input-field').value = suggestion;
                this.sendMessage();
            });
        });
    }

    addMessage(type, text) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${type}`;

        const avatar = type === 'bot' ? '🤖' : '👤';
        const time = new Date().toLocaleTimeString(this.currentLang, { hour: '2-digit', minute: '2-digit' });

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.messages.push({ type, text, timestamp: new Date() });
    }

    formatMessage(text) {
        // Format links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        // Format bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Format line breaks
        text = text.replace(/\n/g, '<br>');
        return text;
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input-field');
        const message = input.value.trim();

        if (!message) return;

        // Add user message
        this.addMessage('user', message);
        input.value = '';

        // Hide suggestions
        document.getElementById('chatbot-suggestions').innerHTML = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Call API
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    language: this.currentLang,
                    context: {
                        page: window.location.pathname,
                        previous_messages: this.messages.slice(-5)
                    }
                })
            });

            if (!response.ok) {
                throw new Error('API error');
            }

            const data = await response.json();

            // Remove typing indicator
            this.hideTypingIndicator();

            // Add bot response
            this.addMessage('bot', data.response || this.getFallbackResponse());

        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTypingIndicator();
            this.addMessage('bot', this.getFallbackResponse());
        }
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chatbot-message bot';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    getFallbackResponse() {
        const fallbacks = {
            en: "I'm here to help! You can ask me about our features, pricing, or how to get started. Or contact our support team at support@recrutder.com",
            fr: "Je suis là pour vous aider! Vous pouvez me poser des questions sur nos fonctionnalités, tarifs, ou comment commencer. Ou contactez notre support à support@recrutder.com",
            es: "¡Estoy aquí para ayudar! Puede preguntarme sobre nuestras funciones, precios o cómo empezar. O contacte a nuestro equipo de soporte en support@recrutder.com",
            de: "Ich bin hier um zu helfen! Sie können mich nach unseren Funktionen, Preisen oder wie Sie beginnen können fragen. Oder kontaktieren Sie unser Support-Team unter support@recrutder.com",
            ar: "أنا هنا للمساعدة! يمكنك أن تسألني عن ميزاتنا أو الأسعار أو كيفية البدء. أو اتصل بفريق الدعم لدينا على support@recrutder.com",
            zh: "我在这里帮助您！您可以问我有关我们的功能、定价或如何开始的问题。或联系我们的支持团队：support@recrutder.com",
            pt: "Estou aqui para ajudar! Você pode me perguntar sobre nossos recursos, preços ou como começar. Ou entre em contato com nossa equipe de suporte em support@recrutder.com",
            ru: "Я здесь, чтобы помочь! Вы можете спросить меня о наших функциях, ценах или как начать. Или свяжитесь с нашей службой поддержки по адресу support@recrutder.com",
            hi: "मैं मदद के लिए यहाँ हूँ! आप मुझसे हमारी सुविधाओं, मूल्य निर्धारण या कैसे शुरू करें के बारे में पूछ सकते हैं। या support@recrutder.com पर हमारी सहायता टीम से संपर्क करें",
            bn: "আমি সাহায্য করতে এখানে আছি! আপনি আমাকে আমাদের বৈশিষ্ট্য, মূল্য বা কীভাবে শুরু করবেন সে সম্পর্কে জিজ্ঞাসা করতে পারেন। অথবা support@recrutder.com এ আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন"
        };
        return fallbacks[this.currentLang] || fallbacks.en;
    }

    updateLanguage(lang) {
        this.currentLang = lang;
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.recrutderChatbot = new RecrutderAIChatbot();
});
