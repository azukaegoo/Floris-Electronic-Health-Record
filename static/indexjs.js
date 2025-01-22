  document.addEventListener('DOMContentLoaded', () => {
        const params = new URLSearchParams(window.location.search);
        const modal = params.get('modal');

        if (modal === 'login') {
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
            loginModal.show();
        } else if (modal === 'register') {
            const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
            registerModal.show();
        }
    });

    // Password validation and confirm password logic
    const newPasswordInput = document.getElementById('password_registration');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const registerBtn = document.getElementById('register_btn');

    const lengthRule = document.getElementById('length-rule');
    const uppercaseRule = document.getElementById('uppercase-rule');
    const numberRule = document.getElementById('number-rule');
    const specialCharRule = document.getElementById('special-char-rule');

    function validatePassword() {
        const password = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Validate password rules
        lengthRule.classList.toggle('valid', password.length >= 8);
        lengthRule.classList.toggle('invalid', password.length < 8);

        uppercaseRule.classList.toggle('valid', /[A-Z]/.test(password));
        uppercaseRule.classList.toggle('invalid', !/[A-Z]/.test(password));

        numberRule.classList.toggle('valid', /\d/.test(password));
        numberRule.classList.toggle('invalid', !/\d/.test(password));

        specialCharRule.classList.toggle('valid', /[!@#$%^&*(),.?":{}|<>]/.test(password));
        specialCharRule.classList.toggle('invalid', !/[!@#$%^&*(),.?":{}|<>]/.test(password));

        // Confirm password validation
        const passwordsMatch = password === confirmPassword && confirmPassword !== "";
        confirmPasswordInput.classList.toggle('is-invalid', !passwordsMatch);
        confirmPasswordInput.classList.toggle('is-valid', passwordsMatch);

        // Enable or disable register button
        registerBtn.disabled = !(
            password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /\d/.test(password) &&
            /[!@#$%^&*(),.?":{}|<>]/.test(password) &&
            passwordsMatch
        );
    }

    // Event listeners for password and confirm password
    newPasswordInput.addEventListener('input', validatePassword);
    confirmPasswordInput.addEventListener('input', validatePassword);

    // Toggle password visibility
    document.getElementById('show_password').addEventListener('change', function () {
        const type = this.checked ? 'text' : 'password';
        newPasswordInput.type = type;
        confirmPasswordInput.type = type;
    });

    document.getElementById('showLoginPassword').addEventListener('change', function () {
        const loginPasswordField = document.getElementById('loginPassword');
        loginPasswordField.type = this.checked ? 'text' : 'password';
    });