document.addEventListener('DOMContentLoaded', () => {
    // API Configuration
    const API_URL = 'http://localhost:8000/api/compare';

    // UI Elements
    const form = document.getElementById('compare-form');
    const submitBtn = document.getElementById('submit-btn');
    const statusMessage = document.getElementById('status-message');
    const errorMessage = document.getElementById('error-message');
    
    // File inputs and their UI wrappers
    const inputs = [
        {
            input: document.getElementById('file_year1'),
            dropzone: document.getElementById('dropzone-1'),
            nameDisplay: document.getElementById('name-1')
        },
        {
            input: document.getElementById('file_year2'),
            dropzone: document.getElementById('dropzone-2'),
            nameDisplay: document.getElementById('name-2')
        }
    ];

    // Setup drag & drop and file selection for each input
    inputs.forEach(item => {
        const { input, dropzone, nameDisplay } = item;

        // Click on dropzone triggers file input
        dropzone.addEventListener('click', () => {
            input.click();
        });

        // File selection event
        input.addEventListener('change', (e) => {
            handleFileSelection(e.target.files, dropzone, nameDisplay);
        });

        // Drag and drop events
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
            
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                // Update the file input's files
                input.files = e.dataTransfer.files;
                handleFileSelection(e.dataTransfer.files, dropzone, nameDisplay);
            }
        });
    });

    function handleFileSelection(files, dropzone, nameDisplay) {
        if (files && files.length > 0) {
            const file = files[0];
            nameDisplay.textContent = file.name;
            dropzone.classList.add('has-file');
            
            // Basic validation
            if (!file.name.toLowerCase().endsWith('.csv')) {
                showError(`El archivo "${file.name}" no parece ser un CSV válido.`);
                dropzone.classList.remove('has-file');
                nameDisplay.textContent = '';
                // Optional: clear the input
            } else {
                hideError();
            }
        } else {
            nameDisplay.textContent = '';
            dropzone.classList.remove('has-file');
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }

    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            statusMessage.classList.remove('hidden');
            hideError();
        } else {
            submitBtn.disabled = false;
            statusMessage.classList.add('hidden');
        }
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const file1 = inputs[0].input.files[0];
        const file2 = inputs[1].input.files[0];

        if (!file1 || !file2) {
            showError("Por favor, selecciona ambos archivos CSV antes de continuar.");
            return;
        }

        setLoading(true);

        // Prepare FormData
        const formData = new FormData();
        formData.append('file_year1', file1);
        formData.append('file_year2', file2);

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorDetails = "Error al procesar la solicitud.";
                try {
                    const errorJson = await response.json();
                    if (errorJson.detail) {
                        errorDetails = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
                    }
                } catch (e) {
                    // Si no es JSON el error
                    errorDetails = `Error HTTP: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorDetails);
            }

            // Successfully received the ZIP file
            const blob = await response.blob();
            
            // Extract filename from Content-Disposition header if possible
            let filename = "comparacion_saldos.zip";
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Reset form
            form.reset();
            inputs.forEach(item => {
                item.nameDisplay.textContent = '';
                item.dropzone.classList.remove('has-file');
            });

        } catch (error) {
            console.error('Error during API call:', error);
            showError(error.message || "No se pudo conectar con el servidor. Verifica que la API esté en ejecución en localhost:8000.");
        } finally {
            setLoading(false);
        }
    });

    // Prevent default behaviors for document drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.body.addEventListener(eventName, e => e.preventDefault());
    });
});
