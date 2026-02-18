document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('uploadSection');
    const fileInput = document.getElementById('fileInput');
    const processingSection = document.getElementById('processingSection');
    const resultsSection = document.getElementById('resultsSection');
    const uploadSection = document.getElementById('uploadSection');

    // Drag & Drop Handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }

    async function uploadFile(file) {
        // UI Transition: Show Processing
        uploadSection.style.display = 'none';
        processingSection.style.display = 'block';
        resultsSection.style.display = 'none';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/process-excel/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Processing failed');
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during processing. Please try again.');
            // Reset UI
            uploadSection.style.display = 'block';
            processingSection.style.display = 'none';
        }
    }

    function displayResults(data) {
        // Hide Processing, Show Results
        processingSection.style.display = 'none';
        resultsSection.style.display = 'block';

        // Populate Stats
        const statsContainer = document.getElementById('statsContainer');
        statsContainer.innerHTML = '';

        data.stats.forEach(stat => {
            const card = document.createElement('div');
            card.className = 'stat-card';
            card.innerHTML = `
                <div class="stat-value">${stat.Count}</div>
                <div class="stat-label">${stat.Metric}</div>
            `;
            statsContainer.appendChild(card);
        });

        // Setup Download Link
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.href = `/download/${data.uid}`;
        downloadBtn.innerHTML = `<span>Download Processed File</span> <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>`;
    }
});
