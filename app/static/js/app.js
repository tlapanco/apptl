/**
 * PersonaAI - Aplicación Global Frontend
 * Manejo de interacciones AJAX (likes, descartar alertas, helpers)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-descartar mensajes Flash después de 5 segundos
    const flashAlerts = document.querySelectorAll('.flash-alert');
    if (flashAlerts.length > 0) {
        setTimeout(() => {
            flashAlerts.forEach(alert => {
                alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000);
    }

    // 2. Manejo de Likes AJAX en Personalidades
    document.querySelectorAll('.btn-like, .btn-like-mini').forEach(likeBtn => {
        likeBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const personalityId = likeBtn.dataset.personalityId;
            if (!personalityId) return;

            try {
                const response = await fetch(`/personalities/${personalityId}/like`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (response.status === 401) {
                    window.location.href = '/auth/login';
                    return;
                }

                if (!response.ok) {
                    throw new Error('Error al procesar el like');
                }

                const data = await response.json();
                
                // Actualizar contador
                const countSpan = document.getElementById(`like-count-${personalityId}`);
                if (countSpan) {
                    countSpan.textContent = data.likes_count;
                }

                // Actualizar estado del botón
                if (data.liked) {
                    likeBtn.classList.add('liked');
                    const label = likeBtn.querySelector('.like-label');
                    if (label) label.textContent = 'Te gusta';
                    const icon = likeBtn.querySelector('.like-icon, .heart-icon');
                    if (icon) icon.textContent = '❤️';
                } else {
                    likeBtn.classList.remove('liked');
                    const label = likeBtn.querySelector('.like-label');
                    if (label) label.textContent = 'Dar Like';
                    const icon = likeBtn.querySelector('.like-icon, .heart-icon');
                    if (icon) icon.textContent = '🤍';
                }
            } catch (err) {
                console.error('Error toggling like:', err);
            }
        });
    });

    // 3. Control de Modo Oscuro / Claro
    const themeToggleBtn = document.getElementById('theme-toggle');
    const updateThemeUI = (theme) => {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector('.theme-icon');
        if (icon) {
            icon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
        themeToggleBtn.setAttribute('title', theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
    };

    const initialTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeUI(initialTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('dochat_theme', newTheme);
            updateThemeUI(newTheme);
        });
    }
});

