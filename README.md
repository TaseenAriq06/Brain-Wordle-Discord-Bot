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

### 🛠️ Utilities
* **`!nyt [optional: number]`**: Connects to the **New York Times API** to retrieve the official daily answer. You can also look up past puzzles (e.g., `!nyt 100`) or specific dates. *Spoiler tags included!*
* **`!unscramble [LETTERS]`**: Uses an anagram algorithm to find all valid 5-letter words from a scrambled input. Great for when you are stuck!
* **`!help`**: Displays a clean embed listing all available commands.

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
