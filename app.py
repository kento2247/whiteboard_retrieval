from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from typing import List
import hashlib
import time
import os

from src.stella import StellaEmbedder
from src.domain.vector_store import VectorStore

app = FastAPI()

# Mount the static folder for static assets
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Add a specific mount point for uploads to ensure they're accessible
app.mount("/uploads", StaticFiles(directory="src/static/uploads"), name="uploads")

# Initialize global instances
embedder = StellaEmbedder()
vector_store = VectorStore(dimension=1024, db_path="vectors.db")

# データモデル（例：画像とテキストペア）
class ImageTextPair(BaseModel):
    image_url: str
    description: str

class SearchResult(BaseModel):
    file_path: str
    distance: float
    text_content: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

class DebateRequest(BaseModel):
    tldr: str
    summary: str = ""

class DebateResponse(BaseModel):
    debate_id: int
    message: str

class DebateListItem(BaseModel):
    id: int
    tldr: str
    summary: str
    created_at: str
    image_path: str | None = None
    score: float = 0.0  # Add score field with default of 0

class DebateListResponse(BaseModel):
    debates: List[DebateListItem]

class DebateResult(BaseModel):
    id: int
    tldr: str
    summary: str
    created_at: str
    image_path: str | None = None
    score: float
    
class DebateSearchResponse(BaseModel):
    debates: List[DebateResult]

class DebateDetailResponse(BaseModel):
    id: int
    tldr: str
    summary: str
    created_at: str
    image_path: str | None = None
    score: float = 0.0
    ocr_text: str | None = None  # Add OCR text field for extracted text

@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse("src/static/index.html")

@app.get("/search", response_class=FileResponse)
async def read_search():
    return FileResponse("src/static/search.html")

@app.get("/record", response_class=FileResponse)
async def read_record():
    return FileResponse("src/static/record.html")

@app.get("/list", response_class=FileResponse)
async def read_list():
    return FileResponse("src/static/list.html")

@app.get("/test-images", response_class=FileResponse)
async def test_images():
    return FileResponse("test_images.html")

@app.get("/debate", response_class=FileResponse)
async def read_debate():
    return FileResponse("src/static/debate.html")

@app.post("/api/search")
async def search_images(query: str):
    try:
        query_vector = embedder.embed_text(query)
        
        results = vector_store.search(query_vector, k=5)
        
        formatted_results = [
            SearchResult(file_path=path, distance=dist, text_content=text)
            for path, dist, text, _ in results
        ]
        
        return SearchResponse(results=formatted_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debate", response_model=DebateResponse)
async def create_debate(request: DebateRequest):
    try:
        debate_id = vector_store.add_debate(request.tldr, request.summary)
        return DebateResponse(debate_id=debate_id, message="Debate created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add")
async def add_image(
    file: UploadFile = File(...),
    text_content: str = "",
    debate_id: str = "0"  # Changed to string to handle form data correctly
):
    try:
        # Parse debate_id as integer, print the raw value for debugging
        print(f"Raw debate_id received: '{debate_id}' (type: {type(debate_id)})")
        
        try:
            debate_id_int = int(debate_id)
        except (ValueError, TypeError):
            print(f"WARNING: Cannot parse debate_id '{debate_id}' as an integer, defaulting to latest debate")
            # Try to get the most recent debate ID as a fallback
            vector_store.cursor.execute("SELECT id FROM debate ORDER BY id DESC LIMIT 1")
            latest_debate = vector_store.cursor.fetchone()
            debate_id_int = latest_debate[0] if latest_debate else 0
            print(f"Using latest debate ID: {debate_id_int}")
        
        # Extra validation
        if debate_id_int <= 0:
            # Try to get the most recent debate ID as a fallback
            vector_store.cursor.execute("SELECT id FROM debate ORDER BY id DESC LIMIT 1")
            latest_debate = vector_store.cursor.fetchone()
            if latest_debate:
                debate_id_int = latest_debate[0]
                print(f"Found invalid debate_id={debate_id}, using latest debate ID {debate_id_int} instead")
            else:
                print(f"WARNING: No valid debates found in database, images won't be associated correctly")
        
        # Verify debate exists
        vector_store.cursor.execute("SELECT id, tldr FROM debate WHERE id = ?", (debate_id_int,))
        debate = vector_store.cursor.fetchone()
        if not debate:
            print(f"WARNING: Debate with ID {debate_id_int} does not exist in database")
            # Try to get any valid debate as a fallback
            vector_store.cursor.execute("SELECT id, tldr FROM debate ORDER BY id DESC LIMIT 1")
            fallback_debate = vector_store.cursor.fetchone()
            if fallback_debate:
                debate_id_int = fallback_debate[0]
                print(f"Using fallback debate ID {debate_id_int} ({fallback_debate[1]})")
            else:
                print(f"ERROR: No debates found in database")
        else:
            print(f"Found debate {debate_id_int}: {debate[1]}")
        
        print(f"Received upload request for debate_id={debate_id_int}, file={file.filename}")
        
        # Create a unique filename using a hash of the original filename and timestamp
        timestamp = str(int(time.time()))
        original_filename = file.filename or "uploaded_image"
        file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
        
        # Create hash from original filename + timestamp
        unique_id = hashlib.md5(f"{original_filename}_{timestamp}".encode()).hexdigest()
        new_filename = f"{unique_id}.{file_extension}"
        
        # Ensure the upload directory exists
        uploads_dir = Path("src/static/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Full path for file system storage
        file_system_path = uploads_dir / new_filename
        
        # URL path for database storage (this is what will be served to the client)
        # Important: No leading slash, and no 'src/' prefix for consistent storage
        url_path = f"static/uploads/{new_filename}"
        
        print(f"Saving file to {file_system_path}")
        
        # Write the file
        contents = await file.read()
        with open(file_system_path, "wb") as f:
            f.write(contents)
        
        # Verify file was written correctly
        if not file_system_path.exists():
            raise HTTPException(status_code=500, detail=f"Failed to save file to {file_system_path}")
            
        if file_system_path.stat().st_size == 0:
            raise HTTPException(status_code=500, detail=f"File was saved but is empty: {file_system_path}")
            
        print(f"Successfully saved file ({file_system_path.stat().st_size} bytes)")
        
        image_id = None
        
        try:
            # Process the image and add it to the vector store
            print(f"Processing image {url_path}")
            image_id = vector_store.process_and_add_image(debate_id_int, url_path)
            print(f"Successfully processed image and added to vector store with ID {image_id}")
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            # Even if processing fails, still add the basic image record to the database
            cursor = vector_store.cursor
            cursor.execute('''
                INSERT INTO image (debate_id, image_path, ocr)
                VALUES (?, ?, ?)
            ''', (debate_id_int, url_path, text_content or ""))
            image_id = cursor.lastrowid
            vector_store.conn.commit()
            print(f"Saved basic image record with ID {image_id} for debate {debate_id_int}")
        
        # Verify the association after saving
        vector_store.cursor.execute("SELECT debate_id FROM image WHERE id = ?", (image_id,))
        saved_debate_id = vector_store.cursor.fetchone()
        
        if not saved_debate_id or saved_debate_id[0] != debate_id_int:
            print(f"WARNING: Image association issue detected. Expected debate_id={debate_id_int}, got {saved_debate_id[0] if saved_debate_id else 'None'}")
            # Fix the association
            vector_store.cursor.execute("UPDATE image SET debate_id = ? WHERE id = ?", (debate_id_int, image_id))
            vector_store.conn.commit()
            print(f"Fixed association: Image {image_id} is now associated with debate {debate_id_int}")
        
        # Double check the image is in the right place in the filesystem
        if not os.path.exists(file_system_path):
            print(f"WARNING: Image file not found at expected location: {file_system_path}")
        else:
            print(f"Confirmed image file exists at: {file_system_path} ({os.path.getsize(file_system_path)} bytes)")
        
        return {
            "message": "Successfully added", 
            "image_id": image_id, 
            "image_path": url_path,
            "debate_id": debate_id_int  # Return debate_id for verification
        }
            
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debates", response_model=DebateListResponse)
async def get_debates():
    try:
        debates = vector_store.get_debates()
        
        formatted_debates = []
        
        for debate in debates:
            debate_id = debate[0]
            tldr = debate[1]
            summary = debate[2]
            
            created_at = ""
            if len(debate) > 3:
                if isinstance(debate[3], str):
                    created_at = debate[3]
                else:
                    created_at = str(debate[3])
            
            # Query for associated images
            vector_store.cursor.execute('''
                SELECT id, image_path FROM image 
                WHERE debate_id = ? 
                ORDER BY id DESC LIMIT 1
            ''', (debate_id,))
            
            result = vector_store.cursor.fetchone()
            
            # Debug image association
            print(f"Debate {debate_id}: Found image? {result is not None}")
            
            image_path = None
            if result and result[0]:
                image_id, image_path = result
                # Make sure the path follows our conventions
                if image_path and image_path.startswith('src/'):
                    image_path = image_path[4:]  # Remove 'src/' prefix
                    print(f"  Fixed image path: {image_path}")
                
                # Verify the file exists
                file_path = f"src/{image_path}" if not image_path.startswith('src/') else image_path
                if not os.path.exists(file_path):
                    # Try alternative paths
                    basename = os.path.basename(image_path)
                    alt_path = f"src/static/uploads/{basename}"
                    if os.path.exists(alt_path):
                        print(f"  Image file not found at {file_path}, but found at {alt_path}")
                        # Update the path in the database
                        normalized_path = f"static/uploads/{basename}"
                        vector_store.cursor.execute(
                            "UPDATE image SET image_path = ? WHERE id = ?", 
                            (normalized_path, image_id)
                        )
                        vector_store.conn.commit()
                        image_path = normalized_path
                        print(f"  Updated image path in database to {normalized_path}")
                    else:
                        print(f"  WARNING: Image file not found at {file_path} or {alt_path}")
            
            formatted_debates.append(DebateListItem(
                id=debate_id,
                tldr=tldr,
                summary=summary,
                created_at=created_at,
                image_path=image_path,
                score=0.0  # Default score is 0 for regular listing
            ))
            
            print(f"Debate {debate_id}: {tldr} - Image path: {image_path}")
        
        return DebateListResponse(debates=formatted_debates)
    except Exception as e:
        print(f"Error fetching debates: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search-debates")
async def search_debates(query: str, minimum_score: float = 0.0, include_all: bool = False):
    try:
        print(f"Searching for debates with query: '{query}'")
        print(f"Parameters: minimum_score={minimum_score}, include_all={include_all}")
        
        # Get all debates first
        all_debates = vector_store.get_debates_with_images()
        print(f"Found {len(all_debates)} total debates")
        
        # Dictionary to store scores for each debate
        score_by_debate = {}
        
        try:
            # Use embedding-based vector search with cosine similarity
            print("Performing embedding-based search...")
            search_results = vector_store.search_by_text(query, k=20)  # Increase k to get more potential matches
            print(f"Search returned {len(search_results)} results")
            
            # Build a dictionary of image_path -> score for results
            score_by_image = {}
            for image_path, distance, _, _ in search_results:
                # Convert distance to similarity score (lower distance is higher similarity)
                # For FAISS L2 distance, use exponential decay to convert to 0-1 range
                similarity = 1.0 / (1.0 + float(distance))
                score_by_image[image_path] = similarity
                print(f"Image: {image_path}, Score: {similarity:.4f}")
                
            # Map debate IDs to their best scores
            for image_path, score in score_by_image.items():
                # Find which debate this image belongs to
                vector_store.cursor.execute('''
                    SELECT debate_id FROM image WHERE image_path = ?
                ''', (image_path,))
                result = vector_store.cursor.fetchone()
                if result and result[0]:
                    debate_id = result[0]
                    # Keep the highest score for each debate
                    if debate_id not in score_by_debate or score > score_by_debate[debate_id]:
                        score_by_debate[debate_id] = score
                        print(f"Associating image score with debate ID {debate_id}: {score:.4f}")
        except Exception as e:
            print(f"Error in vector search: {str(e)}")
            print("Will continue with direct text matching only")
        
        # Format the results, including all debates but with scores
        debate_results = []
        relevant_count = 0
        
        for debate in all_debates:
            debate_id = debate[0]
            tldr = debate[1]
            summary = debate[2]
            created_at = str(debate[3]) if len(debate) > 3 else ""
            
            # Find the associated image
            vector_store.cursor.execute('''
                SELECT image_path FROM image 
                WHERE debate_id = ? 
                ORDER BY id DESC LIMIT 1
            ''', (debate_id,))
            
            image_path_result = vector_store.cursor.fetchone()
            image_path = image_path_result[0] if image_path_result else None
            
            # Normalize image path
            if image_path and image_path.startswith('src/'):
                image_path = image_path[4:]
                
            # Get score from search results or do direct matching on debate text
            score = score_by_debate.get(debate_id, 0.0)
            
            # Always check for direct text matching in titles and summaries
            # as this can sometimes be more accurate than image-based matching
            if query:
                query_lower = query.lower()
                tldr_lower = tldr.lower()
                summary_lower = (summary or "").lower()
                
                # Direct matching in title gets high score
                if query_lower in tldr_lower:
                    direct_match_score = 0.9
                    score = max(score, direct_match_score)
                    print(f"Direct title match for debate {debate_id}: score {direct_match_score}")
                
                # Partial matching in title
                elif any(word in tldr_lower for word in query_lower.split()):
                    # Calculate how many words match
                    query_words = set(query_lower.split())
                    title_words = set(tldr_lower.split())
                    matching_words = sum(1 for word in query_words if word in title_words)
                    partial_match_score = 0.5 * (matching_words / len(query_words))
                    score = max(score, partial_match_score)
                    print(f"Partial title match for debate {debate_id}: score {partial_match_score:.4f}")
                
                # Summary matching
                elif summary and query_lower in summary_lower:
                    summary_match_score = 0.6
                    score = max(score, summary_match_score)
                    print(f"Summary match for debate {debate_id}: score {summary_match_score}")
            
            # Track if this is a relevant result
            is_relevant = score > minimum_score
            if is_relevant:
                relevant_count += 1
            
            # Only include debates that have a score above the minimum or if include_all is true
            if is_relevant or include_all:
                debate_results.append(DebateResult(
                    id=debate_id,
                    tldr=tldr,
                    summary=summary,
                    created_at=created_at,
                    image_path=image_path,
                    score=score
                ))
        
        # Sort debates by score, highest first
        debate_results.sort(key=lambda x: x.score, reverse=True)
        
        print(f"Returning {len(debate_results)} debate results, {relevant_count} with score > {minimum_score}")
        return DebateSearchResponse(debates=debate_results)
    except Exception as e:
        print(f"Error searching debates: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debate/{debate_id}", response_model=DebateDetailResponse)
async def get_debate(debate_id: int):
    try:
        print(f"Fetching details for debate ID: {debate_id}")
        
        # Check if debate exists
        vector_store.cursor.execute('''
            SELECT id, tldr, summary, created_at, updated_at FROM debate WHERE id = ?
        ''', (debate_id,))
        
        debate = vector_store.cursor.fetchone()
        if not debate:
            raise HTTPException(status_code=404, detail=f"Debate with ID {debate_id} not found")
        
        # Extract debate details
        debate_id = debate[0]
        tldr = debate[1]
        summary = debate[2]
        created_at = str(debate[3] or '')
        
        # Get associated image and OCR text
        vector_store.cursor.execute('''
            SELECT id, image_path, ocr FROM image 
            WHERE debate_id = ? 
            ORDER BY id DESC LIMIT 1
        ''', (debate_id,))
        
        image_result = vector_store.cursor.fetchone()
        image_path = None
        ocr_text = None
        
        if image_result:
            image_id, image_path, ocr_text = image_result
            # Normalize path
            if image_path and image_path.startswith('src/'):
                image_path = image_path[4:]
        
        # Create response object
        response = DebateDetailResponse(
            id=debate_id,
            tldr=tldr,
            summary=summary or "",
            created_at=created_at,
            image_path=image_path,
            score=0.0,  # Default score is 0
            ocr_text=ocr_text or ""
        )
        
        print(f"Returning debate details: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching debate details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))