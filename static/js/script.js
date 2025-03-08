// JavaScript for the web application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Web application loaded successfully!');
    
    // Get DOM elements
    const toggleBtn = document.getElementById('toggle-btn');
    const simulateBtn = document.getElementById('simulate-btn');
    const statusOverlay = document.getElementById('status-overlay');
    const feedStatus = document.getElementById('feed-status');
    const connectionDot = document.getElementById('connection-dot');
    const liveVideoFeed = document.getElementById('live-video-feed');
    const backupVideoFeed = document.getElementById('backup-video-feed');
    const backupAudio = document.getElementById('backup-audio');
    const signalBars = document.querySelectorAll('.signal-bar');
    const waveContainer = document.getElementById('wave-container');
    
    // Function to update status display
    function updateStatus() {
        fetch('/get_status')
            .then(response => response.json())
            .then(data => {
                // Update connection status
                if (data.connection === 'stable') {
                    connectionDot.style.backgroundColor = '#34C759'; // Green
                    
                    // Update signal bars for stable connection
                    const activeBarCount = Math.floor(Math.random() * 2) + 3; // 3 or 4 bars
                    updateSignalBars(activeBarCount);
                    
                    // Update wave animation
                    waveContainer.style.opacity = '0.5';
                    document.querySelectorAll('.wave').forEach(wave => {
                        wave.style.animationDuration = '10s, 8s, 6s';
                    });
                } else {
                    connectionDot.style.backgroundColor = '#FF3B30'; // Red
                    
                    // Update signal bars for unstable connection
                    const activeBarCount = Math.floor(Math.random() * 2) + 1; // 1 or 2 bars
                    updateSignalBars(activeBarCount);
                    
                    // Update wave animation
                    waveContainer.style.opacity = '1';
                    document.querySelectorAll('.wave').forEach(wave => {
                        wave.style.animationDuration = '3s, 2.5s, 2s';
                    });
                }
                
                // Update feed status
                feedStatus.textContent = data.current_feed.charAt(0).toUpperCase() + data.current_feed.slice(1);
                statusOverlay.textContent = data.current_feed === 'live' ? 'Live Feed' : 'Backup Feed';
                
                // Update video visibility
                if (data.current_feed === 'live') {
                    liveVideoFeed.style.display = 'block';
                    backupVideoFeed.style.display = 'none';
                    backupAudio.pause();
                } else {
                    liveVideoFeed.style.display = 'none';
                    backupVideoFeed.style.display = 'block';
                    backupAudio.play().catch(e => console.log('Audio play prevented by browser policy'));
                }
            })
            .catch(error => console.error('Error fetching status:', error));
    }
    
    function updateSignalBars(activeCount) {
        signalBars.forEach((bar, index) => {
            if (index < activeCount) {
                bar.classList.add('active');
            } else {
                bar.classList.remove('active');
            }
        });
    }
    
    // Start periodic status updates
    updateStatus();
    setInterval(updateStatus, 1000);
    
    // Toggle feed button
    toggleBtn.addEventListener('click', function() {
        fetch('/toggle_feed')
            .then(response => response.json())
            .then(data => {
                updateStatus();
            })
            .catch(error => console.error('Error toggling feed:', error));
    });
    
    // Simulate button
    simulateBtn.addEventListener('click', function() {
        fetch('/simulate_rapid_switching')
            .then(response => response.json())
            .then(data => {
                if (data.simulating) {
                    simulateBtn.textContent = "Stop Simulation";
                    simulateBtn.classList.add("active-simulation");
                    
                    // Add visual effects for the simulation
                    const signalMeter = document.getElementById('signal-meter');
                    signalMeter.classList.add('simulating');
                    waveContainer.classList.add('simulating');
                    
                    // Clear the interval after 20 seconds
                    setTimeout(() => {
                        fetch('/simulate_rapid_switching').then(() => {
                            simulateBtn.textContent = "Simulate Instability";
                            simulateBtn.classList.remove("active-simulation");
                            signalMeter.classList.remove('simulating');
                            waveContainer.classList.remove('simulating');
                        });
                    }, 20000);
                } else {
                    simulateBtn.textContent = "Simulate Instability";
                    simulateBtn.classList.remove("active-simulation");
                    document.getElementById('signal-meter').classList.remove('simulating');
                    waveContainer.classList.remove('simulating');
                }
            })
            .catch(error => console.error('Error with simulation:', error));
    });
}); 