document.addEventListener('DOMContentLoaded', () => {
    // API Configuration
    const API_URL = 'http://10.6.149.155:8075/api/compare';

    // UI Elements
    const form = document.getElementById('compare-form');
    const submitBtn = document.getElementById('submit-btn');
    const errorMessage = document.getElementById('error-message');
    
    // File inputs and their UI wrappers
    const inputs = [
        {
            input: document.getElementById('file_year1'),
            dropzone: document.getElementById('dropzone-1'),
            nameDisplay: document.getElementById('name-1'),
            removeBtn: document.getElementById('remove-1')
        },
        {
            input: document.getElementById('file_year2'),
            dropzone: document.getElementById('dropzone-2'),
            nameDisplay: document.getElementById('name-2'),
            removeBtn: document.getElementById('remove-2')
        }
    ];

    // Setup drag & drop and file selection for each input
    inputs.forEach(item => {
        const { input, dropzone, nameDisplay, removeBtn } = item;

        // Note: We don't add a click listener to dropzone because the native 
        // <label for="..."> already handles opening the file dialog.
        // Adding one would cause a double-click bug.

        // Remove button event
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            input.value = '';
            handleFileSelection([], dropzone, nameDisplay);
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
            submitBtn.textContent = 'Curando registros...';
            hideError();
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Proceder a la Comparación';
        }
    }

    // ---- Modal helpers ----
    const activeObjectUrls = new Set();

    function createModalElements() {
        let backdrop = document.getElementById('modal-backdrop');
        if (backdrop) return backdrop;

        backdrop = document.createElement('div');
        backdrop.id = 'modal-backdrop';
        backdrop.className = 'modal-backdrop';
        backdrop.setAttribute('role', 'presentation');

        const dialog = document.createElement('div');
        dialog.className = 'modal-dialog';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');

        const header = document.createElement('div');
        header.className = 'modal-header';

        const title = document.createElement('div');
        title.className = 'modal-title';
        title.textContent = 'Archivos generados';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'modal-close';
        closeBtn.innerHTML = '✕';
        closeBtn.type = 'button';
        closeBtn.addEventListener('click', closeModal);

        header.appendChild(title);
        header.appendChild(closeBtn);

        const body = document.createElement('div');
        body.className = 'modal-body';

        dialog.appendChild(header);
        dialog.appendChild(body);
        backdrop.appendChild(dialog);

        backdrop.addEventListener('click', (ev) => {
            if (ev.target === backdrop) closeModal();
        });

        function onKey(e) {
            if (e.key === 'Escape') closeModal();
        }
        backdrop._onKey = onKey;
        document.addEventListener('keydown', onKey);

        return backdrop;
    }

    function getFileMeta(fileName) {
        const normalized = (fileName || '').toLowerCase();

        if (normalized.includes('completa') || normalized.includes('completo')) {
            return {
                title: 'Saldos completos',
                description: 'Incluye cuentas nuevas, vigentes y cerradas.'
            };
        }

        if (normalized.includes('existentes')) {
            return {
                title: 'Comparacion existentes',
                description: 'Incluye solo cuentas vigentes en ambos años.'
            };
        }

        return {
            title: fileName,
            description: 'Archivo generado por el comparador.'
        };
    }

    function showModal(files) {
        const backdrop = createModalElements();
        const body = backdrop.querySelector('.modal-body');

        body.innerHTML = '';
        const list = document.createElement('div');
        list.className = 'download-list';
        body.appendChild(list);

        files.forEach(file => {
            const { name, mime, content_base64 } = file;
            const meta = getFileMeta(name);
            // decode base64
            const binaryString = atob(content_base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
            const blob = new Blob([bytes], { type: mime });
            const url = window.URL.createObjectURL(blob);
            activeObjectUrls.add(url);

            // Row container
            const row = document.createElement('div');
            row.className = 'file-row';
            row.setAttribute('role', 'group');
            row.setAttribute('aria-label', name);

            // Left: icon + name
            const left = document.createElement('div');
            left.className = 'file-left';

            const icon = document.createElement('div');
            icon.className = 'file-icon';
            // small SVG icon for xlsx (simple shape)
            icon.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.2"/><path d="M7 8h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M7 12h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

            const titleEl = document.createElement('div');
            titleEl.className = 'file-title';
            titleEl.textContent = meta.title || name;

            const descEl = document.createElement('div');
            descEl.className = 'file-description';
            descEl.textContent = meta.description;

            left.appendChild(icon);
            left.appendChild(titleEl);
            left.appendChild(descEl);

            // Right: download button
            const btn = document.createElement('a');
            btn.className = 'btn-download';
            // Keep visual button consistent with .btn-primary colors
            btn.classList.add('btn-primary');
            btn.href = url;
            btn.download = name;
            btn.textContent = 'Descargar';

            btn.addEventListener('click', () => setTimeout(() => {
                window.URL.revokeObjectURL(url);
                activeObjectUrls.delete(url);
            }, 10000));

            row.appendChild(left);
            row.appendChild(btn);
            list.appendChild(row);
        });

        if (!document.getElementById('modal-backdrop')) {
            document.body.appendChild(backdrop);
        }

        const closeBtn = backdrop.querySelector('.modal-close');
        if (closeBtn) closeBtn.focus();

        document.body.classList.add('modal-open');
    }

    function closeModal() {
        activeObjectUrls.forEach(url => {
            try { window.URL.revokeObjectURL(url); } catch (e) {}
        });
        activeObjectUrls.clear();

        const backdrop = document.getElementById('modal-backdrop');
        if (!backdrop) return;

        if (backdrop._onKey) document.removeEventListener('keydown', backdrop._onKey);

        backdrop.remove();
        document.body.classList.remove('modal-open');
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

            // Successfully received JSON with both Excel files encoded in base64
            const json = await response.json();

            // Mostrar modal centrado con los archivos
            showModal(json.files);

            // Reset form (we keep the download links visible)
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
