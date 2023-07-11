---
title:  ##
image:  '/otterferret1.jpg'
---
gfdf


{{ define "main" }}
  <h1>File Upload</h1>
  {{ if .Params.file }}
    <p>Uploaded file: {{ .Params.file }}</p>
    <p>Processing the uploaded file...</p>
    <div id="response"></div>
    <script>
      function uploadFile() {
        var fileInput = document.getElementById("file");
        var file = fileInput.files[0];
        var formData = new FormData();
        formData.append("file", file);
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);
        xhr.onload = function () {
          if (xhr.status === 200) {
            document.getElementById("response").innerHTML = "Your loop is ready!";
            var downloadButton = document.createElement("a");
            downloadButton.setAttribute("href", "/download/generated_loop.mp3");
            downloadButton.setAttribute("download", "generated_loop.mp3");
            downloadButton.innerHTML = "Download";
            document.getElementById("response").appendChild(downloadButton);
          } else {
            document.getElementById("response").innerHTML = "Error occurred during file upload and processing.";
          }
        };
        xhr.send(formData);
      }
      uploadFile();
    </script>
  {{ else }}
    <p>No file uploaded.</p>
  {{ end }}
{{ end }}
