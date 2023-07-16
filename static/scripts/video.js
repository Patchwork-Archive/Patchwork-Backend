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
      
      var channel_name = document.getElementById("channel-name");
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