/**
 * PlacementTracker - Lightweight Vanilla JavaScript (100% Offline)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Data-confirm prompt on destructive buttons/forms
    const confirmTriggers = document.querySelectorAll('[data-confirm]');
    confirmTriggers.forEach(element => {
        element.addEventListener('click', (e) => {
            const message = element.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 2. Alert dismissal click
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.cursor = 'pointer';
        alert.setAttribute('title', 'Click to dismiss');
        alert.addEventListener('click', () => {
            alert.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-4px)';
            setTimeout(() => {
                alert.remove();
            }, 200);
        });
    });

    // 3. Auto-submit filter form on select change (optional convenience)
    const autoSubmitSelects = document.querySelectorAll('.filter-form select');
    autoSubmitSelects.forEach(select => {
        select.addEventListener('change', () => {
            // Uncomment below if instant filter on dropdown change is desired
            // select.closest('form').submit();
        });
    });
});
