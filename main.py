import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from database import create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Health
# ---------------------------
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ---------------------------
# Models
# ---------------------------
class ContactMessageIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=5000)


class Project(BaseModel):
    title: str
    location: Optional[str] = None
    image: Optional[str] = None


# ---------------------------
# Contact
# ---------------------------
@app.post("/api/contact")
def submit_contact(msg: ContactMessageIn):
    try:
        doc_id = create_document("contact_messages", msg)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Projects
# ---------------------------
DEFAULT_PROJECTS = [
    {
        "title": "Courtyard Residence",
        "location": "Lisbon, Portugal",
        "image": "https://images.unsplash.com/photo-1501045661006-fcebe0257c3f?q=80&w=1600&auto=format&fit=crop",
    },
    {
        "title": "Gallery Pavilion",
        "location": "Copenhagen, Denmark",
        "image": "https://images.unsplash.com/photo-1529429612777-95c0d0f2ad32?q=80&w=1600&auto=format&fit=crop",
    },
    {
        "title": "Cliff House",
        "location": "Big Sur, USA",
        "image": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?q=80&w=1600&auto=format&fit=crop",
    },
    {
        "title": "Cultural Center",
        "location": "Kyoto, Japan",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1600&auto=format&fit=crop",
    },
]


@app.get("/api/projects", response_model=List[Project])
def list_projects():
    try:
        docs = get_documents("projects")
        if not docs:
            return [Project(**p) for p in DEFAULT_PROJECTS]
        items: List[Project] = []
        for d in docs:
            # Map Mongo doc to Project fields
            items.append(Project(
                title=d.get("title") or d.get("name") or "Untitled",
                location=d.get("location"),
                image=d.get("image") or d.get("image_url"),
            ))
        return items
    except Exception:
        # On any DB error, gracefully fall back to static defaults
        return [Project(**p) for p in DEFAULT_PROJECTS]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
