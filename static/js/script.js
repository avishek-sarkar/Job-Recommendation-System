function showError(message) {
    const flash = document.createElement('div');
    flash.className = 'alert error';
    flash.textContent = message;
    document.querySelector('.card').prepend(flash);
}

function validateFile(file) {
    if (!file) {
        showError("Please upload a PDF file.");
        return false;
    }

    if (!file.name.endsWith('.pdf')) {
        showError("The file is not in PDF format.");
        return false;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError("The file exceeds the 10 MB size limit.");
        return false;
    }

    return true;
}

function showUploading() {
    const file = document.getElementById('resume').files[0];
    if (!validateFile(file)) return false;

    document.getElementById('uploading-msg').style.display = 'block';
    return true;
}

function checkFileType(input) {
    const file = input.files[0];
    const fileNameDisplay = document.getElementById('filename-display');

    if (!validateFile(file)) {
        input.value = '';
        fileNameDisplay.textContent = '';
        return;
    }

    fileNameDisplay.textContent = `Selected file: ${file.name}`;
}

function clearFlashMessages() {
    document.querySelectorAll('.alert').forEach(el => el.remove());
    document.getElementById('uploading-msg').style.display = 'none';
}

// Theme toggle logic
function setTheme(mode) {
    if (mode === 'dark') {
        document.body.classList.add('dark-mode');
        document.getElementById('theme-toggle').textContent = '🌞';
    } else {
        document.body.classList.remove('dark-mode');
        document.getElementById('theme-toggle').textContent = '🌙';
    }
    localStorage.setItem('theme', mode);
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-mode');
    setTheme(isDark ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    toggleBtn.addEventListener('click', toggleTheme);

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
});
