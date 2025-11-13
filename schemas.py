"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    image: Optional[str] = Field(None, description="Primary image URL")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Rockflowerpaper Wholesale - CMS-like Schemas

class Promo(BaseModel):
    message: str
    active: bool = True
    background: str = "#e6f4f1"
    text_color: str = "#0b3d3a"

class NavigationItem(BaseModel):
    name: str
    slug: str
    children: Optional[List["NavigationItem"]] = None

NavigationItem.model_rebuild()

class Collection(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[str] = None

class HeroSlide(BaseModel):
    title: str
    description: Optional[str] = None
    cta_label: str = "Shop Collection"
    cta_href: str = "/collections/all"
    image: str

class Campaign(BaseModel):
    title: str
    subtitle: Optional[str] = None
    cta_label: str = "Explore"
    cta_href: str = "/collections/spring-preview"
    image: str

class HotspotProduct(BaseModel):
    product_id: Optional[str] = None
    title: str
    price: Optional[float] = None
    image: Optional[str] = None
    position: Dict[str, float]  # {"x":0-100, "y":0-100} percentages

class ShopTheLook(BaseModel):
    image: str
    hotspots: List[HotspotProduct]
