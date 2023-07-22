const videoPlayer = document.getElementById('custom-video-player');
const playPauseButton = document.getElementById('play-pause-button');
const playIcon = document.getElementById('play-icon');
const pauseIcon = document.getElementById('pause-icon');
const volumeSlider = document.getElementById('volume-slider');
const skipButton = document.getElementById('skip-button');

playPauseButton.addEventListener('click', togglePlayPause);
volumeSlider.addEventListener('input', updateVolume);
skipButton.addEventListener('click', fetchAndDisplayRandomVideo);

function togglePlayPause() {
  if (videoPlayer.paused) {
    videoPlayer.play();
    playIcon.style.display = 'none';
    pauseIcon.style.display = 'inline';
  } else {
    videoPlayer.pause();
    playIcon.style.display = 'inline';
    pauseIcon.style.display = 'none';
  }
}

function updateVolume() {
  videoPlayer.volume = volumeSlider.value;
}