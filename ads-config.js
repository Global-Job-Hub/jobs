// js/ads-config.js
function loadAds() {
    const adContainers = document.querySelectorAll('.ad-slot-placeholder');
    
    adContainers.forEach(container => {
        // REPLACE THE LINE BELOW WITH YOUR ACTUAL ADSTERRA SCRIPT CODE
        container.innerHTML = '';
        
        // Example if using an iframe or banner:
        // let script = document.createElement('script');
        // script.src = "//www.topcreativeformat.com/YOUR_AD_ID/invoke.js";
        // container.appendChild(script);
    });
}

// Run when the page loads
window.onload = loadAds;
