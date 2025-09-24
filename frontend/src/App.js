import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const emotions = [
  { name: "happy", icon: "😊", color: "#FFD700" },
  { name: "sad", icon: "😢", color: "#4682B4" },
  { name: "angry", icon: "😠", color: "#DC143C" },
  { name: "anxious", icon: "😰", color: "#FF6347" },
  { name: "calm", icon: "😌", color: "#98FB98" },
  { name: "excited", icon: "🤩", color: "#FF69B4" }
];

const petStages = {
  egg: { icon: "🥚", name: "Egg" },
  baby: { icon: "🐣", name: "Baby" },
  adult: { icon: "🦄", name: "Adult" },
  legendary: { icon: "🐉", name: "Legendary" }
};

function App() {
  const [pet, setPet] = useState(null);
  const [moods, setMoods] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [shopItems, setShopItems] = useState([]);
  const [showMoodTracker, setShowMoodTracker] = useState(false);
  const [showShop, setShowShop] = useState(false);
  const [showAchievements, setShowAchievements] = useState(false);
  const [notification, setNotification] = useState("");
  const [petAnimation, setPetAnimation] = useState("");

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Get existing pets
      const petsResponse = await axios.get(`${API}/pets`);
      if (petsResponse.data.length > 0) {
        const existingPet = petsResponse.data[0];
        setPet(existingPet);
        await loadPetData(existingPet.id);
      } else {
        // Create new pet
        const newPetResponse = await axios.post(`${API}/pets`, { name: "MoodPet" });
        setPet(newPetResponse.data);
        await loadPetData(newPetResponse.data.id);
      }
    } catch (error) {
      console.error("Failed to initialize app:", error);
      showNotification("Failed to load app data");
    }
  };

  const loadPetData = async (petId) => {
    try {
      const [moodsResponse, achievementsResponse, shopResponse] = await Promise.all([
        axios.get(`${API}/moods/${petId}`),
        axios.get(`${API}/achievements/${petId}`),
        axios.get(`${API}/shop`)
      ]);
      
      setMoods(moodsResponse.data);
      setAchievements(achievementsResponse.data);
      setShopItems(shopResponse.data);
    } catch (error) {
      console.error("Failed to load pet data:", error);
    }
  };

  const showNotification = (message) => {
    setNotification(message);
    setTimeout(() => setNotification(""), 3000);
  };

  const handlePetAction = async (action) => {
    if (!pet) return;
    
    try {
      const response = await axios.post(`${API}/pets/${pet.id}/${action}`);
      setPet(response.data.pet);
      showNotification(response.data.message);
      
      // Animate pet
      setPetAnimation(action);
      setTimeout(() => setPetAnimation(""), 1000);
    } catch (error) {
      console.error(`Failed to ${action}:`, error);
      showNotification(`Failed to ${action} pet`);
    }
  };

  const handleMoodEntry = async (emotion, intensity) => {
    if (!pet) return;
    
    try {
      await axios.post(`${API}/moods`, {
        emotion: emotion.name,
        intensity: intensity,
        pet_id: pet.id
      });
      
      // Refresh pet data
      const petResponse = await axios.get(`${API}/pets/${pet.id}`);
      setPet(petResponse.data);
      
      await loadPetData(pet.id);
      showNotification(`Mood logged! Your pet feels your ${emotion.name} energy!`);
      setShowMoodTracker(false);
    } catch (error) {
      console.error("Failed to log mood:", error);
      showNotification("Failed to log mood");
    }
  };

  const renamePet = async () => {
    const newName = prompt("Enter new name for your pet:", pet.name);
    if (newName && newName !== pet.name) {
      try {
        await axios.put(`${API}/pets/${pet.id}`, { name: newName });
        setPet({ ...pet, name: newName });
        showNotification(`Pet renamed to ${newName}!`);
      } catch (error) {
        console.error("Failed to rename pet:", error);
        showNotification("Failed to rename pet");
      }
    }
  };

  const MoodTracker = () => (
    <div className="modal">
      <div className="modal-content">
        <h2>How are you feeling?</h2>
        <div className="emotion-grid">
          {emotions.map((emotion) => (
            <div
              key={emotion.name}
              className="emotion-card"
              style={{ borderColor: emotion.color }}
              onClick={() => {
                const intensity = Math.floor(Math.random() * 5) + 5; // Random 5-10
                handleMoodEntry(emotion, intensity);
              }}
            >
              <div className="emotion-icon">{emotion.icon}</div>
              <div className="emotion-name">{emotion.name}</div>
            </div>
          ))}
        </div>
        <button onClick={() => setShowMoodTracker(false)} className="close-btn">Close</button>
      </div>
    </div>
  );

  const Shop = () => (
    <div className="modal">
      <div className="modal-content">
        <h2>🛍️ Pet Shop</h2>
        <div className="shop-grid">
          {shopItems.map((item) => (
            <div key={item.id} className="shop-item">
              <div className="item-icon">{item.icon}</div>
              <div className="item-name">{item.name}</div>
              <div className="item-description">{item.description}</div>
              <div className="item-price">💰 {item.price}</div>
              <button 
                className="buy-btn"
                disabled={!pet || pet.coins < item.price}
                onClick={() => showNotification("Item purchased! (Shop system coming soon)")}
              >
                Buy
              </button>
            </div>
          ))}
        </div>
        <button onClick={() => setShowShop(false)} className="close-btn">Close</button>
      </div>
    </div>
  );

  const Achievements = () => (
    <div className="modal">
      <div className="modal-content">
        <h2>🏆 Achievements</h2>
        <div className="achievements-grid">
          {achievements.map((achievement) => (
            <div 
              key={achievement.id} 
              className={`achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}`}
            >
              <div className="achievement-icon">{achievement.icon}</div>
              <div className="achievement-name">{achievement.name}</div>
              <div className="achievement-description">{achievement.description}</div>
            </div>
          ))}
        </div>
        <button onClick={() => setShowAchievements(false)} className="close-btn">Close</button>
      </div>
    </div>
  );

  if (!pet) {
    return (
      <div className="app">
        <div className="loading">
          <div className="loading-pet">🥚</div>
          <p>Loading your MoodPet...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>🐾 MoodPet</h1>
        <div className="stats">
          <div className="stat">💰 {pet.coins}</div>
          <div className="stat">❤️ {pet.happiness}/100</div>
          <div className="stat">🏥 {pet.health}/100</div>
        </div>
      </header>

      {/* Pet Display */}
      <div className="pet-container">
        <div className="pet-info">
          <h2 onClick={renamePet} className="pet-name">{pet.name}</h2>
          <div className="pet-stage">{petStages[pet.stage].name}</div>
          <div className="experience-bar">
            <div className="experience-fill" style={{width: `${Math.min(100, (pet.experience / 300) * 100)}%`}}></div>
            <span className="experience-text">XP: {pet.experience}/300</span>
          </div>
        </div>
        
        <div className={`pet-display ${petAnimation}`}>
          <div className="pet-emoji">{petStages[pet.stage].icon}</div>
          {pet.happiness > 70 && <div className="happiness-particles">✨</div>}
        </div>

        <div className="pet-actions">
          <button onClick={() => handlePetAction('feed')} className="action-btn feed">
            🍖 Feed
          </button>
          <button onClick={() => handlePetAction('play')} className="action-btn play">
            🏀 Play
          </button>
          <button onClick={() => handlePetAction('train')} className="action-btn train">
            🏋️ Train
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="navigation">
        <button onClick={() => setShowMoodTracker(true)} className="nav-btn">
          📊 Track Mood
        </button>
        <button onClick={() => setShowShop(true)} className="nav-btn">
          🛍️ Shop
        </button>
        <button onClick={() => setShowAchievements(true)} className="nav-btn">
          🏆 Achievements
        </button>
      </nav>

      {/* Modals */}
      {showMoodTracker && <MoodTracker />}
      {showShop && <Shop />}
      {showAchievements && <Achievements />}

      {/* Notification */}
      {notification && (
        <div className="notification">
          {notification}
        </div>
      )}

      {/* Recent Moods */}
      {moods.length > 0 && (
        <div className="recent-moods">
          <h3>Recent Moods</h3>
          <div className="mood-history">
            {moods.slice(0, 5).map((mood, index) => (
              <div key={mood.id} className="mood-entry">
                <span>{emotions.find(e => e.name === mood.emotion)?.icon}</span>
                <span>{new Date(mood.timestamp).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;