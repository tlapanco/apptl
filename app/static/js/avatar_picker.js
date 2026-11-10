/**
 * PersonaAI - Avatar Picker & Image Previewer Helper
 */

function setAvatarMode(mode) {
    const tabs = document.querySelectorAll('.avatar-tab-btn');
    tabs.forEach(t => {
        if (t.getAttribute('data-tab') === mode) {
            t.classList.add('active');
        } else {
            t.classList.remove('active');
        }
    });

    const typeField = document.getElementById('avatar_type_field');
    if (typeField) typeField.value = mode;

    const panelEmoji = document.getElementById('panel-avatar-emoji');
    const panelUrl = document.getElementById('panel-avatar-url');
    const panelFile = document.getElementById('panel-avatar-file');

    if (panelEmoji) panelEmoji.classList.toggle('hidden', mode !== 'emoji');
    if (panelUrl) panelUrl.classList.toggle('hidden', mode !== 'url');
    if (panelFile) panelFile.classList.toggle('hidden', mode !== 'file');

    // Actualizar vista previa según el modo activo
    if (mode === 'emoji') {
        const emojiVal = document.getElementById('avatar')?.value || '🤖';
        updateAvatarPreviewEmoji(emojiVal);
    } else if (mode === 'url') {
        const urlVal = document.getElementById('avatar_url')?.value || '';
        if (urlVal) updateAvatarPreviewUrl(urlVal);
    }
}

function selectEmoji(emoji) {
    const input = document.getElementById('avatar');
    if (input) {
        input.value = emoji;
        updateAvatarPreviewEmoji(emoji);
    }
}

function updateAvatarPreviewEmoji(emoji) {
    const display = document.getElementById('avatar-preview-display');
    if (display) {
        display.innerHTML = `<span class="avatar-emoji">${emoji || '🤖'}</span>`;
    }
}

function updateAvatarPreviewUrl(url) {
    const display = document.getElementById('avatar-preview-display');
    if (!display) return;
    if (!url || !url.trim()) {
        display.innerHTML = `<span class="avatar-emoji">🤖</span>`;
        return;
    }
    display.innerHTML = `<img src="${encodeURI(url.trim())}" alt="Preview" class="avatar-image" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" /><span class="avatar-fallback avatar-emoji" style="display:none;">🤖</span>`;
}

function previewUploadedImage(input) {
    const display = document.getElementById('avatar-preview-display');
    if (!display) return;

    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            display.innerHTML = `<img src="${e.target.result}" alt="Preview" class="avatar-image" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" /><span class="avatar-fallback avatar-emoji" style="display:none;">🤖</span>`;
        };
        reader.readAsDataURL(file);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar estado del picker si ya hay una URL o archivo existente
    const initialAvatar = document.getElementById('avatar')?.value || '';
    if (initialAvatar.startsWith('http://') || initialAvatar.startsWith('https://') || initialAvatar.startsWith('/static/')) {
        const urlInput = document.getElementById('avatar_url');
        if (urlInput) {
            urlInput.value = initialAvatar;
            setAvatarMode('url');
            updateAvatarPreviewUrl(initialAvatar);
        }
    }
});
