document.addEventListener("DOMContentLoaded", () => {
  // Get debate ID from URL query parameter
  const urlParams = new URLSearchParams(window.location.search);
  const debateId = urlParams.get("id");

  if (!debateId) {
    showError("No debate ID provided.");
    return;
  }

  // Fetch debate details
  fetchDebateDetails(debateId);

  // Setup back button to remember search query if present
  const backButton = document.getElementById("back-button");
  const searchQuery = urlParams.get("q");
  if (searchQuery) {
    backButton.href = `/?q=${encodeURIComponent(searchQuery)}`;
  }
});

async function fetchDebateDetails(debateId) {
  try {
    const response = await fetch(`/api/debate/${debateId}`);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch debate details: ${response.status} ${response.statusText}`
      );
    }

    const debate = await response.json();
    displayDebateDetails(debate);
  } catch (error) {
    console.error("Error fetching debate details:", error);
    showError(error.message);
  }
}

function displayDebateDetails(debate) {
  // Clone the template
  const template = document.getElementById("debate-template");
  const debateElement = template.content.cloneNode(true);

  // --- タイトル: 表示と編集用 ---
  const titleH1 = debateElement.getElementById("debate-title");
  const titleInput = debateElement.getElementById("debate-title-input");
  titleH1.textContent = debate.tldr;
  titleInput.value = debate.tldr;

  // --- ID, 日付 ---
  debateElement.getElementById("debate-id").textContent = debate.id;
  debateElement.getElementById("debate-date").textContent = formatDate(
    debate.created_at
  );

  // --- サマリー: 表示と編集用 ---
  const summaryElement = debateElement.getElementById("debate-summary");
  const summaryInput = debateElement.getElementById("debate-summary-input");
  summaryElement.textContent = debate.summary || "No summary available.";
  summaryInput.value = debate.summary || "";

  // --- OCRは編集不可 ---
  const ocrElement = debateElement.getElementById("debate-ocr");
  if (debate.ocr_text && debate.ocr_text.trim()) {
    ocrElement.textContent = debate.ocr_text;
  } else {
    ocrElement.textContent = ""; // ここで空にすると .ocr-text:empty::before で代替表示
  }

  // 画像のセットアップ
  const imageElement = debateElement.getElementById("debate-image");
  if (debate.image_path) {
    setupImageWithFallbacks(imageElement, debate.image_path, debate.tldr);
  } else {
    imageElement.src = "/static/images/placeholder.svg";
    imageElement.alt = "No image available";
  }

  // スコア表示
  if (typeof debate.score === "number") {
    const scoreBadgeContainer = debateElement.getElementById(
      "score-badge-container"
    );
    addScoreBadge(scoreBadgeContainer, debate.score);
  }

  // ボタン類
  const editButton = debateElement.getElementById("edit-debate");
  const saveButton = debateElement.getElementById("save-debate");
  const deleteButton = debateElement.getElementById("delete-debate");

  // --- Edit ボタン ---
  editButton.addEventListener("click", () => {
    // 表示を隠して編集フォームを表示
    titleH1.style.display = "none";
    titleInput.style.display = "inline-block";

    summaryElement.style.display = "none";
    summaryInput.style.display = "block";

    editButton.style.display = "none";
    saveButton.style.display = "inline-block";
  });

  // --- Save ボタン ---
  saveButton.addEventListener("click", () => {
    // フォームの内容を表示用要素に反映
    const newTitle = titleInput.value;
    const newSummary = summaryInput.value;

    titleH1.textContent = newTitle;
    summaryElement.textContent = newSummary;

    // 表示を戻す
    titleH1.style.display = "block";
    titleInput.style.display = "none";

    summaryElement.style.display = "block";
    summaryInput.style.display = "none";

    saveButton.style.display = "none";
    editButton.style.display = "inline-block";

    // TODO: 実際の保存処理をサーバーに送る場合はここでfetchなど
    updateDebateOnServer(debate.id, newTitle, newSummary);
  });

  deleteButton.addEventListener("click", async () => {
    if (confirm(`Are you sure you want to delete "${debate.tldr}"?`)) {
      try {
        const response = await fetch(`/api/debate/${debate.id}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          // エラー応答を受け取った場合
          const errData = await response.json();
          throw new Error(errData.detail || "Failed to delete debate");
        }

        // 正常に削除できた場合は一覧に戻るなどの処理
        alert(`Debate ${debate.id} deleted successfully.`);
        window.location.href = "/"; // 例: ホームに戻る
      } catch (error) {
        console.error("Delete debate error:", error);
        alert("Error deleting debate: " + error.message);
      }
    }
  });

  // 読み込み状態解除
  const container = document.getElementById("debate-container");
  container.className = ""; // Remove loading class
  container.innerHTML = "";
  container.appendChild(debateElement);

  // ページタイトル設定
  document.title = `${debate.tldr} - Debate Details`;
}

// -- 以下の関数はそのまま利用できます --

function setupImageWithFallbacks(imageElement, imagePath, altText) {
  const filename = imagePath.split("/").pop();

  // Build a list of paths to try, in order of preference
  const imagePathsToTry = [
    `/${imagePath}`, // /static/uploads/filename.jpg
    `/static/uploads/${filename}`, // /static/uploads/filename.jpg (direct)
    `/uploads/${filename}`, // /uploads/filename.jpg (alternative mount)
    `/src/static/uploads/${filename}`, // /src/static/uploads/filename.jpg
    `/static/images/placeholder.svg`, // fallback
  ];

  // Set the first path to try
  imageElement.alt = altText;
  imageElement.src = imagePathsToTry[0];

  // Current path index for fallbacks
  let currentPathIndex = 0;

  // Setup error handling to try alternative paths
  imageElement.onerror = function () {
    console.warn(`Failed to load image from ${this.src}`);

    if (currentPathIndex < imagePathsToTry.length - 1) {
      // Try next path
      currentPathIndex++;
      const nextPath = imagePathsToTry[currentPathIndex];
      console.log(`Trying alternative path: ${nextPath}`);
      this.src = nextPath;
    } else {
      // All paths failed, use placeholder
      console.error(`All image paths failed, using placeholder`);
      this.src = "/static/images/placeholder.svg";
      this.alt = "Image not available";
      this.onerror = null; // Prevent further errors
    }
  };

  imageElement.onload = function () {
    console.log(`Successfully loaded image from: ${this.src}`);
  };
}

function addScoreBadge(container, score) {
  if (score <= 0) return; // Don't show zero scores

  const scorePercent = Math.round(score * 100);
  const scoreClass =
    scorePercent > 70 ? "high" : scorePercent > 40 ? "medium" : "low";

  const badge = document.createElement("span");
  badge.className = `score-badge ${scoreClass}`;
  badge.textContent = `${scorePercent}%`;

  container.appendChild(badge);
}

function formatDate(dateString) {
  if (!dateString) return "Unknown date";

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (e) {
    return dateString;
  }
}

function showError(message) {
  // Hide loading container
  document.getElementById("debate-container").style.display = "none";

  // Show error container
  const errorContainer = document.getElementById("error-container");
  errorContainer.style.display = "block";

  // Set error message
  document.getElementById("error-message").textContent = message;
}

async function updateDebateOnServer(debateId, newTitle, newSummary) {
  try {
    const response = await fetch(`/api/debate/${debateId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tldr: newTitle,
        summary: newSummary,
      }),
    });

    if (!response.ok) {
      // 4xx / 5xx エラーの場合
      const errData = await response.json().catch(() => ({}));
      throw new Error(
        errData.detail || `Failed to update debate ID: ${debateId}`
      );
    }

    console.log(`Debate ${debateId} updated successfully.`);
    // alertなど通知系は呼び出し元で必要に応じて実行
  } catch (error) {
    console.error("Update debate error:", error);
    throw error; // 呼び出し元でキャッチさせる
  }
}
