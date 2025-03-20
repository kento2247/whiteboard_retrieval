document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const imageUrl = URL.createObjectURL(file);

    const fileList = document.getElementById('fileList');
    const fileItem = document.createElement('div');
    fileItem.classList.add('file-item');

    // 画像表示
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = file.name;
    img.classList.add('preview-image');

    // ファイル名表示
    const fileName = document.createElement('p');
    fileName.textContent = file.name;
    fileName.classList.add('file-name');

    // 削除ボタン
    const deleteBtn = document.createElement('button');
    deleteBtn.classList.add('delete-btn');
    deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete';
    deleteBtn.addEventListener('click', () => {
        fileList.removeChild(fileItem);
        URL.revokeObjectURL(imageUrl);
    });

    // 要素を追加
    fileItem.appendChild(img);
    fileItem.appendChild(fileName);
    fileItem.appendChild(deleteBtn);
    fileList.appendChild(fileItem);
});
