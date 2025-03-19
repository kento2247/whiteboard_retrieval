document.addEventListener("DOMContentLoaded", function () {
    const imagesContainer = document.querySelector(".images");

    function fetchImageData() {
        return [
            { text: "Image 1", src: "/static/images/1.jpg" },
            { text: "Image 2", src: "/static/images/2.jpg" },
            { text: "Image 3", src: "/static/images/3.jpg" },
            { text: "Image 4", src: "/static/images/4.jpg" },
        ];
    }

    function addImageBlock(data) {
        const blockDiv = document.createElement("div");
        blockDiv.classList.add("image-block");

        const img = document.createElement("img");
        img.src = data.src;
        img.alt = data.text;
        blockDiv.appendChild(img);

        const description = document.createElement("p");
        description.classList.add("description");
        description.textContent = data.text;
        blockDiv.appendChild(description);

        imagesContainer.appendChild(blockDiv);
    }

    const imageData = fetchImageData();
    imageData.forEach(addImageBlock);
});