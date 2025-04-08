// Common JavaScript functions for all pages

// API Base URL - change this to your production URL when deploying
const API_BASE_URL = '/api/v1';

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Create content
    const content = document.createElement('div');
    content.className = 'notification-content';
    
    // Add icon based on type
    let icon = '';
    switch(type) {
        case 'success':
            icon = '✓';
            break;
        case 'error':
            icon = '✗';
            break;
        default:
            icon = 'ℹ';
    }
    
    // Build content
    content.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;
    
    // Create progress bar
    const progress = document.createElement('div');
    progress.className = 'notification-progress';
    const progressInner = document.createElement('div');
    progressInner.className = 'notification-progress-inner';
    progress.appendChild(progressInner);
    
    // Add elements to notification
    notification.appendChild(content);
    notification.appendChild(progress);
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
    
    return notification;
}

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('token') !== null;
    
    // If we have a logout button, add logout functionality
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('token');
            showNotification('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        });
    }
    
    // Check if we need to fetch user info
    const userNameElement = document.getElementById('userName');
    const userCreditsElement = document.getElementById('userCredits');
    
    if (isLoggedIn && (userNameElement || userCreditsElement)) {
        fetchUserInfo();
    }
    
    // Common function to fetch user information
    async function fetchUserInfo() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch user info');
            }
            
            const userData = await response.json();
            
            if (userNameElement) {
                userNameElement.textContent = userData.email.split('@')[0];
            }
            
            if (userCreditsElement) {
                userCreditsElement.textContent = userData.credits;
            }
            
        } catch (error) {
            console.error('Error fetching user info:', error);
            showNotification('Error loading user data', 'error');
        }
    }
    
    // Authentication guard - if this is a protected page and user is not logged in
    const protectedPages = ['dashboard.html', 'history.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage) && !isLoggedIn) {
        showNotification('Please log in to access this page', 'info');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
});