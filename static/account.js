 // Function to preview the uploaded image
    function previewImage(event) {
        const input = event.target; // File input element
        const preview = document.getElementById('profilePicture'); // Image preview element

        if (input.files && input.files[0]) {
            const reader = new FileReader();

            reader.onload = function (e) {
                preview.src = e.target.result; // Set preview image source to uploaded file
            };

            reader.readAsDataURL(input.files[0]); // Read the selected file
        }
    }

    // Function to confirm removing profile picture
    function confirmRemoveProfilePicture() {
        if (confirm("Are you sure you want to remove your profile picture?")) {
            // Set the hidden input value to signal that we want to remove the picture
            document.getElementById('remove_picture').value = 'yes';

            // Reset the preview to a placeholder image
            const preview = document.getElementById('profilePicture');
            preview.src = "https://via.placeholder.com/150";  // Default placeholder image

            // Clear the file input field (if the user clicks to remove, reset file input)
            const input = document.getElementById('profilePictureInput');
            input.value = ''; // Clear file input field

            // Submit the form after removal action
            document.getElementById('profilePictureForm').submit(); // Ensure you're submitting the form
        }
    }


    document.addEventListener("DOMContentLoaded", function () {
        // Store original form values
        const originalFormValues = {};

        // Toggle Edit Mode
        function toggleEditMode(section, isEdit) {
            const inputs = document.querySelectorAll(`#${section}Form input, #${section}Form textarea, #${section}Form select`);
            const submitButton = document.querySelector(`#${section}Form button[type="submit"]`);
            const editButton = document.querySelector(`#${section}Form button[data-enable-edit]`);
            const cancelButton = document.querySelector(`#${section}Form button[data-cancel-edit]`);

            inputs.forEach(input => input.disabled = !isEdit); // Enable/Disable inputs
            submitButton.disabled = !isEdit; // Enable/Disable submit button
            editButton.disabled = isEdit; // Disable edit button when in edit mode
            cancelButton.disabled = !isEdit; // Enable/Disable cancel button when in edit mode

            if (isEdit) {
                // Save original values when enabling edit mode
                inputs.forEach(input => {
                    originalFormValues[input.name] = input.value;
                });
            } else {
                // Restore original values when canceling edit mode
                inputs.forEach(input => input.value = originalFormValues[input.name] || '');
            }
        }

        // Attach event listeners for enabling and canceling edit mode
        document.querySelectorAll("[data-enable-edit], [data-cancel-edit]").forEach(button => {
            button.addEventListener("click", function () {
                const section = this.dataset.enableEdit || this.dataset.cancelEdit;
                const isEdit = this.dataset.enableEdit != undefined;
                toggleEditMode(section, isEdit);
            });
        });

        // Attach event listeners for form submission (Save)
        document.querySelectorAll("[id$='Form']").forEach(form => {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                this.submit(); // Directly submit the form to the server
            });
        });

           // Password Validation Script
    const passwordRules = {
        length: document.getElementById('length-rule'),
        uppercase: document.getElementById('uppercase-rule'),
        number: document.getElementById('number-rule'),
        specialChar: document.getElementById('special-char-rule')
    };

    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const updateBtn = document.getElementById('update-btn');
    const passwordForm = document.getElementById('passwordForm');

    function validatePassword() {
        const password = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const isValid = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            number: /\d/.test(password),
            specialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
            match: password === confirmPassword
        };

        // Update password validation rules UI
        Object.keys(isValid).forEach(rule => {
            if (passwordRules[rule]) {
                passwordRules[rule].classList.toggle('valid', isValid[rule]);
                passwordRules[rule].classList.toggle('invalid', !isValid[rule]);
            }
        });

        confirmPasswordInput.classList.toggle('is-invalid', !isValid.match);
        confirmPasswordInput.classList.toggle('is-valid', isValid.match);

        updateBtn.disabled = !Object.values(isValid).every(Boolean); // Enable/Disable update button
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

    // Password Change - Handle form submission
    updateBtn.addEventListener("click", function () {
        if (!updateBtn.disabled) {
            passwordForm.submit(); // Submit form to backend
        } else {
            alert("Please ensure all password rules are met.");
        }
    });


    // Password Change Cancel - Clear password fields when cancel is clicked
    document.querySelector("#cancel-btn").addEventListener("click", function () {
        ['currentPassword', 'newPassword', 'confirmPassword'].forEach(id => document.getElementById(id).value = "");
        Object.values(passwordRules).forEach(rule => rule.classList.remove('valid', 'invalid'));
    });

});