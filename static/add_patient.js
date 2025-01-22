 document.addEventListener("DOMContentLoaded", function () {
        const multipleYes = document.getElementById('multipleYes');
        const multipleNo = document.getElementById('multipleNo');
        const birthNoField = document.getElementById('birthNoField');
        const birthNoInput = document.getElementById('birthNo');

        const deceasedTrue = document.getElementById('deceasedTrue');
        const deceasedFalse = document.getElementById('deceasedFalse');
        const deceasedDetailsField = document.getElementById('deceasedDetailsField');

        // Toggle visibility for multiple birth
        function toggleBirthNoField() {
            if (multipleYes.checked) {
                birthNoField.style.display = "block";
                birthNoInput.disabled = false;
            } else {
                birthNoField.style.display = "none";
                birthNoInput.disabled = true;
            }
        }

        // Toggle visibility for deceased details
        function toggleDeceasedDetailsField() {
            if (deceasedTrue.checked) {
                deceasedDetailsField.style.display = "block";
                document.getElementById('dateDeceased').disabled = false;
                document.getElementById('reasonDeceased').disabled = false;
            } else {
                deceasedDetailsField.style.display = "none";
                document.getElementById('dateDeceased').disabled = true;
                document.getElementById('reasonDeceased').disabled = true;
            }
        }

        // Add event listeners
        multipleYes.addEventListener('change', toggleBirthNoField);
        multipleNo.addEventListener('change', toggleBirthNoField);
        deceasedTrue.addEventListener('change', toggleDeceasedDetailsField);
        deceasedFalse.addEventListener('change', toggleDeceasedDetailsField);

        // Initialize visibility on page load
        toggleBirthNoField();
        toggleDeceasedDetailsField();
    });


   document.getElementById('uploadPhoto').addEventListener('change', function(event) {
        const file = event.target.files[0]; // Get the selected file
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                // Update the thumbnail preview
                document.getElementById('photoPreview').src = e.target.result;
                // Update the full-size image in the modal
                document.getElementById('fullImagePreview').src = e.target.result;
            };
            reader.readAsDataURL(file); // Convert the file to a data URL
        }
    });