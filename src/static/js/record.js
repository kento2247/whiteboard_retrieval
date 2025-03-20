document.addEventListener("DOMContentLoaded", setupRecordPage);

function setupRecordPage() {
    const form = document.getElementById("record-form");
    const imageSource = document.getElementById("image-source");
    const uploadContainer = document.getElementById("upload-container");
    const cameraContainer = document.getElementById("camera-container");
    const imageUpload = document.getElementById("image-upload");
    const imagePreview = document.getElementById("image-preview");
    const previewContainer = document.getElementById("preview-container");
    const cameraPreview = document.getElementById("camera-preview");
    const captureBtn = document.getElementById("capture-btn");
    const canvas = document.getElementById("canvas");
    const cancelBtn = document.getElementById("cancel-btn");
    
    let capturedImage = null;
    let stream = null;
    
    // Handle image source selection
    imageSource.addEventListener("change", function() {
        if (this.value === "upload") {
            uploadContainer.style.display = "block";
            cameraContainer.style.display = "none";
            stopCamera();
        } else {
            uploadContainer.style.display = "none";
            cameraContainer.style.display = "block";
            startCamera();
        }
    });
    
    // Handle file upload preview
    imageUpload.addEventListener("change", function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                previewContainer.style.display = "block";
            };
            
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    // Start camera
    function startCamera() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(mediaStream) {
                    stream = mediaStream;
                    cameraPreview.srcObject = mediaStream;
                    cameraPreview.play();
                })
                .catch(function(error) {
                    console.error("Error accessing camera:", error);
                    alert("Could not access the camera. Please check permissions or try uploading an image instead.");
                    imageSource.value = "upload";
                    uploadContainer.style.display = "block";
                    cameraContainer.style.display = "none";
                });
        } else {
            alert("Your browser does not support camera access. Please upload an image instead.");
            imageSource.value = "upload";
            uploadContainer.style.display = "block";
            cameraContainer.style.display = "none";
        }
    }
    
    // Stop camera
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }
    
    // Capture image from camera
    captureBtn.addEventListener("click", function() {
        const context = canvas.getContext("2d");
        canvas.width = cameraPreview.videoWidth;
        canvas.height = cameraPreview.videoHeight;
        context.drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
        
        // Convert to blob for sending to server
        canvas.toBlob(function(blob) {
            capturedImage = blob;
            // Display preview
            imagePreview.src = canvas.toDataURL("image/jpeg");
            previewContainer.style.display = "block";
        }, "image/jpeg");
    });
    
    // Cancel button
    cancelBtn.addEventListener("click", function() {
        window.location.href = "/";
    });
    
    // Form submission
    form.addEventListener("submit", async function(e) {
        e.preventDefault();
        
        const title = document.getElementById("title").value;
        const textContent = document.getElementById("text-content").value;
        
        if (!title) {
            alert("Please enter a title");
            return;
        }
        
        // Check if we have an image - either uploaded or captured
        let imageFile;
        if (imageSource.value === "upload") {
            imageFile = imageUpload.files[0];
            if (!imageFile) {
                alert("Please upload an image");
                return;
            }
            console.log(`Selected file: ${imageFile.name}, size: ${imageFile.size} bytes, type: ${imageFile.type}`);
        } else {
            if (!capturedImage) {
                alert("Please capture an image from the camera");
                return;
            }
            // Generate a unique name for the camera capture with timestamp
            const timestamp = new Date().getTime();
            imageFile = new File([capturedImage], `camera_capture_${timestamp}.jpg`, { type: "image/jpeg" });
            console.log(`Created camera capture file, size: ${capturedImage.size} bytes`);
        }
        
        // Show loading state
        const saveBtn = document.getElementById("save-btn");
        const originalBtnText = saveBtn.textContent;
        saveBtn.disabled = true;
        saveBtn.textContent = "Processing...";
        
        // Create overlay with loading spinner
        const loadingOverlay = document.createElement("div");
        loadingOverlay.className = "loading-overlay";
        loadingOverlay.innerHTML = `
            <div class="spinner"></div>
            <p>Processing image and creating embeddings...</p>
        `;
        document.body.appendChild(loadingOverlay);
        
        let debateId = null;
        
        // First create a debate
        try {
            console.log("Creating debate record...");
            const debateResponse = await fetch("/api/debate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tldr: title,
                    summary: textContent || ""
                })
            });
            
            if (!debateResponse.ok) {
                const errorText = await debateResponse.text();
                throw new Error(`Failed to create debate record: ${debateResponse.status} ${errorText}`);
            }
            
            const debateData = await debateResponse.json();
            debateId = debateData.debate_id;
            console.log(`Successfully created debate with ID: ${debateId}`);
            
            // Verify we have a valid debate ID before proceeding
            if (!debateId || debateId <= 0) {
                throw new Error(`Invalid debate ID received: ${debateId}`);
            }
            
            // Now upload the image with the debate ID
            console.log(`Uploading image for debate ID: ${debateId}...`);
            const formData = new FormData();
            formData.append("file", imageFile);
            formData.append("text_content", textContent || "");
            
            // Make absolutely sure debate_id is a string to prevent FormData issues
            const debateIdString = String(debateId);
            console.log(`Converting debate_id (${typeof debateId}: ${debateId}) to string: ${debateIdString}`);
            formData.append("debate_id", debateIdString);
            
            // Debug the actual FormData content
            console.log("FormData entries:");
            for (const pair of formData.entries()) {
                console.log(`  ${pair[0]}: ${pair[1]}`);
            }
            
            // Log what we're sending
            console.log(`Form data:
                - debate_id: ${debateId} (typeof: ${typeof debateId})
                - text_content: ${textContent ? textContent.substring(0, 50) + '...' : "(empty)"}
                - file: ${imageFile.name} (${imageFile.size} bytes)
            `);
            
            const imageResponse = await fetch("/api/add", {
                method: "POST",
                body: formData
            });
            
            let responseData;
            try {
                responseData = await imageResponse.json();
                console.log("Full image upload response:", responseData);
            } catch (jsonError) {
                const errorText = await imageResponse.text();
                throw new Error(`Invalid JSON response: ${errorText}`);
            }
            
            if (!imageResponse.ok) {
                throw new Error(`Failed to upload image: ${responseData.detail || imageResponse.statusText}`);
            }
            
            // Verify the image was properly associated
            if (responseData.image_id && responseData.image_path) {
                console.log(`Image successfully uploaded and associated:
                    - Image ID: ${responseData.image_id}
                    - Image Path: ${responseData.image_path}
                    - Debate ID: ${debateId}
                `);
                
                // Verify the association is correct
                // We'll fetch the debates to confirm our image is associated with the debate
                try {
                    const verifyResponse = await fetch('/api/debates');
                    if (verifyResponse.ok) {
                        const debatesData = await verifyResponse.json();
                        const ourDebate = debatesData.debates.find(d => d.id === debateId);
                        if (ourDebate && ourDebate.image_path) {
                            console.log(`✅ Verification successful! Debate ${debateId} has image path: ${ourDebate.image_path}`);
                        } else {
                            console.warn(`⚠️ Verification failed! Debate ${debateId} does not have an associated image in the API response`);
                        }
                    }
                } catch (verifyError) {
                    console.warn(`Error during verification: ${verifyError.message}`);
                }
                
                // Verify the image is accessible
                const imgTest = new Image();
                imgTest.onload = function() {
                    console.log(`Image is accessible at path: ${responseData.image_path}`);
                };
                imgTest.onerror = function() {
                    console.warn(`Image is NOT accessible at path: ${responseData.image_path}`);
                };
                
                // Try both potential paths
                const testPaths = [
                    `/${responseData.image_path}`,
                    `/static/uploads/${responseData.image_path.split('/').pop()}`
                ];
                
                for (const path of testPaths) {
                    console.log(`Testing image accessibility at: ${path}`);
                    const testImg = new Image();
                    testImg.src = path;
                }
            } else {
                console.warn(`Warning: Image may not have been properly associated:
                    - Response: ${JSON.stringify(responseData)}
                `);
            }
            
            // Redirect to home page after successful submission
            console.log("Redirecting to home page...");
            window.location.href = "/";
            
        } catch (error) {
            console.error("Error saving record:", error);
            alert("Error saving record: " + error.message);
            
            // Remove loading overlay and restore button state
            document.body.removeChild(loadingOverlay);
            saveBtn.disabled = false;
            saveBtn.textContent = originalBtnText;
        }
    });
    
    // Clean up when leaving the page
    window.addEventListener("beforeunload", stopCamera);
}