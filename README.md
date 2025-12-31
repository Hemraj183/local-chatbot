# EtherChat: Premium Local AI Terminal 🔮

A beautiful, high-tech fantasy-themed chatbot interface for **LM Studio**. Built with Streamlit and featuring Stripe-inspired glassmorphism, background art, and robust model management.

![EtherChat Full View](assets/screenshot_full.png)

## ✨ Features

- **Premium UI**: Dark mode with Stripe-style glassmorphism and animated fantasy backgrounds.
- **Neural Link Management**: Robust sidebar controls to Load, Purge (Unload), and track model state in real-time.
- **PDF & Image Support**: Drop vision-capable models to chat with images, or upload PDFs for instant knowledge extraction.
- **Thinking Indicator**: Visualizes the AI's internal "thought" process (supports `<think>` tags) with a mystical "Astral Reasoning" overlay.
- **Performance Metrics**: Real-time tracking of tokens per second (e/s), total tokens, and generation duration.
- **Responsive Design**: Optimized for both high-end laptops and mobile devices.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **LM Studio**: [Download here](https://lmstudio.ai/)
- **LMS CLI**: Ensure you have the `lms` command-line tool enabled (Options > CLI in LM Studio).

### 2. Install Dependencies
Run the following command in your terminal:
```bash
pip install streamlit openai pypdf
```

---

## 🚀 How to Start

### Option A: One-Click (Windows)
Simply run the included batch file:
- **Double-click `run_chatbot.bat`**
- This will automatically:
  1. Boot the LM Studio server (0.0.0.0).
  2. Auto-load the default AI model.
  3. Launch the EtherChat interface in your browser.

### Option B: Manual Startup
If you prefer the command line:
1. **Start the server**:
   ```bash
   lms server start --bind 0.0.0.0 --cors true
   ```
2. **Launch the app**:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```

---

## 📱 Local Network Access
EtherChat is built for cross-device usage. To access it from your **Phone or Tablet**:
1. Connect to the same WiFi as your computer.
2. Find your computer's local IP (the `.bat` file will show this).
3. Open your mobile browser and enter: `http://YOUR_IP_ADDRESS:8501`

---

## 📸 Screenshots

### Global Terminal (Chat)
![Chat Screenshot](assets/screenshot_chat.png)

## 🛡️ Model Control
The sidebar provides a **"Neural Core"** section where you can:
- **🔮 Load Core**: Safely unload previous models and boot up your selected AI.
- **💀 Purge Core**: Completely free up your RAM by offloading the model with verified API confirmation.
- **🔄 Sync List**: Instantly refresh your available models list if you download something new in LM Studio.

---
*Created for a seamless local AI experience. Powered by LM Studio & Streamlit.*
