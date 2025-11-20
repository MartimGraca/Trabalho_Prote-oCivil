// Simple JavaScript for basic interactivity

// Filter functionality
const filterButtons = document.querySelectorAll('.filter-btn');
const alertCards = document.querySelectorAll('.alert-card');

filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons
        filterButtons.forEach(btn => btn.classList.remove('active'));
        // Add active class to clicked button
        button.classList.add('active');
        
        const filterText = button.textContent.toLowerCase();
        
        // Filter alerts
        alertCards.forEach(card => {
            if (filterText === 'todos') {
                card.style.display = 'block';
            } else {
                const severity = card.className.match(/severity-(\w+)/)[1];
                const severityMap = {
                    'critical': 'crítico',
                    'high': 'alto',
                    'medium': 'médio',
                    'low': 'baixo'
                };
                
                if (severityMap[severity] === filterText) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            }
        });
    });
});

// Search functionality
const searchInput = document.querySelector('.search-input');

searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    
    alertCards.forEach(card => {
        const title = card.querySelector('.alert-title').textContent.toLowerCase();
        const description = card.querySelector('.alert-description').textContent.toLowerCase();
        const location = card.querySelector('.alert-location span').textContent.toLowerCase();
        const category = card.querySelector('.alert-category span').textContent.toLowerCase();
        
        if (title.includes(searchTerm) || 
            description.includes(searchTerm) || 
            location.includes(searchTerm) ||
            category.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // If search is cleared and no filter is active except "Todos"
    if (searchTerm === '') {
        const activeFilter = document.querySelector('.filter-btn.active');
        if (activeFilter && activeFilter.textContent.toLowerCase() !== 'todos') {
            activeFilter.click(); // Re-apply the active filter
        }
    }
});

// Alert card click handler
alertCards.forEach(card => {
    card.addEventListener('click', () => {
        // Add a simple animation effect
        card.style.transform = 'scale(0.98)';
        setTimeout(() => {
            card.style.transform = '';
        }, 100);
        
        // In a real application, this would open a detailed view
        console.log('Alert clicked:', card.querySelector('.alert-title').textContent);
    });
});

// Update time display (simulate real-time updates)
function updateTimestamps() {
    const timeElements = document.querySelectorAll('.alert-time');
    // This is a simple example - in a real app, you'd calculate actual time differences
    // For now, we'll just add a visual indicator that times are "live"
    timeElements.forEach(el => {
        el.classList.add('loading');
        setTimeout(() => {
            el.classList.remove('loading');
        }, 1000);
    });
}

// Update timestamps every minute
setInterval(updateTimestamps, 60000);

// Mobile menu toggle (if needed in future)
function initMobileMenu() {
    const header = document.querySelector('.header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll <= 0) {
            header.style.transform = 'translateY(0)';
            return;
        }
        
        if (currentScroll > lastScroll && currentScroll > 100) {
            // Scrolling down
            header.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            header.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Portal de Alertas - Proteção Civil loaded');
    initMobileMenu();
    
    // Add smooth reveal animation to cards
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 50);
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Set initial state for animation
    alertCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
});
