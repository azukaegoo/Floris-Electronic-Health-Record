
        // Password Validation Script
        const newPasswordInput = document.getElementById('new_password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        const resetBtn = document.getElementById('reset_btn');

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

            // Enable or disable reset button
            resetBtn.disabled = !(
                password.length >= 8 &&
                /[A-Z]/.test(password) &&
                /\d/.test(password) &&
                /[!@#$%^&*(),.?":{}|<>]/.test(password) &&
                passwordsMatch
            );
        }

        // Event listeners for password and confirm password inputs
        newPasswordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);

        // Toggle Password Visibility
        const showPasswordCheckbox = document.getElementById('show_password');
        showPasswordCheckbox.addEventListener('change', function () {
            const type = this.checked ? 'text' : 'password';
            newPasswordInput.type = type;
            confirmPasswordInput.type = type;
        });
