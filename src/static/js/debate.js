document.addEventListener('DOMContentLoaded', () => {
    // Get debate ID from URL query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const debateId = urlParams.get('id');
    
    if (!debateId) {
        showError('No debate ID provided.');
        return;
    }
    
    // Fetch debate details
    fetchDebateDetails(debateId);
    
    // Setup back button to remember search query if present
    const backButton = document.getElementById('back-button');
    const searchQuery = urlParams.get('q');
    if (searchQuery) {
        backButton.href = `/?q=${encodeURIComponent(searchQuery)}`;
    }
});

async function fetchDebateDetails(debateId) {
    try {
        const response = await fetch(`/api/debate/${debateId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch debate details: ${response.status} ${response.statusText}`);
        }
        
        const debate = await response.json();
        displayDebateDetails(debate);
    } catch (error) {
        console.error('Error fetching debate details:', error);
        showError(error.message);
    }
}

function displayDebateDetails(debate) {
    // Clone the template
    const template = document.getElementById('debate-template');
    const debateElement = template.content.cloneNode(true);
    
    // Fill in the details
    debateElement.getElementById('debate-title').textContent = debate.tldr;
    debateElement.getElementById('debate-id').textContent = debate.id;
    debateElement.getElementById('debate-date').textContent = formatDate(debate.created_at);
    
    // Set summary, handling empty or null cases
    const summaryElement = debateElement.getElementById('debate-summary');
    summaryElement.textContent = debate.summary || 'No summary available.';
    
    // Set OCR text, handling empty or null cases
    const ocrElement = debateElement.getElementById('debate-ocr');
    if (debate.ocr_text && debate.ocr_text.trim()) {
        ocrElement.textContent = debate.ocr_text;
    } else {
        ocrElement.textContent = '';  // Will trigger the empty ::before content
    }
    
    // Handle image loading with fallbacks
    const imageElement = debateElement.getElementById('debate-image');
    if (debate.image_path) {
        setupImageWithFallbacks(imageElement, debate.image_path, debate.tldr);
    } else {
        imageElement.src = '/static/images/placeholder.svg';
        imageElement.alt = 'No image available';
    }
    
    // Add score badge if available
    if (typeof debate.score === 'number') {
        const scoreBadgeContainer = debateElement.getElementById('score-badge-container');
        addScoreBadge(scoreBadgeContainer, debate.score);
    }
    
    // Setup action buttons
    const editButton = debateElement.getElementById('edit-debate');
    editButton.addEventListener('click', () => {
        // Placeholder for edit functionality
        alert('Edit functionality not implemented yet.');
    });
    
    const deleteButton = debateElement.getElementById('delete-debate');
    deleteButton.addEventListener('click', () => {
        if (confirm(`Are you sure you want to delete "${debate.tldr}"?`)) {
            // Placeholder for delete functionality
            alert('Delete functionality not implemented yet.');
        }
    });
    
    // Clear loading state and display the debate
    const container = document.getElementById('debate-container');
    container.className = ''; // Remove loading class
    container.innerHTML = '';
    container.appendChild(debateElement);
    
    // Set page title
    document.title = `${debate.tldr} - Debate Details`;
}

function setupImageWithFallbacks(imageElement, imagePath, altText) {
    const filename = imagePath.split('/').pop();
    
    // Build a list of paths to try, in order of preference
    const imagePathsToTry = [
        `/${imagePath}`,                      // /static/uploads/filename.jpg
        `/static/uploads/${filename}`,        // /static/uploads/filename.jpg (direct)
        `/uploads/${filename}`,               // /uploads/filename.jpg (alternative mount)
        `/src/static/uploads/${filename}`,    // /src/static/uploads/filename.jpg
        `/static/images/placeholder.svg`      // fallback
    ];
    
    // Set the first path to try
    imageElement.alt = altText;
    imageElement.src = imagePathsToTry[0];
    
    // Current path index for fallbacks
    let currentPathIndex = 0;
    
    // Setup error handling to try alternative paths
    imageElement.onerror = function() {
        console.warn(`Failed to load image from ${this.src}`);
        
        if (currentPathIndex < imagePathsToTry.length - 1) {
            // Try next path
            currentPathIndex++;
            const nextPath = imagePathsToTry[currentPathIndex];
            console.log(`Trying alternative path: ${nextPath}`);
            this.src = nextPath;
        } else {
            // All paths failed, use placeholder
            console.error(`All image paths failed, using placeholder`);
            this.src = '/static/images/placeholder.svg';
            this.alt = 'Image not available';
            this.onerror = null; // Prevent further errors
        }
    };
    
    // Setup success handler
    imageElement.onload = function() {
        console.log(`Successfully loaded image from: ${this.src}`);
    };
}

function addScoreBadge(container, score) {
    if (score <= 0) return; // Don't show zero scores
    
    const scorePercent = Math.round(score * 100);
    const scoreClass = scorePercent > 70 ? 'high' : scorePercent > 40 ? 'medium' : 'low';
    
    const badge = document.createElement('span');
    badge.className = `score-badge ${scoreClass}`;
    badge.textContent = `${scorePercent}%`;
    
    container.appendChild(badge);
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

function showError(message) {
    // Hide loading container
    document.getElementById('debate-container').style.display = 'none';
    
    // Show error container
    const errorContainer = document.getElementById('error-container');
    errorContainer.style.display = 'block';
    
    // Set error message
    document.getElementById('error-message').textContent = message;
} 