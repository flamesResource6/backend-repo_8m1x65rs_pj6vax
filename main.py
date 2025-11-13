import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Promo, NavigationItem, Collection, HeroSlide, Campaign, ShopTheLook
from database import db, create_document, get_documents

app = FastAPI(title="Rockflowerpaper Wholesale CMS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Rockflowerpaper Wholesale API running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# --------- CMS-like Endpoints ---------
# Helper to get single latest doc from a collection, or seed a default

def _get_singleton(collection: str, default_data: Dict[str, Any]) -> Dict[str, Any]:
    if db is None:
        # Return default if DB not configured
        return default_data
    doc = db[collection].find_one(sort=[("_id", -1)])
    if not doc:
        db[collection].insert_one(default_data.copy())
        return default_data
    doc["_id"] = str(doc["_id"])  # stringify
    return doc


def _upsert_singleton(collection: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if db is None:
        return payload
    existing = db[collection].find_one()
    if existing:
        db[collection].update_one({"_id": existing["_id"]}, {"$set": payload})
        updated = db[collection].find_one({"_id": existing["_id"]})
    else:
        db[collection].insert_one(payload)
        updated = db[collection].find_one()
    updated["_id"] = str(updated["_id"])  # type: ignore
    return updated


# Promo Banner
@app.get("/api/config/promo")
def get_promo():
    default = Promo(message="Reserve Now, Pay Later – Pre-Orders Ship Early February").model_dump()
    return _get_singleton("promo", default)


@app.put("/api/config/promo")
def put_promo(promo: Promo):
    return _upsert_singleton("promo", promo.model_dump())


# Navigation / Mega Menu (collections -> categories -> subcategories)
@app.get("/api/navigation")
def get_navigation():
    default_tree = [
        {"name": "Stories to Tell", "slug": "stories", "children": []},
        {"name": "Bags", "slug": "bags", "children": [
            {"name": "Totes", "slug": "totes"},
            {"name": "Crossbody", "slug": "crossbody"},
            {"name": "Pouches", "slug": "pouches"},
        ]},
        {"name": "Home", "slug": "home", "children": [
            {"name": "Decor", "slug": "decor"},
            {"name": "Throws", "slug": "throws"},
            {"name": "Tabletop", "slug": "tabletop"},
        ]},
        {"name": "Kitchen", "slug": "kitchen", "children": [
            {"name": "Tea Towels", "slug": "tea-towels"},
            {"name": "Aprons", "slug": "aprons"},
            {"name": "Serveware", "slug": "serveware"},
        ]},
        {"name": "Clothing", "slug": "clothing", "children": [
            {"name": "Dresses", "slug": "dresses"},
            {"name": "Tops", "slug": "tops"},
            {"name": "Kaftans", "slug": "kaftans"},
        ]},
        {"name": "Eco Living", "slug": "eco-living", "children": [
            {"name": "Blu Collection", "slug": "blu"},
            {"name": "Reusable", "slug": "reusable"},
        ]},
        {"name": "All Products", "slug": "all"},
        {"name": "Retail Displays", "slug": "retail-displays"}
    ]
    return _get_singleton("navigation", {"items": default_tree})


class NavigationPayload(BaseModel):
    items: List[NavigationItem]


@app.put("/api/navigation")
def put_navigation(payload: NavigationPayload):
    return _upsert_singleton("navigation", {"items": [i.model_dump() for i in payload.items]})


# Collections list (for tiles and rails)
@app.get("/api/collections")
def get_collections():
    default = [
        {"name": "Eco Collection", "slug": "eco", "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1600&auto=format&fit=crop"},
        {"name": "Home", "slug": "home", "image": "https://images.unsplash.com/photo-1505692794403-34cb7b57d23d?q=80&w=1600&auto=format&fit=crop"},
        {"name": "Clothing", "slug": "clothing", "image": "https://images.unsplash.com/photo-1503342217505-b0a15cf70489?q=80&w=1600&auto=format&fit=crop"},
        {"name": "Blu Collection", "slug": "blu", "image": "https://images.unsplash.com/photo-1520975682030-00ac1524f5a3?q=80&w=1600&auto=format&fit=crop"},
        {"name": "Bags", "slug": "bags", "image": "https://images.unsplash.com/photo-1520975960015-4f2a09f0b34b?q=80&w=1600&auto=format&fit=crop"},
        {"name": "Kitchen", "slug": "kitchen", "image": "https://images.unsplash.com/photo-1526318472351-c75fcf070305?q=80&w=1600&auto=format&fit=crop"}
    ]
    if db is None:
        return {"items": default}
    # Seed if empty
    if db["collection"].count_documents({}) == 0:
        for c in default:
            create_document("collection", c)
    items = get_documents("collection", {}, limit=None)
    # normalize
    for it in items:
        it["_id"] = str(it.get("_id"))
    return {"items": items}


# Hero slides
@app.get("/api/hero")
def get_hero():
    default = [
        {
            "title": "Spring '26 Coastal Stories",
            "description": "Easy, breezy pieces with a coastal soul.",
            "cta_label": "Shop Collection",
            "cta_href": "/collections/spring-26",
            "image": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=1600&auto=format&fit=crop"
        },
        {
            "title": "Eco-Friendly Essentials",
            "description": "Blu Collection: recycled, reusable, retailer-loved.",
            "cta_label": "Shop Blu",
            "cta_href": "/collections/blu",
            "image": "https://images.unsplash.com/photo-1526403226-eda5ebf4c11b?q=80&w=1600&auto=format&fit=crop"
        }
    ]
    return _get_singleton("hero", {"slides": default})


class HeroPayload(BaseModel):
    slides: List[HeroSlide]


@app.put("/api/hero")
def put_hero(payload: HeroPayload):
    return _upsert_singleton("hero", {"slides": [s.model_dump() for s in payload.slides]})


# Featured Rail
@app.get("/api/featured-rail")
def get_featured_rail():
    default = {
        "items": [
            {"name": "New Dresses", "slug": "dresses", "image": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=1600&auto=format&fit=crop"},
            {"name": "Tabletop", "slug": "tabletop", "image": "https://images.unsplash.com/photo-1494869042583-472f78114d3a?q=80&w=1600&auto=format&fit=crop"},
            {"name": "Totes", "slug": "totes", "image": "https://images.unsplash.com/photo-1518118432662-7230bc0fdd3f?q=80&w=1600&auto=format&fit=crop"},
            {"name": "Kaftans", "slug": "kaftans", "image": "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1600&auto=format&fit=crop"}
        ]
    }
    return _get_singleton("featured_rail", default)


@app.put("/api/featured-rail")
def put_featured_rail(payload: Dict[str, Any]):
    return _upsert_singleton("featured_rail", payload)


# Campaign banner
@app.get("/api/campaign")
def get_campaign():
    default = Campaign(
        title="Spring '26 Preview",
        subtitle="Pre-book your bestsellers early.",
        cta_label="Explore Spring '26 Preview",
        cta_href="/collections/spring-26",
        image="https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=2000&auto=format&fit=crop"
    ).model_dump()
    return _get_singleton("campaign", default)


@app.put("/api/campaign")
def put_campaign(payload: Campaign):
    return _upsert_singleton("campaign", payload.model_dump())


# Shop the Look
@app.get("/api/shop-the-look")
def get_shop_the_look():
    default = {
        "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=2000&auto=format&fit=crop",
        "hotspots": [
            {"title": "Striped Kaftan", "price": 58.0, "position": {"x": 28, "y": 62}, "image": "https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?q=80&w=800&auto=format&fit=crop"},
            {"title": "Woven Tote", "price": 24.0, "position": {"x": 64, "y": 58}, "image": "https://images.unsplash.com/photo-1520975960015-4f2a09f0b34b?q=80&w=800&auto=format&fit=crop"},
            {"title": "Shell Necklace", "price": 12.0, "position": {"x": 52, "y": 38}, "image": "https://images.unsplash.com/photo-1520975682030-00ac1524f5a3?q=80&w=800&auto=format&fit=crop"}
        ]
    }
    return _get_singleton("shop_the_look", default)


@app.put("/api/shop-the-look")
def put_shop_the_look(payload: ShopTheLook):
    return _upsert_singleton("shop_the_look", payload.model_dump())


# Utility: simple search suggestion stub (for demo)
@app.get("/api/search")
def search(q: Optional[str] = None):
    q = (q or "").strip().lower()
    if not q:
        return {"results": []}
    # naive filter from collections names as demo
    cols = get_collections()
    results = [
        {"label": it.get("name"), "href": f"/collections/{it.get('slug')}"}
        for it in cols.get("items", []) if q in it.get("name", "").lower()
    ][:6]
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
