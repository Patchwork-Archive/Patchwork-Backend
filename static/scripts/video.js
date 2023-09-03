function toggleDescription() {
    var description = document.getElementById("description");
    var toggleButton = document.getElementById("toggle-description");

    if (description.classList.contains("collapsed")) {
      description.classList.remove("collapsed");
      toggleButton.innerHTML = "Show Less";
      description.style.maxHeight = "none"; 
    } else {
      description.classList.add("collapsed");
      toggleButton.innerHTML = "Show More";
      description.style.maxHeight = "";
    }
}

function openInVLC(url) {
  // if platform is not Mobile or tablet
  if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))) {
    if(!confirm("This feature is mainly for mobile devices who can't view WEBM videos natively in their browser. We detected that you're not on a mobile device. Try anyways?")){
      return;
    }
  }
    window.location.href = 'vlc://' + url;
}

function getInfoJSON(cdn_url) {
  var request = new XMLHttpRequest();
  request.open('GET', cdn_url + '.info.json', true);
  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var data = JSON.parse(request.responseText);

      var title = document.getElementById("title");
      title.innerHTML = data.title;

      var description = document.getElementById("description");
      description.innerHTML = data.description;
      
      var channel_name = document.getElementById("channel_name");
      channel_name.innerHTML = data.uploader;

    } else {
      console.log("Error: " + request.status);
    }
  };
  request.onerror = function () {
    console.log("Error: " + request.status);
  };
  request.send();
}