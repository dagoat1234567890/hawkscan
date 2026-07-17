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
                const wrapper = document.createElement('div');
                wrapper.style.display = 'flex';
                wrapper.style.alignItems = 'center';
                wrapper.style.justifyContent = 'space-between';
                wrapper.style.border = '1px solid var(--border-color)';
                wrapper.style.borderRadius = '8px';
                wrapper.style.marginBottom = '0.5rem';
                wrapper.style.background = conv.id === currentConversationId ? 'var(--border-color)' : 'transparent';
                
                const btn = document.createElement('button');
                btn.textContent = conv.title;
                btn.style.padding = '0.8rem';
                btn.style.flexGrow = '1';
                btn.style.background = 'transparent';
                btn.style.border = 'none';
                btn.style.color = 'var(--text-primary)';
                btn.style.cursor = 'pointer';
                btn.style.textAlign = 'left';
                btn.style.whiteSpace = 'nowrap';
                btn.style.overflow = 'hidden';
                btn.style.textOverflow = 'ellipsis';
                btn.onclick = () => loadMessages(conv.id);
                
                const delBtn = document.createElement('button');
                delBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
                delBtn.style.background = 'transparent';
                delBtn.style.border = 'none';
                delBtn.style.color = '#ef4444';
                delBtn.style.cursor = 'pointer';
                delBtn.style.padding = '0.8rem';
                delBtn.title = "Delete Chat";
                delBtn.onclick = async (e) => {
                    e.stopPropagation();
                    if(confirm("Are you sure you want to delete this chat?")) {
                        await fetch(`/api/conversations/${conv.id}`, { method: 'DELETE' });
                        if(currentConversationId === conv.id) {
                            newChatBtn.onclick();
                        } else {
                            loadConversations();
                        }
                    }
                };
                
                wrapper.appendChild(btn);
                wrapper.appendChild(delBtn);
                conversationList.appendChild(wrapper);
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
