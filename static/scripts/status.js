setTimeout(function() {
    location.reload();
  }, 15000);
  var countdown = 15;

function updateCountdown() {
    var countdownElement = document.getElementById("countdown");
    countdownElement.textContent = countdown;
    countdown--;
    if (countdown < 0) {
      clearInterval(timer);
    }
}

var timer = setInterval(updateCountdown, 1000);