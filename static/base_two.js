

// toast notification
 document.addEventListener("DOMContentLoaded", function () {
        // Automatically show Bootstrap toasts
        const toastElList = [].slice.call(document.querySelectorAll('.toast'));
        const toastList = toastElList.map(function (toastEl) {
            return new bootstrap.Toast(toastEl).show();
        });

        // Dynamic Toast Positioning
        const toastContainer = document.getElementById("toastContainer");

        function updateToastPosition() {
            const scrollY = window.scrollY || window.pageYOffset;
            const windowHeight = window.innerHeight;

            if (scrollY > windowHeight / 2) {
                // User is scrolled down past the midpoint of the page
                toastContainer.style.top = "unset";
                toastContainer.style.bottom = "20px"; // Adjust distance from bottom
                toastContainer.style.left = "50%";
                toastContainer.style.transform = "translateX(-50%)";
            } else {
                // User is near the top of the page
                toastContainer.style.top = "20px"; // Adjust distance from top
                toastContainer.style.bottom = "unset";
                toastContainer.style.left = "50%";
                toastContainer.style.transform = "translateX(-50%)";
            }
        }

        // Update position on page load and on scroll
        updateToastPosition();
        window.addEventListener("scroll", updateToastPosition);
    });

  // pop over
    document.addEventListener("DOMContentLoaded", function () {
    const helpIcon = document.getElementById('helpIcon');
    const popover = new bootstrap.Popover(helpIcon, {
        trigger: 'manual',
        sanitize: false,
        placement: 'right'
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
});