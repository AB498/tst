// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNavClose = document.querySelector('.mobile-nav-close');
    const mobileNav = document.querySelector('.mobile-nav');

    if (mobileMenuToggle && mobileNavClose && mobileNav) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileNav.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        mobileNavClose.addEventListener('click', function() {
            mobileNav.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Close message alerts
    const messageCloseButtons = document.querySelectorAll('.message-close');

    messageCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.closest('.message');
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
                // Using display:none instead of remove() to prevent potential issues
                // message.remove();
            }, 300);
        });
    });

    // Auto-hide messages after 5 seconds
    const messageAlerts = document.querySelectorAll('.fixed.top-20 .message');

    messageAlerts.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
                // Using display:none instead of remove() to prevent potential issues
                // message.remove();
            }, 300);
        }, 5000);
    });
});
