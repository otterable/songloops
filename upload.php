<?php
// Check if a file was uploaded
if ($_FILES['file']['error'] === UPLOAD_ERR_OK) {
    // Set the upload directory
    $uploadDir = 'uploads/';

    // Generate a unique filename
    $filename = uniqid() . '_' . basename($_FILES['file']['name']);
    
    // Set the path for saving the uploaded file
    $uploadPath = $uploadDir . $filename;

    // Move the uploaded file to the designated directory
    if (move_uploaded_file($_FILES['file']['tmp_name'], $uploadPath)) {
        // File upload successful
        echo 'File uploaded successfully.';
    } else {
        // File upload failed
        echo 'Error uploading file.';
    }
} else {
    // No file uploaded or an error occurred
    echo 'No file uploaded or an error occurred.';
}
?>
