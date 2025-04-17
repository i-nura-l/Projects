# 👗 wea-rCloth – Your Smart Wardrobe Assistant

**wea-rCloth** is a digital wardrobe management system built using **Streamlit** and **Airtable**, designed to help users organize clothing, generate outfit combinations, and visualize their personal style data. It supports real-time interaction, smart filtering, and lays the foundation for AI-based fashion recommendations.

---

## 👥 Team Members

- **Nurali Bakytbek uulu** – Project Management & Programming  
- **Aijan Tilekova** – Data Collection

---

## 🎯 Project Objectives

- Digitally organize clothing items by category, type, style, color, and season.
- Generate style- and season-compatible outfit combinations.
- Allow users to rate and favorite outfits.
- Visualize wardrobe insights with charts (pie, bar, scatter, line).
- Prepare backend and logic for future ML-based recommendations.

---

## 🛠️ Methodology

### 1. Data Storage & Management
- Used **Airtable** to store wardrobe and combination data (migrated from CSV).
- Data schema includes: Category, Type, Style, Color, Season, Image, Email.

### 2. Outfit Generation Logic
- Auto-generate outfits based on style and season filters.
- Manual combination builder for full user control.
- Ratings and favorites are stored per user.

### 3. Data Processing & Visualization
- Built with **pandas** for data manipulation.
- Visual insights via **matplotlib** and **seaborn**.

### 4. User Interface (Streamlit)
- Add/edit clothing items and profile settings (bio, avatar).
- View combinations, apply filters, and rate outfits.
- Admin panel for managing users and global data.

---

## 🌟 Novelty of Work (Kyrgyzstan & Beyond)

wea-rCloth is the **first fashion-tech prototype of its kind developed in Kyrgyzstan**. While global apps focus on e-commerce or AI styling, wea-rCloth emphasizes user-driven outfit generation, data insights, and local season-awareness. It merges fashion, technology, and user feedback into a single lightweight tool that fills a gap in the regional digital fashion space.

---

## 📊 Results & Discussion

- Users can create, update, and visualize their wardrobe in real time.
- Outfit generator produces valid combinations with minimal input.
- Admins can view global stats and manage user data securely.
- Data visualization reveals dominant styles and underused items.
- Limitations include lack of AI, image color analysis, and cloud media hosting.

---

## 🔮 Future Roadmap

- 🌦️ **Weather Integration** – Recommend outfits based on live weather via APIs  
- ☁️ **Cloud Media Storage** – Migrate image handling to Firebase or AWS S3  
- 🎨 **Color Detection** – Analyze image content for dominant clothing colors  
- 🤖 **AI Recommendations** – Learn user preferences and suggest personalized looks  
- 📱 **Mobile App Version** – Progressive Web App (PWA) or Flutter app  
- 🗓️ **Outfit Calendar** – Let users plan outfits for events or weekly wear  
- ♻️ **Sustainability Tracker** – Identify rarely worn items to suggest decluttering  

---

## ⏱️ Real-Time Applicability

wea-rCloth supports real-time use by allowing users to instantly manage clothing items, generate new combinations, and gain immediate insight into their wardrobe through dynamic charts and outfit ratings. Planned updates like weather APIs and cloud hosting will enhance this further for daily, practical use.

---

## ✅ Conclusion

**wea-rCloth** is a complete, scalable solution for intelligent wardrobe management. It allows users to go beyond simple clothing storage, offering decision-making support, visual insights, and a foundation for future intelligent recommendations. The system demonstrates strong real-world applicability, especially for users seeking a personal, data-informed fashion assistant.

---

## 🔗 Project Links

- **GitHub Repository:** https://github.com/i-nura-l/Projects/tree/main/wea-rCloth
- **Live Demo (optional):** https://wea-rcloth-app.streamlit.app/ 
- **Demo Video/Screenshots:** 

---

## 📚 References

- [Streamlit Documentation](https://docs.streamlit.io/)  
- [Airtable API Reference](https://airtable.com/api)  
- [pyAirtable GitHub](https://github.com/gtalarico/pyairtable)  
- [bcrypt Python Library](https://pypi.org/project/bcrypt/)  
- [pandas Documentation](https://pandas.pydata.org/docs/)  
- [Matplotlib](https://matplotlib.org/)  
- [Seaborn](https://seaborn.pydata.org/)  

---

*Made with ❤️ by students from Kyrgyzstan to combine fashion, data, and technology into one interactive platform.*
