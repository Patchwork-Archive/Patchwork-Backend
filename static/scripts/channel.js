function addPageParam(offset) {
    let currentURL = window.location.href;
    let currentPage = 1; // Default to page 1 if no page parameter found
    const pageParam = new URLSearchParams(window.location.search).get("page");
    if (pageParam) {
      currentPage = parseInt(pageParam);
    }
    const newPage = Math.max(currentPage + offset, 1);
  
    let newURL = currentURL;
    if (currentURL.includes("?page=")) {
      newURL = currentURL.replace(/page=\d+/i, "page=" + newPage);
    } else {
      newURL += (currentURL.includes("?") ? "&" : "?") + "page=" + newPage;
    }
    window.location.href = newURL;
  }
  