document.addEventListener("DOMContentLoaded", function () {
    const imageTextPair = document.querySelector(".image-text-pair");

    const dataBlocks = [
        { text: "Whiteboard1", images: ["/static/images/1.jpg", "/static/images/1.jpg", "/static/images/1.jpg"] },
        { text: "Whiteboard2", images: ["/static/images/2.jpg", "/static/images/2.jpg", "/static/images/2.jpg"] },
        { text: "Whiteboard3", images: ["/static/images/3.jpg", "/static/images/3.jpg"] },
        { text: "Whiteboard4", images: ["/static/images/4.jpg", "/static/images/4.jpg", "/static/images/4.jpg"] }
    ];

    function addImageBlock(data) {
        const blockDiv = document.createElement("div");
        blockDiv.classList.add("image-block");

        const carouselDiv = document.createElement("div");
        carouselDiv.classList.add("carousel");

        const indicatorsDiv = document.createElement("div");
        indicatorsDiv.classList.add("carousel-indicators");

        data.images.forEach((src, index) => {
            const img = document.createElement("img");
            img.src = src;
            img.alt = data.text;
            carouselDiv.appendChild(img);

            const dot = document.createElement("span");
            dot.classList.add("dot");
            if (index === 0) dot.classList.add("active");
            dot.dataset.index = index;
            indicatorsDiv.appendChild(dot);

            dot.addEventListener("click", () => {
                const imgRect = img.getBoundingClientRect();
                const carouselRect = carouselDiv.getBoundingClientRect();
                
                const scrollLeft = carouselDiv.scrollLeft + imgRect.left - carouselRect.left - (carouselRect.width / 2) + (imgRect.width / 2);
                
                carouselDiv.scrollTo({
                    left: scrollLeft,
                    behavior: "smooth",
                });

                updateIndicators(indicatorsDiv, index);
            });
        });

        const description = document.createElement("p");
        description.classList.add("description");
        description.textContent = data.text;

        blockDiv.appendChild(carouselDiv);
        blockDiv.appendChild(indicatorsDiv);
        blockDiv.appendChild(description);
        imageTextPair.appendChild(blockDiv);

        carouselDiv.addEventListener("scroll", () => {
            let closestIndex = 0;
            let minDiff = Infinity;
            Array.from(carouselDiv.children).forEach((img, index) => {
                let diff = Math.abs(carouselDiv.scrollLeft - img.offsetLeft);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestIndex = index;
                }
            });
            updateIndicators(indicatorsDiv, closestIndex);
        });
    }

    function updateIndicators(indicatorsDiv, activeIndex) {
        Array.from(indicatorsDiv.children).forEach((dot, index) => {
            dot.classList.toggle("active", index === activeIndex);
        });
    }

    dataBlocks.forEach(addImageBlock);
});