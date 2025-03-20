document.addEventListener("DOMContentLoaded", () => {
  // Check if we have a search query in the URL
  const urlParams = new URLSearchParams(window.location.search);
  const searchQuery = urlParams.get("q");

  if (searchQuery) {
    // If we have a search query, perform search
    performAPISearch(searchQuery);

    // Update search box with the query
    const searchBox = document.getElementById("search-box");
    if (searchBox) {
      searchBox.value = searchQuery;
    }

    // Update page title
    document.title = `Search: ${searchQuery}`;
  } else {
    // If no search query, fetch all debates
    fetchDebates();
  }
});

async function fetchDebates() {
  try {
    const response = await fetch("/api/debates");
    if (!response.ok) {
      throw new Error("Failed to fetch debates");
    }

    const data = await response.json();
    displayDebates(data.debates);
  } catch (error) {
    console.error("Error fetching debates:", error);
    document.querySelector(".image-text-pair").innerHTML = `
            <div class="error-message">
                <p>Failed to load debates. Please try again later.</p>
                <p>Error: ${error.message}</p>
            </div>
        `;
  }
}

async function performAPISearch(query) {
  try {
    // Show loading state
    const container = document.querySelector(".image-text-pair");
    container.innerHTML = `
            <div class="loading">
                <p>Searching for "${query}"...</p>
            </div>
        `;

    console.log(`Searching for debates with query: "${query}"`);

    // Call the search API with minimum score of 0.01 to filter out irrelevant results
    // We can optionally include all results by adding &include_all=true
    const minimum_score = 0.001; // Only include results with some relevance
    const include_all = false; // Don't include all debates by default

    const url = `/api/search-debates?query=${encodeURIComponent(
      query
    )}&minimum_score=${minimum_score}&include_all=${include_all}`;
    console.log(`Fetching from: ${url}`);

    const response = await fetch(url);

    // Check for non-200 response
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Server error (${response.status}): ${errorText}`);
      throw new Error(`Search failed with status ${response.status}`);
    }

    // Parse JSON response
    let data;
    try {
      data = await response.json();
      console.log("Search results:", data);
    } catch (jsonError) {
      console.error("Failed to parse JSON response:", jsonError);
      throw new Error("Invalid response from server");
    }

    // Check if response has expected format
    if (!data || !data.debates) {
      console.error("Unexpected response format:", data);
      throw new Error("Invalid response format");
    }

    // Find the highest score for color-coding
    const hasScores = data.debates.some((debate) => debate.score > 0);

    // Display the results
    displayDebates(data.debates, true, hasScores);

    // Count relevant results (with score > 0)
    const relevantResults = data.debates.filter(
      (debate) => debate.score > 0
    ).length;

    // Update the header to indicate search results
    const header =
      document.querySelector("header") || document.createElement("header");
    if (data.debates.length === 0) {
      header.innerHTML = `
                <h1>No Results for "${query}"</h1>
                <p>Try a different search term or <a href="/" class="clear-search">view all debates</a></p>
            `;
    } else {
      header.innerHTML = `
                <h1>Search Results: "${query}"</h1>
                <p>${data.debates.length} debates found${
        hasScores ? `, ${relevantResults} with matches` : ""
      }</p>
                <a href="/" class="clear-search">Clear Search</a>
            `;
    }

    if (!document.querySelector("header")) {
      document.body.insertBefore(header, document.body.firstChild);
    }
  } catch (error) {
    console.error("Error searching debates:", error);
    document.querySelector(".image-text-pair").innerHTML = `
            <div class="error-message">
                <p>Failed to search debates. Please try again.</p>
                <p>Error: ${error.message}</p>
                <p><a href="/" class="clear-search">View all debates</a></p>
            </div>
        `;
  }
}

function displayDebates(debates, isSearchResult = false, hasScores = false) {
  console.log("Rendering debates:", debates);

  const container = document.querySelector(".image-text-pair");
  container.innerHTML = "";

  if (debates.length === 0) {
    container.innerHTML = `
            <div class="no-debates">
                <p>${
                  isSearchResult
                    ? "No matches found"
                    : "No whiteboard images found"
                }.</p>
                <p>${
                  isSearchResult
                    ? '<a href="/">Back to all debates</a>'
                    : 'Click <a href="/record">here</a> to add a new one'
                }.</p>
            </div>
        `;
    return;
  }

  // Create cards for each debate
  const debatesFragment = document.createDocumentFragment();
  const placeholderImage = "/static/images/placeholder.svg";

  debates.forEach((debate) => {
    // Ensure debate has a score property, default to 0 if not in search results
    if (!debate.hasOwnProperty("score")) {
      debate.score = 0;
    }

    console.log(
      `Processing debate ID ${debate.id} with image path: "${
        debate.image_path
      }"${isSearchResult ? ` (score: ${debate.score.toFixed(4)})` : ""}`
    );

    const card = document.createElement("div");
    card.className = "debate-card";
    card.dataset.id = debate.id;
    card.dataset.score = debate.score;

    // Add classes based on score ranges if we're in search results mode
    if (isSearchResult && hasScores) {
      if (debate.score > 0.8) {
        card.classList.add("high-match");
      } else if (debate.score > 0.5) {
        card.classList.add("medium-match");
      } else if (debate.score > 0) {
        card.classList.add("low-match");
      } else {
        card.classList.add("no-match");
      }
    }

    // Handle image path
    let imagePath = null;
    let imagePathsToTry = [];

    if (debate.image_path) {
      const filename = debate.image_path.split("/").pop();

      // Build a list of paths to try, in order of preference
      imagePathsToTry = [
        `/${debate.image_path}`, // /static/uploads/filename.jpg
        `/static/uploads/${filename}`, // /static/uploads/filename.jpg (direct)
        `/uploads/${filename}`, // /uploads/filename.jpg (alternative mount)
        `/src/static/uploads/${filename}`, // /src/static/uploads/filename.jpg
        `/static/images/placeholder.svg`, // fallback
      ];

      console.log(
        `Generated image paths for debate ${debate.id}:`,
        imagePathsToTry
      );

      // Set the first path to try
      imagePath = imagePathsToTry[0];
    } else {
      console.log(`No image path for debate ${debate.id}, using placeholder`);
      imagePath = placeholderImage;
    }

    // Create a div to hold the image with error handling
    const imageDiv = document.createElement("div");
    imageDiv.className = "debate-image";

    // Create an image element with error handling
    const imgElement = document.createElement("img");
    imgElement.alt = debate.tldr;
    imgElement.src = imagePath;

    // Current path index for fallbacks
    let currentPathIndex = 0;

    // Setup error handling to try alternative paths
    imgElement.onerror = function () {
      console.warn(
        `Failed to load image from ${this.src} for debate ${debate.id}`
      );

      if (
        imagePathsToTry.length > 0 &&
        currentPathIndex < imagePathsToTry.length - 1
      ) {
        // Try next path
        currentPathIndex++;
        const nextPath = imagePathsToTry[currentPathIndex];
        console.log(`Trying alternative path ${currentPathIndex}: ${nextPath}`);
        this.src = nextPath;
      } else {
        // All paths failed, use placeholder
        console.error(
          `All image paths failed for debate ${debate.id}, using placeholder`
        );
        this.src = placeholderImage;
        this.onerror = null; // Prevent further errors
      }
    };

    // Setup success handler
    imgElement.onload = function () {
      console.log(
        `✅ Successfully loaded image for debate ${debate.id} from: ${this.src}`
      );
    };

    // Add image to its container
    imageDiv.appendChild(imgElement);

    // Create the details div
    const detailsDiv = document.createElement("div");
    detailsDiv.className = "debate-details";

    // Add score badge for all debates with a score > 0
    let scoreHtml = "";
    if (debate.score > 0) {
      const scorePercent = Math.round(debate.score * 100);
      scoreHtml = `<span class="score-badge ${
        scorePercent > 70 ? "high" : scorePercent > 40 ? "medium" : "low"
      }">${scorePercent}%</span>`;
    } else if (isSearchResult) {
      // For search results with zero score, show a "No match" badge
      scoreHtml = `<span class="score-badge no-match">No match</span>`;
    }

    detailsDiv.innerHTML = `
            <h3>${debate.tldr} ${scoreHtml}</h3>
            <p class="debate-summary">${
              debate.summary?.substring(0, 100) || ""
            }${debate.summary?.length > 100 ? "..." : ""}</p>
            <p class="debate-date">${formatDate(debate.created_at)}</p>
        `;

    // Add parts to the card
    card.appendChild(imageDiv);
    card.appendChild(detailsDiv);

    // Add click event to navigate to debate details
    card.addEventListener("click", () => {
      window.location.href = `/debate?id=${debate.id}`;
    });

    debatesFragment.appendChild(card);
  });

  container.appendChild(debatesFragment);

  // Add floating button to create a new record
  const addButton = document.createElement("div");
  addButton.className = "add-button";
  addButton.innerHTML = "+";
  addButton.title = "Add new whiteboard";
  addButton.addEventListener("click", () => {
    window.location.href = "/record";
  });

  document.body.appendChild(addButton);
}

function formatDate(dateString) {
  if (!dateString) return "";

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  } catch (e) {
    return dateString;
  }
}

// Search functionality
document.getElementById("search-btn")?.addEventListener("click", performSearch);
document
  .getElementById("search-box")
  ?.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      performSearch();
    }
  });

function performSearch() {
  const query = document.getElementById("search-box").value.trim();
  if (query) {
    window.location.href = `/?q=${encodeURIComponent(query)}`;
  }
}
