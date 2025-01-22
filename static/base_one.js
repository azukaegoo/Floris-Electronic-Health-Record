document.addEventListener("DOMContentLoaded", function () {
    // Automatically show Bootstrap toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.forEach(function (toastEl) {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });

    // Floating Help Icon Popover
    const helpIcon = document.getElementById('helpPopover');
    if (helpIcon) {
        const popover = new bootstrap.Popover(helpIcon, {
            trigger: 'manual',
            sanitize: false,
            placement: 'left'
        });

        helpIcon.addEventListener('click', function () {
            if (helpIcon.getAttribute('aria-expanded') === 'true') {
                popover.hide();
            } else {
                popover.show();
            }
        });

        document.addEventListener('click', function (event) {
            const isHelpIcon = helpIcon.contains(event.target);
            const isInsidePopover = document.querySelector('.popover')?.contains(event.target);

            if (!isHelpIcon && !isInsidePopover) {
                popover.hide();
            }
        });
    }
});