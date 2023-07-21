function addPageParam(offset) {
    var currentURL = window.location.href;
    var pageNumber = 1;
    var urlParts = currentURL.split("?");
    var baseUrl = urlParts[0];
    var queryParams = {};
    if (urlParts.length > 1) {
      var queryString = urlParts[1];
      var paramPairs = queryString.split("&");
      paramPairs.forEach(function(pair) {
        var parts = pair.split("=");
        queryParams[parts[0]] = parts[1];
      });
  
      if (queryParams.hasOwnProperty("page")) {
        pageNumber = parseInt(queryParams["page"]) + offset;
        if (pageNumber < 1) {
          pageNumber = 1;
        }
      } else {
        pageNumber = 2;
      }
    } else {
      pageNumber = 2;
    }
    queryParams["page"] = pageNumber;
    var newURL = baseUrl + "?" + Object.keys(queryParams).map(function(key) {
      return key + "=" + queryParams[key];
    }).join("&");
  
    window.history.pushState({ path: newURL }, "", newURL);
    location.reload();
    window.scrollTo(0, 0);
  }
  