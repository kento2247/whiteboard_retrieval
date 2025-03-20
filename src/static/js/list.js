document.addEventListener("DOMContentLoaded", async function () {
  const imagesContainer = document.querySelector(".images");

  async function fetchImageData() {
    const response = await fetch("/api/debates");
    const data = await response.json();
    debates = data.debates;
    let return_data = [];
    debates.forEach((item) => {
      return_data.push({
        id: item.id,
        src: item.image_path,
        text: item.tldr,
      });
    });
    return return_data;
  }

  function addImageBlock(data) {
    const blockDiv = document.createElement("div");
    blockDiv.classList.add("image-block");

    const link = document.createElement("a");
    link.href = `/debate?id=${data.id}`;

    const img = document.createElement("img");
    img.src = data.src;
    img.alt = data.text;
    link.appendChild(img);

    const description = document.createElement("p");
    description.classList.add("description");
    description.textContent = data.text;
    link.appendChild(description);

    blockDiv.appendChild(link);

    imagesContainer.appendChild(blockDiv);
  }

  const imageData = await fetchImageData();
  imageData.forEach(addImageBlock);
});
