from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class Emotion(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    CALM = "calm"
    EXCITED = "excited"

class PetStage(str, Enum):
    EGG = "egg"
    BABY = "baby" 
    ADULT = "adult"
    LEGENDARY = "legendary"

# Models
class Pet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "MoodPet"
    stage: PetStage = PetStage.EGG
    happiness: int = 50
    health: int = 100
    coins: int = 100
    experience: int = 0
    last_fed: Optional[datetime] = None
    last_played: Optional[datetime] = None
    last_trained: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PetCreate(BaseModel):
    name: str = "MoodPet"

class PetUpdate(BaseModel):
    name: Optional[str] = None
    happiness: Optional[int] = None
    health: Optional[int] = None
    coins: Optional[int] = None

class MoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emotion: Emotion
    intensity: int = Field(default=5, ge=1, le=10)
    note: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pet_id: str

class MoodEntryCreate(BaseModel):
    emotion: Emotion
    intensity: int = Field(default=5, ge=1, le=10)
    note: Optional[str] = None
    pet_id: str

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    pet_id: str

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: int
    category: str
    icon: str

# Helper functions
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key in ['created_at', 'timestamp', 'last_fed', 'last_played', 'last_trained', 'unlocked_at']:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Pet Routes
@api_router.post("/pets", response_model=Pet)
async def create_pet(pet_data: PetCreate):
    pet_dict = Pet(name=pet_data.name).dict()
    pet_dict = prepare_for_mongo(pet_dict)
    await db.pets.insert_one(pet_dict)
    return Pet(**parse_from_mongo(pet_dict))

@api_router.get("/pets/{pet_id}", response_model=Pet)
async def get_pet(pet_id: str):
    pet = await db.pets.find_one({"id": pet_id})
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return Pet(**parse_from_mongo(pet))

@api_router.get("/pets", response_model=List[Pet])
async def get_all_pets():
    pets = await db.pets.find().to_list(1000)
    return [Pet(**parse_from_mongo(pet)) for pet in pets]

@api_router.put("/pets/{pet_id}", response_model=Pet)
async def update_pet(pet_id: str, pet_update: PetUpdate):
    update_data = {k: v for k, v in pet_update.dict().items() if v is not None}
    if update_data:
        await db.pets.update_one({"id": pet_id}, {"$set": update_data})
    
    pet = await db.pets.find_one({"id": pet_id})
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return Pet(**parse_from_mongo(pet))

# Pet Actions
@api_router.post("/pets/{pet_id}/feed")
async def feed_pet(pet_id: str):
    pet = await db.pets.find_one({"id": pet_id})
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    now = datetime.now(timezone.utc)
    updates = {
        "happiness": min(100, pet.get("happiness", 50) + 15),
        "health": min(100, pet.get("health", 100) + 10),
        "coins": pet.get("coins", 100) + 5,
        "experience": pet.get("experience", 0) + 10,
        "last_fed": now.isoformat()
    }
    
    await db.pets.update_one({"id": pet_id}, {"$set": updates})
    
    updated_pet = await db.pets.find_one({"id": pet_id})
    return {"message": "Pet fed successfully!", "pet": Pet(**parse_from_mongo(updated_pet))}

@api_router.post("/pets/{pet_id}/play")
async def play_with_pet(pet_id: str):
    pet = await db.pets.find_one({"id": pet_id})
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    now = datetime.now(timezone.utc)
    updates = {
        "happiness": min(100, pet.get("happiness", 50) + 20),
        "coins": pet.get("coins", 100) + 8,
        "experience": pet.get("experience", 0) + 15,
        "last_played": now.isoformat()
    }
    
    await db.pets.update_one({"id": pet_id}, {"$set": updates})
    
    updated_pet = await db.pets.find_one({"id": pet_id})
    return {"message": "Had fun playing!", "pet": Pet(**parse_from_mongo(updated_pet))}

@api_router.post("/pets/{pet_id}/train")
async def train_pet(pet_id: str):
    pet = await db.pets.find_one({"id": pet_id})
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    now = datetime.now(timezone.utc)
    updates = {
        "happiness": min(100, pet.get("happiness", 50) + 10),
        "health": min(100, pet.get("health", 100) + 5),
        "coins": pet.get("coins", 100) + 12,
        "experience": pet.get("experience", 0) + 25,
        "last_trained": now.isoformat()
    }
    
    # Check for evolution
    experience = updates["experience"]
    current_stage = pet.get("stage", "egg")
    
    if experience >= 300 and current_stage == "adult":
        updates["stage"] = "legendary"
    elif experience >= 150 and current_stage == "baby":
        updates["stage"] = "adult"
    elif experience >= 50 and current_stage == "egg":
        updates["stage"] = "baby"
    
    await db.pets.update_one({"id": pet_id}, {"$set": updates})
    
    updated_pet = await db.pets.find_one({"id": pet_id})
    return {"message": "Training completed!", "pet": Pet(**parse_from_mongo(updated_pet))}

# Mood Routes
@api_router.post("/moods", response_model=MoodEntry)
async def create_mood_entry(mood_data: MoodEntryCreate):
    mood_dict = MoodEntry(**mood_data.dict()).dict()
    mood_dict = prepare_for_mongo(mood_dict)
    await db.mood_entries.insert_one(mood_dict)
    
    # Update pet happiness based on mood
    pet = await db.pets.find_one({"id": mood_data.pet_id})
    if pet:
        happiness_change = 0
        if mood_data.emotion in [Emotion.HAPPY, Emotion.EXCITED, Emotion.CALM]:
            happiness_change = mood_data.intensity
        elif mood_data.emotion in [Emotion.SAD, Emotion.ANGRY, Emotion.ANXIOUS]:
            happiness_change = -mood_data.intensity // 2
        
        new_happiness = max(0, min(100, pet.get("happiness", 50) + happiness_change))
        coins_earned = 10 + mood_data.intensity
        
        await db.pets.update_one(
            {"id": mood_data.pet_id}, 
            {"$set": {"happiness": new_happiness}, "$inc": {"coins": coins_earned, "experience": 5}}
        )
    
    return MoodEntry(**parse_from_mongo(mood_dict))

@api_router.get("/moods/{pet_id}", response_model=List[MoodEntry])
async def get_mood_entries(pet_id: str):
    moods = await db.mood_entries.find({"pet_id": pet_id}).sort("timestamp", -1).to_list(100)
    return [MoodEntry(**parse_from_mongo(mood)) for mood in moods]

# Shop Routes
@api_router.get("/shop", response_model=List[ShopItem])
async def get_shop_items():
    # Default shop items
    default_items = [
        {"name": "Premium Food", "description": "Increases happiness by 25", "price": 50, "category": "food", "icon": "🍖"},
        {"name": "Toy Ball", "description": "Fun toy for playing", "price": 30, "category": "toy", "icon": "🏀"},
        {"name": "Training Weights", "description": "Boosts training effectiveness", "price": 75, "category": "training", "icon": "🏋️"},
        {"name": "Sparkle Background", "description": "Beautiful starry background", "price": 100, "category": "background", "icon": "✨"},
        {"name": "Rainbow Collar", "description": "Colorful pet accessory", "price": 60, "category": "accessory", "icon": "🌈"},
    ]
    
    existing_items = await db.shop_items.find().to_list(100)
    if not existing_items:
        for item_data in default_items:
            item = ShopItem(id=str(uuid.uuid4()), **item_data)
            await db.shop_items.insert_one(item.dict())
        
        existing_items = await db.shop_items.find().to_list(100)
    
    return [ShopItem(**item) for item in existing_items]

# Achievements
@api_router.get("/achievements/{pet_id}", response_model=List[Achievement])
async def get_achievements(pet_id: str):
    achievements = await db.achievements.find({"pet_id": pet_id}).to_list(100)
    
    # Create default achievements if none exist
    if not achievements:
        default_achievements = [
            {"name": "First Steps", "description": "Create your first pet", "icon": "🐣"},
            {"name": "Mood Tracker", "description": "Log 10 mood entries", "icon": "📊"},
            {"name": "Happy Pet", "description": "Reach 100 happiness", "icon": "😊"},
            {"name": "Evolution Master", "description": "Evolve to Adult stage", "icon": "🌟"},
            {"name": "Coin Collector", "description": "Earn 500 coins", "icon": "💰"},
        ]
        
        for ach_data in default_achievements:
            achievement = Achievement(pet_id=pet_id, **ach_data)
            await db.achievements.insert_one(achievement.dict())
        
        achievements = await db.achievements.find({"pet_id": pet_id}).to_list(100)
    
    return [Achievement(**parse_from_mongo(ach)) for ach in achievements]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()