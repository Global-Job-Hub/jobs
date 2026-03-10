/**
 * Global Job Hub - Centralized Ad Loader
 * This script finds all '.ad-slot-placeholder' divs and 
 * injects your Adsterra units into them automatically.
 */
document.addEventListener("DOMContentLoaded", function() {
    const placeholders = document.querySelectorAll('.ad-slot-placeholder');
    
    placeholders.forEach((slot, index) => {
        // 1. Clear the "Loading..." text
        slot.innerHTML = '';
        slot.style.border = 'none'; // Remove the dashed border once loaded

        /**
         * --- HOW TO ADD YOUR ADSTERRA CODE ---
         * Adsterra usually gives you two parts:
         * 1. A Script Source URL (e.g., //www.topcreativeformat.com/xyz/invoke.js)
         * 2. A Configuration Variable (atob(...) logic)
         */

        try {
            // EXAMPLE: If your Adsterra code looks like a standard banner script:
            let adScript = document.createElement('script');
            adScript.type = 'text/javascript';
            
            // REPLACE THE URL BELOW with your real Adsterra 'invoke.js' URL
            adScript.src = '//www.topcreativeformat.com/YOUR_AD_ID_HERE/invoke.js'; 
            
            // Append the script to the slot
            slot.appendChild(adScript);
            
            console.log(`Ad Slot ${index + 1} initialized.`);
        } catch (err) {
            console.error("Ad Loader Error:", err);
            slot.innerHTML = '<p style="font-size:10px; color:#ccc;">Notice: Ad disabled</p>';
        }
    });
});
