function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach(el => {
        setTimeout(() => {
            try { bootstrap.Alert.getOrCreateInstance(el).close(); } catch (_) {}
        }, 5000);
    });

    const currentPath = window.location.pathname;
    document.querySelectorAll('.gh-nav-links .nav-link').forEach(link => {
        if (link.getAttribute('href') && currentPath.startsWith(new URL(link.href).pathname)) {
            link.classList.add('active');
        }
    });
});
