document.addEventListener('DOMContentLoaded', function () {
    const followUpSelect = document.getElementById("followUp");
    const followUpDateField = document.getElementById("followUpDate");

    // Initialize follow-up date visibility
    followUpDateField.disabled = followUpSelect.value !== "Yes";

    followUpSelect.addEventListener("change", function () {
        followUpDateField.disabled = this.value !== "Yes";
    });

    const paymentMethodSelect = document.getElementById('paymentMethod');
    const insuranceProviderGroup = document.getElementById('insuranceProviderGroup');
    const insuranceClaimGroup = document.getElementById('insuranceClaimGroup');

    // Initialize insurance fields visibility
    if (paymentMethodSelect.value === 'insurance') {
        insuranceProviderGroup.style.display = 'block';
        insuranceClaimGroup.style.display = 'block';
    } else {
        insuranceProviderGroup.style.display = 'none';
        insuranceClaimGroup.style.display = 'none';
    }

    paymentMethodSelect.addEventListener('change', function () {
        if (this.value === 'insurance') {
            insuranceProviderGroup.style.display = 'block';
            insuranceClaimGroup.style.display = 'block';
        } else {
            insuranceProviderGroup.style.display = 'none';
            insuranceClaimGroup.style.display = 'none';
        }
    });
});

 document.getElementById("imageFiles").addEventListener("change", async (event) => {
        const previewContainer = document.getElementById("previewContainer");
        previewContainer.innerHTML = ""; // Clear existing previews

        const files = event.target.files; // Get the selected files
        for (const file of files) {
            const reader = new FileReader();
            reader.onload = function(e) {
                // Create a new image element for each selected file
                const img = document.createElement("img");
                img.src = e.target.result;  // Set image source to the preview
                img.classList.add("img-thumbnail"); // Add Bootstrap class for styling

                const col = document.createElement("div");
                col.classList.add("col-md-3", "mb-3");  // Create column for grid layout
                col.appendChild(img);  // Append image to the column

                previewContainer.appendChild(col);  // Add the column to the preview container
            };
            reader.readAsDataURL(file); // Read the file as a data URL (base64)
        }
    });

    document.getElementById("previewContainer").addEventListener("click", (event) => {
        if (event.target.tagName === "IMG") {
            const modalImage = document.getElementById("fullImagePreview");
            modalImage.src = event.target.src; // Set modal image to clicked preview image
            const modal = new bootstrap.Modal(document.getElementById("imageModal"));
            modal.show(); // Show the modal
        }
    });