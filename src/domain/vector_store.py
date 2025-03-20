import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np

from src.model import Processer


class VectorStore:
    def __init__(self, dimension: int = 1024, db_path: str = "vectors.db"):
        self.dimension = dimension
        # self.index = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexFlatIP(dimension)
        self.processer = Processer()

        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS debate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tldr TEXT,
                summary TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            
            CREATE TABLE IF NOT EXISTS image (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id INTEGER,
                ocr TEXT,
                image_path TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (debate_id) REFERENCES debate(id)
            );
        """
        )
        self.conn.commit()

        self.faiss_to_image_id = {}
        self.image_id_to_faiss = {}
        self.image_id_to_text = {}
        self._load_existing_vectors()

    def _load_existing_vectors(self):
        """Load existing vectors from disk if they exist"""
        vector_file = self.db_path.parent / "vectors.faiss"
        if vector_file.exists():
            self.index = faiss.read_index(str(vector_file))

            self.cursor.execute("SELECT id FROM image ORDER BY id")
            for i, (image_id,) in enumerate(self.cursor.fetchall()):
                self.faiss_to_image_id[i] = image_id
                self.image_id_to_faiss[image_id] = i
                self.image_id_to_text[image_id] = ""

    def add_debate(self, tldr: str, summary: str) -> int:
        """Add a new debate entry"""
        self.cursor.execute(
            """
            INSERT INTO debate (tldr, summary)
            VALUES (?, ?)
        """,
            (tldr, summary),
        )
        self.conn.commit()
        return self.cursor.lastrowid or 0  # Return 0 if None

    def add_image(
        self, debate_id: int, image_path: str, vector: np.ndarray, ocr_text: str
    ) -> int:
        """Add a new image and its vector"""
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)
        vector = vector.reshape(1, -1)

        self.cursor.execute(
            """
            INSERT INTO image (debate_id, image_path, ocr)
            VALUES (?, ?, ?)
        """,
            (debate_id, image_path, ocr_text),
        )
        image_id = self.cursor.lastrowid
        self.conn.commit()

        # Add the vector to the FAISS index
        vector /= np.linalg.norm(vector, axis=1, keepdims=True)  # L2ノルムを 1 に正規化
        self.index.add(vector)
        faiss_idx = self.index.ntotal - 1

        self.faiss_to_image_id[faiss_idx] = image_id
        self.image_id_to_faiss[image_id] = faiss_idx
        self.image_id_to_text[image_id] = ocr_text

        faiss.write_index(self.index, str(self.db_path.parent / "vectors.faiss"))

        return image_id or 0  # Return 0 if None

    def process_and_add_image(self, debate_id: int, image_path: str) -> int:
        """Process image with embedder and add to store"""
        print(f"Processing image for debate_id={debate_id}, with path={image_path}")

        # Make sure debate_id is valid and convert to int if needed
        try:
            debate_id = int(debate_id)
        except (ValueError, TypeError):
            print(f"WARNING: Invalid debate_id format: {debate_id}, converting to 0")
            debate_id = 0

        if debate_id <= 0:
            print(
                f"WARNING: Invalid debate_id: {debate_id}, image may not be associated correctly"
            )
        else:
            # Verify debate exists
            self.cursor.execute("SELECT id FROM debate WHERE id = ?", (debate_id,))
            debate = self.cursor.fetchone()
            if not debate:
                print(f"WARNING: Debate with ID {debate_id} does not exist in database")
                # Attempt to get the latest valid debate_id
                self.cursor.execute("SELECT id FROM debate ORDER BY id DESC LIMIT 1")
                latest_debate = self.cursor.fetchone()
                if latest_debate:
                    new_debate_id = latest_debate[0]
                    print(
                        f"Using latest debate ID {new_debate_id} instead of {debate_id}"
                    )
                    debate_id = new_debate_id

        # First, standardize the path format for storage in the database
        # Remove any leading slash and 'src/' prefix from the database path
        db_path = image_path.lstrip("/")
        if db_path.startswith("src/"):
            db_path = db_path[4:]

        # For file system access, construct the full path
        # If the path doesn't include 'src/' but should, add it
        if not db_path.startswith("src/"):
            processing_path = f"src/{db_path}"
        else:
            processing_path = db_path

        print(f"Original image_path: {image_path}")
        print(f"Database path: {db_path}")
        print(f"Processing path: {processing_path}")

        # Verify the file exists
        if not os.path.exists(processing_path):
            print(
                f"WARNING: Image file not found at {processing_path}, trying alternative paths"
            )
            # Try some alternative paths
            alt_paths = [
                processing_path,
                db_path,
                f"src/static/uploads/{os.path.basename(db_path)}",
                f"static/uploads/{os.path.basename(db_path)}",
            ]

            for path in alt_paths:
                if os.path.exists(path):
                    print(f"Found file at alternative path: {path}")
                    processing_path = path
                    break
            else:
                raise FileNotFoundError(
                    f"Image file not found at any expected location. Tried: {alt_paths}"
                )

        file_size = os.path.getsize(processing_path)
        print(f"File size: {file_size} bytes")

        if file_size == 0:
            raise ValueError(f"Image file is empty: {processing_path}")

        # Even if image processing fails, we always want to add the basic record to ensure
        # the image path is saved in the database and associated with the debate
        image_id = None

        try:
            # Process image using the full file path for file system access
            print(f"Processing image with Mistral API...")
            image_data = self.processer.process_image(processing_path)
            print(
                f"Image processing successful. Description: {image_data.description if hasattr(image_data, 'description') else 'No description'}..."
            )

            # Add the image with vector embedding
            image_id = self.add_image(
                debate_id=debate_id,
                image_path=db_path,  # Use the standardized path for storage
                vector=image_data.description_feats,
                ocr_text=(
                    ", ".join(image_data.ocr) if hasattr(image_data, "ocr") else ""
                ),
            )
            print(f"Added image with vector embedding, image_id={image_id}")

        except Exception as e:
            import traceback

            print(f"Error processing image: {str(e)}")
            traceback.print_exc()

            # Always save a basic record even if processing fails
            self.cursor.execute(
                """
                INSERT INTO image (debate_id, image_path, ocr)
                VALUES (?, ?, ?)
            """,
                (debate_id, db_path, ""),
            )

            image_id = self.cursor.lastrowid
            self.conn.commit()

            print(
                f"Failed to process image with Mistral API, but saved basic record with image_id={image_id}, debate_id={debate_id}"
            )

        # Double-check the association
        if image_id:
            self.cursor.execute("SELECT debate_id FROM image WHERE id = ?", (image_id,))
            result = self.cursor.fetchone()
            if result and result[0] != debate_id:
                print(
                    f"WARNING: Image {image_id} is associated with debate {result[0]}, not {debate_id}"
                )
                self.cursor.execute(
                    "UPDATE image SET debate_id = ? WHERE id = ?", (debate_id, image_id)
                )
                self.conn.commit()
                print(
                    f"Fixed: Image {image_id} is now associated with debate {debate_id}"
                )

        return image_id or 0  # Ensure we always return an integer

    def search(
        self, query_vector: np.ndarray, k: int = 5
    ) -> List[Tuple[str, float, str, str]]:
        """Search for similar images and return their details"""
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector, dtype=np.float32)

        query_vector /= np.linalg.norm(
            query_vector, axis=1, keepdims=True
        )  # L2ノルムを 1 に正規化
        query_vector = query_vector.reshape(1, -1)

        # Search using FAISS - lower distance is better match
        # FAISS search params: x=query_vector, k=k (number of results)
        distances, indices = self.index.search(query_vector, k)

        results = []
        for distance, faiss_idx in zip(distances[0], indices[0]):
            if faiss_idx < 0:  # FAISS returns -1 for not enough results
                continue

            faiss_idx = int(faiss_idx)

            image_id = self.faiss_to_image_id[faiss_idx]
            self.cursor.execute(
                """
                SELECT i.image_path, i.ocr, d.tldr, d.summary
                FROM image i
                LEFT JOIN debate d ON i.debate_id = d.id
                WHERE i.id = ?
            """,
                (image_id,),
            )
            image_path, ocr, tldr, summary = self.cursor.fetchone()
            results.append((image_path, float(distance), ocr, tldr))

        return results

    def search_by_text(
        self, query_text: str, k: int = 5
    ) -> List[Tuple[str, float, str, str]]:
        """Search using text query that will be embedded using Stella and compared with image embeddings"""
        print(f"Performing embedding-based search for: '{query_text}'")

        try:
            # Embed the query text using Stella via the Processer
            query_embedding = self.processer.process_instruction(
                query_text
            ).instruction_feats
            print(f"Generated query embedding with shape: {query_embedding.shape}")

            # Use the standard FAISS search with the query embedding
            return self.search(query_vector=query_embedding, k=k)

        except Exception as e:
            print(f"Error during embedding-based search: {str(e)}")
            print("Falling back to text-based matching...")

            # Fall back to simple text matching if embedding fails
            return self._text_based_search_fallback(query_text, k)

    def _text_based_search_fallback(
        self, query_text: str, k: int = 5
    ) -> List[Tuple[str, float, str, str]]:
        """Fallback search using simple text matching when embeddings fail"""
        query_lower = query_text.lower()

        # Get all images with their debates
        self.cursor.execute(
            """
            SELECT 
                i.id, i.image_path, i.ocr, 
                d.id, d.tldr, d.summary
            FROM image i
            LEFT JOIN debate d ON i.debate_id = d.id
        """
        )

        results = []
        for img_id, img_path, ocr, debate_id, tldr, summary in self.cursor.fetchall():
            # Skip if any critical field is missing
            if not all([img_path, debate_id, tldr]):
                continue

            # Combine all text fields for searching
            all_text = f"{tldr} {summary or ''} {ocr or ''}".lower()

            # Calculate a simple score based on word matches
            query_words = set(query_lower.split())

            # Simple cosine similarity approximation
            # Count matching words
            matching_words = 0
            for word in query_words:
                if word in all_text:
                    matching_words += 1

            # Only include if there's at least one match
            if matching_words > 0:
                # Calculate a similarity score (0 to 1)
                # This is a simplified version of cosine similarity
                text_words = len(set(all_text.split()))
                if text_words > 0:
                    # Jaccard similarity (intersection over union)
                    score = matching_words / (
                        len(query_words) + text_words - matching_words
                    )
                else:
                    score = 0.0

                # Convert to a distance metric (lower is better)
                distance = 1.0 - score

                print(f"Match for '{tldr}': score={score:.4f}, distance={distance:.4f}")

                results.append((img_path, distance, ocr or "", tldr))

        # Sort by distance (lower is better)
        results.sort(key=lambda x: x[1])

        print(f"Found {len(results)} matches using text fallback")

        # Return at most k results
        return results[:k]

    def get_debate(self, debate_id: int) -> Tuple[str, str, List[Tuple[str, str]]]:
        """Get debate details with all associated images"""
        self.cursor.execute(
            """
            SELECT tldr, summary FROM debate WHERE id = ?
        """,
            (debate_id,),
        )
        tldr, summary = self.cursor.fetchone()

        self.cursor.execute(
            """
            SELECT image_path, ocr FROM image WHERE debate_id = ?
        """,
            (debate_id,),
        )
        images = self.cursor.fetchall()

        return tldr, summary, images

    def get_debates(self) -> List[Tuple[int, str, str]]:
        """Get all debates"""
        self.cursor.execute(
            """
            SELECT id, tldr, summary FROM debate ORDER BY updated_at DESC
        """
        )
        return self.cursor.fetchall()

    def get_debates_with_images(self) -> List[Tuple[int, str, str, str]]:
        """Get all debates with creation timestamps"""
        self.cursor.execute(
            """
            SELECT id, tldr, summary, updated_at FROM debate ORDER BY updated_at DESC
        """
        )
        return self.cursor.fetchall()

    def update_debate(self, debate_id: int, tldr: str, summary: str):
        """Update debate details"""
        self.cursor.execute(
            """
            UPDATE debate 
            SET tldr = ?, summary = ?, updated_at = datetime('now')
            WHERE id = ?
        """,
            (tldr, summary, debate_id),
        )
        self.conn.commit()

    def delete_debate(self, debate_id: int):
        """Delete a debate and all associated images"""
        self.cursor.execute(
            """
            SELECT id, image_path FROM image WHERE debate_id = ?
        """,
            (debate_id,),
        )
        image_data = self.cursor.fetchall()

        for image_id, image_path in image_data:
            faiss_idx = self.image_id_to_faiss[image_id]
            self.index.remove(faiss_idx)
            del self.image_id_to_faiss[image_id]
            del self.image_id_to_text[image_id]

            if os.path.exists(image_path):
                os.remove(image_path)

        self.cursor.execute(
            """
            DELETE FROM image WHERE debate_id = ?
        """,
            (debate_id,),
        )
        self.cursor.execute(
            """
            DELETE FROM debate WHERE id = ?
        """,
            (debate_id,),
        )
        self.conn.commit()

    def close(self):
        """Close the database connection and save FAISS index"""
        faiss.write_index(self.index, str(self.db_path.parent / "vectors.faiss"))
        self.conn.close()
