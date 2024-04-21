console.log('In Js file...')
// Javascript for HW1
const canvas = document.getElementById('obj-image-canvas');
const ctx = canvas.getContext('2d');
const points = [];

function loadObjectImage() {
    const fileInput = document.getElementById('object-image');
    if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(fileInput.files[0]);
    }
}

canvas.addEventListener('click', function(event) {
    if (points.length >= 2) {
        alert('Only two points can be selected');
        return;
    }

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    points.push({ x: x, y: y });

    // Draw a circle or marker at the clicked position
    ctx.fillStyle = 'red';
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fill();

    // Update hidden form fields
    if (points.length == 1) {
        document.getElementById('point1').value = `${x},${y}`;
    } else if (points.length == 2) {
        document.getElementById('point2').value = `${x},${y}`;
    }
});



// Javascript for HW2
// Integral Image
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('imageUploadForIntegral').addEventListener('change', displayOriginalImageBeforeIntegral);
});

function displayOriginalImageBeforeIntegral() {
    const input = document.getElementById('imageUploadForIntegral');
    if (input.files && input.files[0]) {
        // Display the original image
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('original-image').src = e.target.result;
            document.querySelector('.image-integral-container').classList.add('active')
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function processIntegral() {
    const input = document.getElementById('imageUploadForIntegral');
    if (input.files && input.files[0]) {
        // Display the original image
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('original-image').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);

        // Send the image to the Flask backend
        const formData = new FormData();
        formData.append('image', input.files[0]);
        
        fetch('/compute-integral', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            // Display the integral image
            const url = URL.createObjectURL(blob);
            document.getElementById('integral-image').src = url;
        });
    }
}


// Stitch functionality
function displayImagePreviews(files) {
    console.log('In display image preview')
    const previewContainer = document.getElementById('stitch-preview');
    previewContainer.innerHTML = ''; // Clear existing previews

    for (let file of files) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.maxWidth = '100px'; // Set a max width for the preview images
            img.style.maxHeight = '100px';
            previewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
}

document.getElementById('stitchImagesUploadInput').addEventListener('change', function() {
    displayImagePreviews(this.files);
});


function stitchImages() {
    const input = document.getElementById('stitchImagesUploadInput');
    if (input.files.length) {
        const formData = new FormData();
        for (let i = 0; i < input.files.length; i++) {
            formData.append('images[]', input.files[i]);
        }

        fetch('/stitch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            document.getElementById('stitched_image').src = url;
            document.getElementById('stitched_image').style.width = '500px';
            document.getElementById('stitched_image').style.height = '500px'
        });
    }
}