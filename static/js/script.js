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

    const normalizePath = path => path.length > 1 ? path.replace(/\/+$/, '') : path;
    const currentPath = normalizePath(window.location.pathname);
    const navLinks = [...document.querySelectorAll('.gh-nav-links .nav-link')];
    const pathMatches = link => {
        const linkPath = normalizePath(new URL(link.href).pathname);
        return currentPath === linkPath || (
            link.dataset.activePrefix === 'true' &&
            currentPath.startsWith(`${linkPath}/`)
        );
    };
    const hashMatchExists = navLinks.some(link => {
        const linkUrl = new URL(link.href);
        return linkUrl.hash && linkUrl.hash === window.location.hash && pathMatches(link);
    });

    navLinks.forEach(link => {
        const linkHash = new URL(link.href).hash;
        const isCurrent = pathMatches(link) && (
            linkHash
                ? window.location.hash === linkHash
                : !hashMatchExists
        );

        if (isCurrent) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });
});
