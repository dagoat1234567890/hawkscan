document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const conversationList = document.getElementById('conversation-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    
    let currentConversationId = null;

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        if (sender === 'ai' && typeof marked !== 'undefined') {
            msgDiv.innerHTML = marked.parse(text);
        } else {
            msgDiv.textContent = text;
        }
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    async function loadConversations() {
        try {
            const res = await fetch('/api/conversations');
            const data = await res.json();
            conversationList.innerHTML = '';
            data.forEach(conv => {
                const btn = document.createElement('button');
                btn.textContent = conv.title;
                btn.style.padding = '0.8rem';
                btn.style.borderRadius = '8px';
                btn.style.border = '1px solid var(--border-color)';
                btn.style.background = conv.id === currentConversationId ? 'var(--border-color)' : 'transparent';
                btn.style.color = 'var(--text-primary)';
                btn.style.cursor = 'pointer';
                btn.style.textAlign = 'left';
                btn.onclick = () => loadMessages(conv.id);
                conversationList.appendChild(btn);
            });
        } catch (e) {
            console.error('Failed to load conversations', e);
        }
    }

    async function loadMessages(convId) {
        currentConversationId = convId;
        chatMessages.innerHTML = '';
        try {
            const res = await fetch(`/api/conversations/${convId}`);
            const data = await res.json();
            data.forEach(msg => {
                addMessage(msg.content, msg.role === 'assistant' ? 'ai' : 'user');
            });
            loadConversations(); // refresh list to highlight active
        } catch (e) {
            console.error('Failed to load messages', e);
        }
    }

    newChatBtn.onclick = () => {
        currentConversationId = null;
        chatMessages.innerHTML = `
            <div class="message ai">
                Hello! I am Hawkscan, your e-commerce and market analysis agent. How can I assist you today?
            </div>
        `;
        loadConversations();
    };

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        addMessage(text, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, conversation_id: currentConversationId }),
            });
            const data = await response.json();
            
            if (response.ok) {
                if (!currentConversationId && data.conversation_id) {
                    currentConversationId = data.conversation_id;
                    loadConversations();
                }
                addMessage(data.reply, 'ai');
                if (data.action) {
                    setTimeout(() => addMessage(`⚡ System Notification: ${data.action}`, 'ai'), 500);
                }
            } else {
                addMessage(`Error: ${data.error}`, 'ai');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Failed to communicate with Hermes.', 'ai');
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    loadConversations();
});
