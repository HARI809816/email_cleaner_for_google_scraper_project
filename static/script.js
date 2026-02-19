document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('uploadSection');
    const fileInput = document.getElementById('fileInput');
    const processingSection = document.getElementById('processingSection');
    const resultsSection = document.getElementById('resultsSection');
    const uploadSection = document.getElementById('uploadSection');

    // ──────────────────────────────────────────
    // Drag & Drop Handlers
    // ──────────────────────────────────────────
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.add('dragover'), false));
    ['dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.remove('dragover'), false));

    dropZone.addEventListener('drop', e => handleFiles(e.dataTransfer.files), false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', e => handleFiles(e.target.files));

    function handleFiles(files) {
        if (files.length > 0) uploadFile(files[0]);
    }

    // ──────────────────────────────────────────
    // Upload & Process
    // ──────────────────────────────────────────
    async function uploadFile(file) {
        // Animate out upload, show processing
        uploadSection.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => {
            uploadSection.style.display = 'none';
            processingSection.style.display = 'block';
            resultsSection.style.display = 'none';
        }, 280);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/process-excel/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Processing failed');

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during processing. Please try again.');
            uploadSection.style.display = 'block';
            uploadSection.style.animation = 'fadeUp 0.4s ease both';
            processingSection.style.display = 'none';
        }
    }

    // ──────────────────────────────────────────
    // Display Results
    // ──────────────────────────────────────────

    // Per-metric icon & highlight config
    const cardConfig = {
        'Sheet 2 Total (All Clean)': { emoji: '🧹', highlight: false },
        'Sheet 3 (Similar Name Emails)': { emoji: '👥', highlight: false },
        'Sheet 4 (Name Found)': { emoji: '✅', highlight: false },
        'Sheet 4 (Name Blank)': { emoji: '⚠️', highlight: false },
        'Sheet 5 (Email Name Extracted)': { emoji: '🔍', highlight: false },
        'Sheet 6 Final Combined': { emoji: '🏆', highlight: true },
    };

    function displayResults(data) {
        processingSection.style.display = 'none';
        resultsSection.style.display = 'block';
        resultsSection.style.animation = 'fadeIn 0.5s ease both';

        const statsContainer = document.getElementById('statsContainer');
        statsContainer.innerHTML = '';

        data.stats.forEach((stat, index) => {
            const cfg = cardConfig[stat.Metric] || { emoji: '', highlight: false };
            const card = document.createElement('div');
            card.className = 'stat-card' + (cfg.highlight ? ' stat-card--highlight' : '');

            // Placeholder while counting animation runs
            card.innerHTML = `
                <div class="stat-value" data-target="${stat.Count}">0</div>
                <div class="stat-label">${cfg.emoji ? cfg.emoji + ' ' : ''}${stat.Metric}</div>
            `;
            statsContainer.appendChild(card);

            // Staggered entrance: each card appears 80ms after the previous
            setTimeout(() => {
                card.classList.add('visible');
                // Animate count up after card appears
                setTimeout(() => animateCount(card.querySelector('.stat-value'), stat.Count), 200);
            }, index * 80);
        });

        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.href = `/download/${data.uid}`;
    }

    // ──────────────────────────────────────────
    // Count-Up Animation
    // ──────────────────────────────────────────
    function animateCount(el, target) {
        if (target === 0) return;
        const duration = 900; // ms
        const start = performance.now();

        function step(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target).toLocaleString();
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }
});

/* Inject fadeOut keyframe dynamically so we can use it inline */
const style = document.createElement('style');
style.textContent = `@keyframes fadeOut { to { opacity: 0; transform: translateY(-12px); } }`;
document.head.appendChild(style);
