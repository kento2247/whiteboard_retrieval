document.addEventListener("DOMContentLoaded", fetchData);

async function fetchData() {
    try {
        const data = {
            title: "Metadata",
            images: [
                "/static/images/1.jpg",
                "/static/images/2.jpg",
                "/static/images/3.jpg"
            ],
            tableData: [
                ["AAA", "BBB", "CCC"],
                ["123", "456"]
            ],
            summary: "This is a summary of the OCR result."
        };

        document.getElementById("title").textContent = data.title;

        const carousel = document.getElementById("image-carousel");
        const indicatorsContainer = document.querySelector(".carousel-indicators");
        const fragment = document.createDocumentFragment();
        const indicatorsFragment = document.createDocumentFragment();

        data.images.forEach((src, index) => {
            const img = document.createElement("img");
            img.src = src;
            img.alt = "OCR Image";
            fragment.appendChild(img);

            const dot = document.createElement("span");
            dot.classList.add("dot");
            if (index === 0) dot.classList.add("active");
            indicatorsFragment.appendChild(dot);

            dot.addEventListener("click", () => {
                carousel.scrollTo({
                    left: img.offsetLeft,
                    behavior: "smooth"
                });
                updateIndicators(index);
            });
        });

        carousel.appendChild(fragment);
        indicatorsContainer.appendChild(indicatorsFragment);

        carousel.addEventListener("scroll", () => {
            const scrollLeft = carousel.scrollLeft;
            const carouselWidth = carousel.clientWidth;
            const totalWidth = carousel.scrollWidth;
            const scrollFraction = scrollLeft / (totalWidth - carouselWidth);
            const activeIndex = Math.round(scrollFraction * (data.images.length - 1));
            updateIndicators(activeIndex);
        });

        const table = document.getElementById("data-table");
        const tableFragment = document.createDocumentFragment();

        data.tableData.forEach(rowData => {
            const row = document.createElement("tr");

            rowData.forEach(cellData => {
                const cell = document.createElement("td");
                cell.textContent = cellData;
                row.appendChild(cell);
            });

            tableFragment.appendChild(row);
        });

        table.appendChild(tableFragment);

        document.getElementById("textbox").value = data.summary;
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

function updateIndicators(activeIndex) {
    const dots = document.querySelectorAll(".carousel-indicators .dot");
    dots.forEach((dot, index) => {
        dot.classList.toggle("active", index === activeIndex);
    });
}