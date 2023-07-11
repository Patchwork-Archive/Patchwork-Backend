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