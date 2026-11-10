/**
 * PersonaAI - Controlador de Chat Asíncrono
 * Maneja el envío y recepción de mensajes en tiempo real mediante fetch API
 */

document.addEventListener('DOMContentLoaded', () => {
    const chatLayout = document.getElementById('chat-layout');
    if (!chatLayout) return;

    const chatId = chatLayout.dataset.chatId;
    const chatForm = document.getElementById('chat-form');
    const inputField = document.getElementById('chat-input-field');
    const sendButton = document.getElementById('btn-send-message');
    const messagesContainer = document.getElementById('chat-messages-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const emptyGreeting = document.getElementById('chat-empty-greeting');

    let isSubmitting = false;

    // Auto-scroll al fondo al cargar
    scrollToBottom();

    // Auto-expand textarea
    inputField.addEventListener('input', () => {
        inputField.style.height = 'auto';
        inputField.style.height = Math.min(inputField.scrollHeight, 140) + 'px';
    });

    // Manejar envío al presionar Enter (sin Shift)
    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    if (sendButton) {
        sendButton.addEventListener('click', (e) => {
            e.preventDefault();
            sendMessage();
        });
    }

    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text || isSubmitting) return;

        isSubmitting = true;
        setFormDisabled(true);

        // Ocultar mensaje inicial de saludo si existía
        if (emptyGreeting) {
            emptyGreeting.style.display = 'none';
        }

        // 1. Agregar mensaje del usuario a la interfaz de inmediato
        appendUserMessage(text);
        inputField.value = '';
        inputField.style.height = 'auto';
        scrollToBottom();

        // 2. Mostrar indicador de 'escribiendo...'
        showTyping(true);
        scrollToBottom();

        try {
            const response = await fetch(`/chats/${chatId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            showTyping(false);

            if (!response.ok || !data.success) {
                const errorMsg = data.error || 'Hubo un inconveniente al generar la respuesta.';
                appendErrorMessage(errorMsg);
            } else {
                // 3. Agregar respuesta de la IA
                appendAssistantMessage(data.assistant_message.content, data.personality);
            }
        } catch (error) {
            console.error('Error enviando mensaje:', error);
            showTyping(false);
            appendErrorMessage('Error de conexión con el servidor. Por favor, intenta de nuevo.');
        } finally {
            isSubmitting = false;
            setFormDisabled(false);
            inputField.focus();
            scrollToBottom();
        }
    }

    function renderAvatarHtmlJs(avatarVal, defaultEmoji = '🤖') {
        if (!avatarVal) return `<span class="avatar-emoji">${defaultEmoji}</span>`;
        const str = String(avatarVal).trim();
        if (str.startsWith('http://') || str.startsWith('https://') || str.startsWith('/static/')) {
            return `<img src="${encodeURI(str)}" alt="Avatar" class="avatar-image" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" loading="lazy" /><span class="avatar-fallback avatar-emoji" style="display:none;">${defaultEmoji}</span>`;
        }
        return `<span class="avatar-emoji">${escapeHtml(str)}</span>`;
    }

    function appendUserMessage(content) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-bubble-wrapper message-user';

        // Intentar leer avatar del header si existe
        const userAvatarEl = document.querySelector('.user-menu-wrapper .user-avatar');
        const userAvatarContent = userAvatarEl ? userAvatarEl.innerHTML : '👤';

        wrapper.innerHTML = `
            <div class="message-avatar">${userAvatarContent}</div>
            <div class="message-body">
                <div class="message-header">
                    <span class="message-sender-name">Tú</span>
                    <span class="message-time">Ahora</span>
                </div>
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;

        // Insertar antes del indicador de typing
        messagesContainer.insertBefore(wrapper, typingIndicator);
    }

    function appendAssistantMessage(content, personalityInfo) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-bubble-wrapper message-assistant';

        const topbarAvatarEl = document.getElementById('chat-topbar-avatar-element');
        const avatarHtml = personalityInfo?.avatar 
            ? renderAvatarHtmlJs(personalityInfo.avatar, '🤖')
            : (topbarAvatarEl ? topbarAvatarEl.innerHTML : '🤖');

        const name = personalityInfo?.name || document.querySelector('.chat-personality-name')?.textContent.trim() || 'Asistente';

        wrapper.innerHTML = `
            <div class="message-avatar">${avatarHtml}</div>
            <div class="message-body">
                <div class="message-header">
                    <span class="message-sender-name">${escapeHtml(name)}</span>
                    <span class="message-time">Ahora</span>
                </div>
                <div class="message-text">${formatMessageContent(content)}</div>
            </div>
        `;

        messagesContainer.insertBefore(wrapper, typingIndicator);
    }

    function appendErrorMessage(errorText) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-bubble-wrapper message-assistant';

        wrapper.innerHTML = `
            <div class="message-avatar">⚠️</div>
            <div class="message-body">
                <div class="message-header">
                    <span class="message-sender-name">Sistema</span>
                    <span class="message-time">Error</span>
                </div>
                <div class="message-text" style="color: #ef4444; background: #fee2e2; border-color: #fca5a5;">
                    ${escapeHtml(errorText)}
                </div>
            </div>
        `;

        messagesContainer.insertBefore(wrapper, typingIndicator);
    }

    function showTyping(show) {
        if (show) {
            typingIndicator.classList.remove('hidden');
        } else {
            typingIndicator.classList.add('hidden');
        }
    }

    function setFormDisabled(disabled) {
        inputField.disabled = disabled;
        sendButton.disabled = disabled;
        if (disabled) {
            sendButton.style.opacity = '0.5';
        } else {
            sendButton.style.opacity = '1';
        }
    }

    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, m => map[m]);
    }

    function formatMessageContent(rawText) {
        if (!rawText) return '';
        
        let text = String(rawText).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Extract code blocks first to protect from formatting
        const codeBlocks = [];
        text = text.replace(/```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g, (match, lang, code) => {
            const langLabel = lang ? escapeHtml(lang) : 'código';
            const escapedCode = escapeHtml(code.replace(/^\n+|\n+$/g, ''));
            const placeholder = `%%%CODEBLOCK_${codeBlocks.length}%%%`;
            codeBlocks.push(
                `<div class="code-block-wrapper">` +
                `<div class="code-block-header">` +
                `<span class="code-lang">${langLabel}</span>` +
                `<button type="button" class="btn-copy-code" onclick="copyCodeSnippet(this)" title="Copiar código al portapapeles">Copiar</button>` +
                `</div>` +
                `<pre><code class="language-${langLabel}">${escapedCode}</code></pre>` +
                `</div>`
            );
            return placeholder;
        });

        // Extract inline code
        const inlineCodes = [];
        text = text.replace(/`([^`\n]+)`/g, (match, code) => {
            const placeholder = `%%%INLINECODE_${inlineCodes.length}%%%`;
            inlineCodes.push(`<code>${escapeHtml(code)}</code>`);
            return placeholder;
        });

        // Escape HTML for the rest
        text = escapeHtml(text);

        // Headers
        text = text.replace(/^### (.*$)/gim, '<h4>$1</h4>');
        text = text.replace(/^## (.*$)/gim, '<h3>$1</h3>');
        text = text.replace(/^# (.*$)/gim, '<h2>$1</h2>');

        // Blockquotes
        text = text.replace(/^\&gt;\s?(.*$)/gim, '<blockquote>$1</blockquote>');

        // Horizontal Rules
        text = text.replace(/^---+$/gim, '<hr>');

        // Bold & Italic
        text = text.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/_(.*?)_/g, '<em>$1</em>');
        text = text.replace(/~~(.*?)~~/g, '<del>$1</del>');

        // Markdown Links: [text](url)
        text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

        // Bullet lists
        text = text.replace(/(?:^|\n)[ \t]*[-*+][ \t]+(.*)/g, (match, item) => {
            return `\n<li class="bullet-item">${item}</li>`;
        });
        text = text.replace(/(<li class="bullet-item">.*?<\/li>)+/gs, (match) => {
            return `<ul class="chat-list">${match}</ul>`;
        });

        // Numbered lists
        text = text.replace(/(?:^|\n)[ \t]*\d+\.[ \t]+(.*)/g, (match, item) => {
            return `\n<li class="numbered-item">${item}</li>`;
        });
        text = text.replace(/(<li class="numbered-item">.*?<\/li>)+/gs, (match) => {
            return `<ol class="chat-list">${match}</ol>`;
        });

        // Restore Inline Codes
        inlineCodes.forEach((ic, idx) => {
            text = text.replace(new RegExp(`%%%INLINECODE_${idx}%%%`, 'g'), ic);
        });

        // Convert double newlines to paragraphs / single to <br>
        const paragraphs = text.split(/\n{2,}/);
        const formattedParagraphs = paragraphs.map(p => {
            p = p.trim();
            if (!p) return '';
            if (p.startsWith('<div class="code-block-wrapper"') || 
                p.startsWith('<h2>') || p.startsWith('<h3>') || p.startsWith('<h4>') || 
                p.startsWith('<blockquote>') || p.startsWith('<ul') || p.startsWith('<ol') || p.startsWith('<hr>')) {
                return p;
            }
            return `<p>${p.replace(/\n/g, '<br>')}</p>`;
        });

        text = formattedParagraphs.filter(Boolean).join('\n');

        // Restore Code Blocks
        codeBlocks.forEach((cb, idx) => {
            text = text.replace(new RegExp(`%%%CODEBLOCK_${idx}%%%`, 'g'), cb);
        });

        return text;
    }
});
