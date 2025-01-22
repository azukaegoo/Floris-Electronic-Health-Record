document.addEventListener("DOMContentLoaded", function () {
    // Get all forms with the 'patient-form' class
    const forms = document.querySelectorAll(".patient-form");

    // Loop through each form and initialize the buttons
    forms.forEach(form => {
        const editButton = form.querySelector(".edit-btn");
        const cancelButton = form.querySelector(".cancel-btn");
        const saveButton = form.querySelector(".save-btn");
        const inputs = form.querySelectorAll("input, textarea, select");

        // Store the original values of the form fields
        const originalValues = {};
        inputs.forEach(input => {
            originalValues[input.id] = input.value;
        });

        // Toggle form fields between enabled and disabled states
        function toggleEditMode(isEditMode) {
            inputs.forEach(input => {
                input.disabled = !isEditMode; // Enable/Disable inputs
            });

            saveButton.disabled = !isEditMode; // Enable/Disable Save button
            editButton.disabled = isEditMode; // Disable Edit button while in Edit mode
            cancelButton.disabled = !isEditMode; // Enable Cancel button only in Edit mode
        }

        // Event listener for Edit button
        editButton.addEventListener("click", function () {
            toggleEditMode(true); // Enable form fields and show Save/Cancel buttons
        });

        // Event listener for Cancel button
        cancelButton.addEventListener("click", function () {
            // Restore the original values to inputs
            inputs.forEach(input => {
                input.value = originalValues[input.id];
            });
            toggleEditMode(false); // Disable form fields and hide Save/Cancel buttons
        });

        // Event listener for Save button
        saveButton.addEventListener("click", function () {
            // Handle saving the form data (you can add your save logic here)
            form.submit();
            toggleEditMode(false); // Disable edit mode after saving
        });
    });
});
