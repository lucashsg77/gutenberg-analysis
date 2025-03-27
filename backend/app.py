import asyncio
import logging
import os
import json
import time
from typing import Optional, Set
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from gutenberg import GutenbergAPI
from analysis import BookAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Gutenberg Book Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

gutenberg_api = GutenbergAPI()
book_analyzer = BookAnalyzer()

book_cache = {}
book_fetch_tasks = {}
analysis_cache = {}
analysis_tasks = {}

active_tasks: Set[str] = set()

class BookRequest(BaseModel):
    book_id: str

class AnalysisStatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    progress: Optional[float] = None

@app.get("/")
async def root():
    return {"message": "Gutenberg Book Analysis API is running"}

@app.get("/api/active-tasks")
async def get_active_tasks():
    """Debug endpoint to check active tasks"""
    return {
        "active_task_count": len(active_tasks),
        "active_tasks": list(active_tasks),
        "book_fetch_tasks": len(book_fetch_tasks),
        "analysis_tasks": len(analysis_tasks)
    }

@app.get("/api/book-fetch-status/{book_id}")
async def get_book_fetch_status(book_id: str):
    """Check the status of a book fetch operation"""
    if book_id in book_cache:
        return {"status": "complete", "message": "Book is available", "progress": 100}
    
    if book_id in book_fetch_tasks:
        return book_fetch_tasks[book_id]
    
    return {"status": "not_found", "message": "No fetch operation found for this book ID"}

@app.get("/api/fetch-stream/{book_id}")
async def stream_book_fetch_updates(request: Request, book_id: str):
    """Stream real-time updates about the book fetching process using SSE"""
    async def event_generator():
        if book_id in book_cache:
            yield f"data: {json.dumps({'status': 'complete', 'progress': 100, 'message': 'Book is available'})}\n\n"
            return
        elif book_id in book_fetch_tasks:
            yield f"data: {json.dumps(book_fetch_tasks[book_id])}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'not_found', 'message': 'No fetch operation found'})}\n\n"
            return

        last_sent_progress = -1
        last_sent_stage = ""
        
        while True:
            if await request.is_disconnected():
                break

            if book_id in book_cache:
                yield f"data: {json.dumps({'status': 'complete', 'progress': 100, 'message': 'Book is available'})}\n\n"
                break

            if book_id in book_fetch_tasks:
                current_status = book_fetch_tasks[book_id]
                current_progress = current_status.get('progress', 0)
                current_stage = current_status.get('stage', '')

                if (current_progress != last_sent_progress or current_stage != last_sent_stage):
                    yield f"data: {json.dumps(current_status)}\n\n"
                    last_sent_progress = current_progress
                    last_sent_stage = current_stage

                if current_status.get('status') == 'error':
                    yield f"data: {json.dumps(current_status)}\n\n"
                    break

            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.get("/api/analysis-stream/{book_id}")
async def stream_analysis_updates(request: Request, book_id: str):
    """Stream real-time updates about the analysis progress using Server-Sent Events"""
    async def event_generator():
        if book_id in analysis_cache:
            yield f"data: {json.dumps({'status': 'complete', 'progress': 100, 'message': 'Analysis complete'})}\n\n"
            return
        elif book_id in analysis_tasks:
            yield f"data: {json.dumps(analysis_tasks[book_id])}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'not_found', 'message': 'No analysis found'})}\n\n"
            return

        last_sent_progress = -1
        last_sent_stage = ""
        
        while True:
            if await request.is_disconnected():
                break

            if book_id in analysis_cache:
                yield f"data: {json.dumps({'status': 'complete', 'progress': 100, 'message': 'Analysis complete'})}\n\n"
                break

            if book_id in analysis_tasks:
                current_status = analysis_tasks[book_id]
                current_progress = current_status.get('progress', 0)
                current_stage = current_status.get('stage', '')

                if (current_progress != last_sent_progress or current_stage != last_sent_stage):
                    yield f"data: {json.dumps(current_status)}\n\n"
                    last_sent_progress = current_progress
                    last_sent_stage = current_stage

                if current_status.get('status') == 'error':
                    yield f"data: {json.dumps(current_status)}\n\n"
                    break

            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/api/book")
async def get_book(request: BookRequest):
    """Fetch book content and metadata from Project Gutenberg"""
    book_id = request.book_id.strip()

    if book_id in book_cache:
        return {"status": "complete", "message": "Book is available", "book_id": book_id}

    if book_id in book_fetch_tasks and book_fetch_tasks[book_id]["status"] == "processing":
        return {"status": "processing", "message": "Book fetch is in progress", "book_id": book_id}

    book_fetch_tasks[book_id] = {
        "status": "processing", 
        "progress": 5, 
        "message": f"Starting book fetch for ID {book_id}",
        "stage": "fetch_init"
    }

    task_id = f"book_fetch_{book_id}"
    if task_id not in active_tasks:
        active_tasks.add(task_id)
        asyncio.create_task(process_book_fetch(book_id, task_id))
    
    return {"status": "processing", "message": "Book fetch started", "book_id": book_id}

@app.post("/api/analyze")
async def analyze_book(request: BookRequest):
    """Start book analysis using LLM in the background"""
    book_id = request.book_id.strip()

    if book_id in analysis_tasks and analysis_tasks[book_id]["status"] == "processing":
        return {"status": "processing", "message": "Analysis is already in progress"}

    if book_id in analysis_cache:
        return {"status": "complete", "message": "Analysis is complete"}

    if book_id not in book_cache:
        if book_id not in book_fetch_tasks:
            await get_book(BookRequest(book_id=book_id))
            return {"status": "waiting_for_book", "message": "Waiting for book to be fetched first"}
        elif book_fetch_tasks[book_id]["status"] == "processing":
            return {"status": "waiting_for_book", "message": "Waiting for book fetch to complete"}
        elif book_fetch_tasks[book_id]["status"] == "error":
            return {"status": "error", "message": book_fetch_tasks[book_id]["message"]}

    analysis_tasks[book_id] = {
        "status": "processing", 
        "progress": 5, 
        "message": "Starting analysis...",
        "stage": "initialization"
    }

    task_id = f"analysis_{book_id}"
    if task_id not in active_tasks:
        active_tasks.add(task_id)
        asyncio.create_task(process_book_analysis_incremental(book_id, task_id))
    
    return {"status": "processing", "message": "Analysis started"}

@app.get("/api/analysis-status/{book_id}")
async def get_analysis_status(book_id: str):
    """Check the status of book analysis"""
    if book_id in analysis_cache:
        return {"status": "complete", "message": "Analysis is complete", "progress": 100}
    
    if book_id in analysis_tasks:
        return analysis_tasks[book_id]
    
    return {"status": "not_found", "message": "No analysis found for this book ID"}

@app.get("/api/analysis/{book_id}")
async def get_analysis_results(book_id: str):
    """Get the results of book analysis"""
    if book_id not in analysis_cache:
        if book_id in analysis_tasks and analysis_tasks[book_id]["status"] == "processing":
            raise HTTPException(
                status_code=202, 
                detail="Analysis is still in progress"
            )
        raise HTTPException(
            status_code=404, 
            detail="Analysis not found. Please start an analysis first."
        )
    
    return analysis_cache[book_id]

@app.get("/api/book-content/{book_id}")
async def get_book_content(book_id: str):
    """Get the book content if available"""
    if book_id not in book_cache:
        if book_id in book_fetch_tasks and book_fetch_tasks[book_id]["status"] == "processing":
            raise HTTPException(
                status_code=202, 
                detail="Book fetch is still in progress"
            )
        raise HTTPException(
            status_code=404, 
            detail="Book not found. Please fetch the book first."
        )
    
    return book_cache[book_id]

async def process_book_fetch(book_id: str, task_id: str):
    """Process book fetch in true asynchronous manner with detailed progress updates"""
    try:
        start_time = time.time()

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 5, 
            "message": "Starting book fetch...",
            "stage": "fetch_init"
        }

        await asyncio.sleep(0.1)

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 10, 
            "message": "Fetching book metadata...",
            "stage": "metadata_fetch"
        }

        metadata, meta_error = await gutenberg_api.get_book_metadata(book_id)
        if meta_error:
            book_fetch_tasks[book_id] = {
                "status": "error", 
                "message": meta_error
            }
            return

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 25, 
            "message": f"Metadata retrieved for '{metadata.get('title', f'Book {book_id}')}'. Fetching content...",
            "stage": "content_fetch_starting"
        }

        await asyncio.sleep(0.1)

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 30, 
            "message": f"Downloading content for '{metadata.get('title', f'Book {book_id}')}'...",
            "stage": "content_fetch"
        }

        content_start = time.time()
        content, content_error = await gutenberg_api.get_book_content(book_id)
        if content_error:
            book_fetch_tasks[book_id] = {
                "status": "error", 
                "message": content_error
            }
            return
            
        fetch_duration = time.time() - content_start

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 60, 
            "message": f"Content downloaded ({len(content)/1024:.1f} KB). Cleaning and processing...",
            "stage": "content_cleaning_starting"
        }

        await asyncio.sleep(0.1)

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 70, 
            "message": f"Cleaning and formatting book content...",
            "stage": "content_cleaning"
        }

        cleaned_content = gutenberg_api.clean_book_content(content)
        
        content_preview = cleaned_content[:5000] + "..." if len(cleaned_content) > 5000 else cleaned_content

        book_fetch_tasks[book_id] = {
            "status": "processing", 
            "progress": 90, 
            "message": f"Content processed, finalizing...",
            "stage": "finalizing"
        }

        await asyncio.sleep(0.1)

        book_result = {
            "metadata": metadata,
            "content_preview": content_preview,
            "content_length": len(cleaned_content)
        }

        book_cache[book_id] = {
            **book_result,
            "full_content": cleaned_content
        }

        total_duration = time.time() - start_time
        book_fetch_tasks[book_id] = {
            "status": "complete", 
            "progress": 100, 
            "message": f"Book '{metadata.get('title')}' successfully fetched and processed",
            "stage": "complete",
            "fetch_duration": fetch_duration,
            "total_duration": total_duration,
            "content_size": len(cleaned_content)
        }

    except Exception as e:
        logger.error(f"Error in book fetch for {book_id}: {str(e)}")
        book_fetch_tasks[book_id] = {
            "status": "error", 
            "message": f"Error during book fetch: {str(e)}"
        }
    finally:
        active_tasks.discard(task_id)

async def process_book_analysis_incremental(book_id: str, task_id: str):
    """Process book analysis incrementally, updating status as results come in"""
    try:

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 5, 
            "message": "Preparing analysis...",
            "stage": "initialization"
        }

        book_data = book_cache[book_id]

        async_gen = book_analyzer.analyze_book_incremental(
            book_data["full_content"], 
            book_data["metadata"]
        )

        await asyncio.sleep(0.1)
        
        async for update in async_gen:
            status_update = dict(update)

            if status_update["status"] == "processing":
                stage = status_update.get("stage", "")
                current_progress = status_update.get("progress", 0)
                
                if stage == "character_analysis_prep":
                    status_update["progress"] = max(current_progress, 10)
                elif stage == "character_analysis_complete":
                    status_update["progress"] = max(current_progress, 40)
                elif stage == "graph_generation":
                    status_update["progress"] = max(current_progress, 60)
                elif stage == "theme_analysis_complete":
                    status_update["progress"] = max(current_progress, 90)

            analysis_tasks[book_id] = status_update

            await asyncio.sleep(0.1)

            if update["status"] == "complete":
                analysis_cache[book_id] = update["partial_results"]
                break
    
    except Exception as e:
        logger.error(f"Error in book analysis for {book_id}: {str(e)}")
        analysis_tasks[book_id] = {
            "status": "error", 
            "message": f"Error during analysis: {str(e)}"
        }
    finally:
        active_tasks.discard(task_id)

async def process_book_analysis(book_id: str, task_id: str):
    """Process book analysis in traditional synchronous manner (kept for fallback)"""
    try:
        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 5, 
            "message": "Preparing analysis...",
            "stage": "initialization"
        }

        book_data = book_cache[book_id]
        book_title = book_data["metadata"]["title"]

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 15, 
            "message": f"Analyzing text structure for '{book_title}'",
            "stage": "text_processing"
        }
        await asyncio.sleep(0.2)

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 30, 
            "message": "Identifying characters and relationships",
            "stage": "character_analysis"
        }

        analysis_results, error = book_analyzer.analyze_book(
            book_data["full_content"], 
            book_data["metadata"]
        )
        
        if error:
            analysis_tasks[book_id] = {"status": "error", "message": error}
            return

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 70, 
            "message": "Building character network graph",
            "stage": "graph_generation"
        }
        await asyncio.sleep(0.2)

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 85, 
            "message": "Extracting themes and significant quotes",
            "stage": "theme_analysis"
        }
        await asyncio.sleep(0.2)

        analysis_tasks[book_id] = {
            "status": "processing", 
            "progress": 95, 
            "message": "Finalizing results",
            "stage": "finalization"
        }
        await asyncio.sleep(0.2)
        analysis_cache[book_id] = analysis_results

        analysis_tasks[book_id] = {
            "status": "complete", 
            "progress": 100, 
            "message": "Analysis complete",
            "stage": "complete"
        }
    
    except Exception as e:
        logger.error(f"Error in book analysis for {book_id}: {str(e)}")
        analysis_tasks[book_id] = {
            "status": "error", 
            "message": f"Error during analysis: {str(e)}"
        }
    finally:
        active_tasks.discard(task_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)