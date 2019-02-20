var progressInterval;
function $(id) {
  return document.getElementById(id);
}
function setMode(which) {
  if (which == "final") {
    show("pending", false);
    show("busy", false);
  } else {
    var other = (which == "pending") ? "busy" : "pending";
    show(other, false);
  }
  show(which, true);
}
function show(id, display) {
  var val = (display) ? "inherit" : "none";
  console.log("Setting display of " + id + " to: " + val);
  $(id).style.display = val;
}
function updateProgress() {
  var p = $("progress")
  p.n += p.delta;
  if (p.n > 80) {
    p.delta = (p.n > 93) ? .4 : 1.2;
  }
  if (p.n > 99) {
    p.n = 100;
    windows.clearInterval(progressInterval);
  }
  p.style.width = Math.round(p.n) + "%";
}
function refresh() {
  var p = $("progress");
  p.n = 1;
  p.delta = 8;
  p.style.width = "1%";
  setMode("busy");
  progressInterval = window.setInterval(updateProgress, 1000);
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4) {
      window.clearInterval(progressInterval);
      if (this.status == 200) {
        var i = this.responseURL.indexOf("/resp/");
        if (i == -1) {
          setMode("pending");
        } else {
          $("final_url").innerHTML = this.responseURL.substring(i);
          $("response").innerHTML = this.responseText;
          setMode("final");
        }
      } else {
        $("outcome").innerHTML = this.responseText;
        setMode("final");
      }
    }
  };
  xhttp.open("GET", rootLoc, true);
  xhttp.send();
}
