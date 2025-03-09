// JavaScript for the web application
document.addEventListener('DOMContentLoaded', function () {
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
    const startTranscriptionBtn = document.getElementById('start-transcription-btn');

    // Function to update status display
    function updateStatus() {
        fetch('/get_status', { timeout: 500 })  // Add a timeout to the fetch request
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
                        wave.style.animationDuration = '10s';
                    });

                    // Check less frequently when stable
                    if (window.statusInterval) clearInterval(window.statusInterval);
                    window.statusInterval = setInterval(updateStatus, 1000);
                } else {
                    connectionDot.style.backgroundColor = '#FF3B30'; // Red

                    // Update signal bars for unstable connection
                    const activeBarCount = Math.floor(Math.random() * 2) + 1; // 1 or 2 bars
                    updateSignalBars(activeBarCount);

                    // Update wave animation
                    waveContainer.style.opacity = '1';
                    document.querySelectorAll('.wave').forEach(wave => {
                        wave.style.animationDuration = '3s';
                    });

                    // Check more frequently when unstable
                    if (window.statusInterval) clearInterval(window.statusInterval);
                    window.statusInterval = setInterval(updateStatus, 500);
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

                // Show internet status
                if (!data.internet_accessible && !data.simulating) {
                    statusOverlay.textContent = 'No Internet Connection';
                    statusOverlay.classList.add('error');
                } else {
                    statusOverlay.classList.remove('error');
                }

                // Add this to display the transcription
                if (data.transcription) {
                    let transcriptionDisplay = document.getElementById('transcription-display');
                    if (transcriptionDisplay) {
                        // Get the current displayed text (if any)
                        const currentDisplayedText = transcriptionDisplay.querySelector('p') ? 
                            transcriptionDisplay.querySelector('p').textContent : '';
                        
                        // Only update if the transcription is different
                        if (data.transcription !== currentDisplayedText) {
                            // Clear existing content
                            transcriptionDisplay.innerHTML = '';
                            
                            // Create a new paragraph for the latest transcription
                            const transcriptionPara = document.createElement('p');
                            transcriptionPara.textContent = data.transcription;
                            transcriptionDisplay.appendChild(transcriptionPara);
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching status:', error);
                // If we can't even fetch status, we definitely have connection issues
                connectionDot.style.backgroundColor = '#FF3B30'; // Red
                statusOverlay.textContent = 'No Internet Connection';
                statusOverlay.classList.add('error');

                // Check more frequently when there's an error
                if (window.statusInterval) clearInterval(window.statusInterval);
                window.statusInterval = setInterval(updateStatus, 500);
            });
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
    window.statusInterval = setInterval(updateStatus, 1000);

    // Toggle feed button
    toggleBtn.addEventListener('click', function () {
        fetch('/toggle_feed')
            .then(response => response.json())
            .then(data => {
                updateStatus();
            })
            .catch(error => console.error('Error toggling feed:', error));
    });

    // Simulate button
    simulateBtn.addEventListener('click', function () {
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

    // Add this function to directly check network status from the browser
    function checkNetworkStatus() {
        if (!navigator.onLine) {
            connectionDot.style.backgroundColor = '#FF3B30'; // Red
            statusOverlay.textContent = 'No Internet Connection';
            statusOverlay.classList.add('error');

            // Force switch to backup feed
            liveVideoFeed.style.display = 'none';
            backupVideoFeed.style.display = 'block';
            backupAudio.play().catch(e => console.log('Audio play prevented by browser policy'));
        }
    }

    // Add event listeners for online/offline events
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', checkNetworkStatus);

    // Check network status every 500ms
    setInterval(checkNetworkStatus, 500);

    startTranscriptionBtn.addEventListener('click', function () {
        fetch('/start_transcription')
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
            })
            .catch(error => console.error('Error starting transcription:', error));
    });
}); 