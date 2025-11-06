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

// ==================== Developer Info Page Functions ====================
// GitHub usernames configuration
const developers = [
    { username: 'avishek-sarkar', role: 'Developer' },
    { username: 'prantic007', role: 'Developer' }
];

async function fetchGitHubProfile(username) {
    try {
        const response = await fetch(`https://api.github.com/users/${username}`);
        if (!response.ok) throw new Error('Failed to fetch profile');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${username}:`, error);
        return null;
    }
}

function createDevCard(profile, role) {
    if (!profile) {
        return `
            <div class="dev-card">
                <div class="error">Failed to load developer information</div>
            </div>
        `;
    }

    return `
        <div class="dev-card">
            <div class="dev-profile">
                <img src="${profile.avatar_url}" alt="${profile.name || profile.login}" class="dev-avatar">
                <div class="dev-info">
                    <h2>${profile.name || profile.login}</h2>
                    <p class="username">@${profile.login} • ${role}</p>
                </div>
            </div>
            <p class="dev-bio">${profile.bio || 'Passionate developer building innovative solutions.'}</p>
            <div class="dev-stats">
                <div class="stat">
                    <div class="stat-value">${profile.public_repos}</div>
                    <div class="stat-label">Repositories</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${profile.followers}</div>
                    <div class="stat-label">Followers</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${profile.following}</div>
                    <div class="stat-label">Following</div>
                </div>
            </div>
            <div class="dev-links">
                <a href="${profile.html_url}" target="_blank" rel="noopener noreferrer" class="dev-btn">
                    View GitHub Profile
                </a>
            </div>
        </div>
    `;
}

async function loadDevelopers() {
    const container = document.getElementById('developers-content');
    
    if (!container) return; // Exit if we're not on developer page
    
    try {
        const profiles = await Promise.all(
            developers.map(dev => fetchGitHubProfile(dev.username))
        );
        
        const cardsHTML = profiles.map((profile, index) => 
            createDevCard(profile, developers[index].role)
        ).join('');
        
        container.innerHTML = `<div class="developers-grid">${cardsHTML}</div>`;
    } catch (error) {
        container.innerHTML = `
            <div class="error">
                Failed to load developer information. Please try again later.
            </div>
        `;
    }
}

// ==================== Theme Toggle Functionality ====================

function setTheme(mode) {
    if (mode === 'dark') {
        document.body.classList.add('dark-mode');
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) toggleBtn.textContent = '🌞';
    } else {
        document.body.classList.remove('dark-mode');
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) toggleBtn.textContent = '🌙';
    }
    localStorage.setItem('theme', mode);
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-mode');
    setTheme(isDark ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
    
    // Load developers if on developer page
    loadDevelopers();
});
