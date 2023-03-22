// Dropzone function
function handleFileSelect(event, dropzone) {
                        event.stopPropagation();
                        event.preventDefault();

                        const files = event.dataTransfer.files;

                        if (files.length > 0) {
                            dropzone.files = files;
                            dropzone.dispatchEvent(new Event('change'));
                        }
                    }

                    function handleDragOver(event) {
                        event.stopPropagation();
                        event.preventDefault();
                        event.dataTransfer.dropEffect = 'move';
                    }

                    document.addEventListener('DOMContentLoaded', function () {
                        const rawCountsDropzone = document.getElementById('raw_counts_dropzone');
                        const plateDiagramDropzone = document.getElementById('plate_diagram_dropzone');

                        rawCountsDropzone.parentNode.addEventListener('dragover', handleDragOver, false);
                        rawCountsDropzone.parentNode.addEventListener('drop', (event) => handleFileSelect(event, rawCountsDropzone), false);

                        plateDiagramDropzone.parentNode.addEventListener('dragover', handleDragOver, false);
                        plateDiagramDropzone.parentNode.addEventListener('drop', (event) => handleFileSelect(event, plateDiagramDropzone), false);
                    });


// Update table function
function updateTable() {
            window.onload = function () {
                const mainForm = document.getElementById("form");

                mainForm.addEventListener("submit", function (event) {
                    event.preventDefault();

                    const formData = new FormData(mainForm);

                    const fileInput = document.querySelector('input[type="file"]');
                    const files = fileInput.files;

                    for (let i = 0; i < files.length; i++) {
                        const file = files[i];
                        if (!formData.getAll('file').includes(file)) {
                            formData.append("file", file);
                        }
                    }

                    fetch("/process", {
                        method: "POST",
                        body: formData,
                    })
                        .then((response) => {
                            if (response.ok) {
                                return response.json();
                            } else {
                                throw new Error("Error uploading file");
                            }
                        })
                        .then((data) => {
                            const tableBody = document.querySelector("#data tbody");
                            tableBody.innerHTML = data.update_table;

                            // Reset file input value (clears selected files)
                            fileInput.value = "";
                        })
                        .catch((error) => {
                            console.error(error);
                        });
                });
            };
        }

// File validation function

