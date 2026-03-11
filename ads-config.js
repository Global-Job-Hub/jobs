/**
 * Global Job Hub - Centralized Ad Loader
 */
document.addEventListener("DOMContentLoaded", function() {
    const placeholders = document.querySelectorAll('.ad-slot-placeholder');
    
    placeholders.forEach((slot, index) => {
        // Clear previous content
        slot.innerHTML = '';
        slot.style.border = 'none';
        slot.style.background = 'transparent';

        try {
            // Check if this slot needs specific Adsterra options (e.g. 300x250)
            // You can customize this logic based on data-attributes if needed
            let adScript = document.createElement('script');
            adScript.type = 'text/javascript';
            
            /* If you want to use ONE script for all slots in the Job Details,
               paste your primary Adsterra 'invoke.js' URL here.
            */
            adScript.src = 'https://www.highperformanceformat.com/67ea727e78dcc41b8d65c7c29c63ea48/invoke.js'; 
            
            slot.appendChild(adScript);
            console.log(`Ad Slot ${index + 1} injected.`);
        } catch (err) {
            console.error("Ad Loader Error:", err);
        }
    });
});
