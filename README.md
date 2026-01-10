![Brain Wordle Banner](https://github.com/TaseenAriq06/Brain-Wordle-Discord-Bot/blob/9bd5514932bcf05b360fb3d9e297317a8c8c335a/assets/save.jpg)
# 🧠 Brain Wordle - Discord Bot

> A fully functional Discord bot that brings the popular Wordle game directly into your server. Built with Python and the Discord API.

## 📖 Overview

**Brain Wordle** is an interactive Discord bot that allows users to play unlimited games of Wordle, solve anagrams, and check the official New York Times daily solution. It features per-user state management, allowing multiple members to play their own private games simultaneously in the same channel without interference.

## ✨ Features

### 🎮 Unlimited Gameplay
* **`!play`**: Starts a new game with a secret 5-letter word selected from a dictionary of 3,000+ words.
* **`!guess [WORD]`**: Submits a guess. The bot provides instant feedback using emojis:
    * 🟩 **Green**: Correct letter, correct spot.
    * 🟨 **Yellow**: Correct letter, wrong spot.
    * ⬜ **White**: Letter not in the word.
* **Visual Interface**: The board updates dynamically, showing "Found Letters" and "Valid Letters" at the top for easy tracking.

  ![Brain Wordle Hint](https://github.com/TaseenAriq06/Brain-Wordle-Discord-Bot/blob/5c1ac801f22dd6a1e896256ec92e5a8ac3d8d6b1/assets/visual.webp)
  <img src="https://github.com/TaseenAriq06/Brain-Wordle-Discord-Bot/blob/f4f2175546776c768702637a862df1a0d4d8fce2/assets/stats.webp" width="200" height="200" />

### 🛠️ Utilities
| Command | Usage | Description |
| :--- | :--- | :--- |
| **!help** | `!help` | Displays a custom embed listing all available commands. |
| **!play** | `!play` | Starts a new, private Wordle game session for the user. |
| **!guess** | `!guess [word]` | Submits a 5-letter word attempt. Returns the board with emojis indicating letter accuracy (🟩 Green, 🟨 Yellow, ⬜ Gray). |
| **!stats** | `!stats` | Displays your personal win/loss record, win percentage, and streak history. |
| **!surrender** | `!surrender` | Gives up on the current word to reveal the answer (Counts as a loss). |
| **!hint**| `!hint` | Scans the dictionary using your current Green, Yellow, and Gray clues to suggest valid words that fit your specific puzzle. |
| **!nyt** | `!nyt` | Connects to the NYT API to retrieve the *official* Wordle answer for the current date (hidden behind a spoiler tag). |

---

## 🗺️ Roadmap & Future Goals
### This project is currently in **active development**. Here are the planned updates:

* Cloud Deployment: Migrate from local hosting to a 24/7 cloud service (Discloud or Railway).
* UI Overhaul: enhance the !play interface with Discord Embeds for a cleaner look.
* Stats System: Track user wins, streaks, and average guess counts using a JSON file ✅

---

## 🚀 Installation & Setup

If you want to run this bot on your own machine, follow these steps:

### Prerequisites
* Python 3.8 or higher
* A Discord Bot Token (from the [Discord Developer Portal](https://discord.com/developers/applications))

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/Brain-Wordle-Bot.git](https://github.com/YOUR_USERNAME/Brain-Wordle-Bot.git)
cd Brain-Wordle-Bot
