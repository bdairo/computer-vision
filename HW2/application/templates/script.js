const canvas = document.getElementById('image-canvas');
const ctx = canvas.getContext('2d');
const points = [];

function loadImage() {
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

// Optional: Function to handle loading image for integral computation
function loadIntegralImage() {
    // Similar to loadImage(), for integral image computation
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
