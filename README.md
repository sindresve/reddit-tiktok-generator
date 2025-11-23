# 📘 Project Setup Guide

This project generates reddit styled tiktok story videos from YouTube transcripts and uses background videos for final output processing. Follow the steps below to set up the environment and run the program correctly.

---

## ✅ 1. Install Python (Correct Version Required)

Make sure you have **Python 3.10 or 3.11** installed (depending on what your project needs).

Check your version:

```bash
python --version
```

If it’s not the required version, download it from:
[https://www.python.org/downloads/](https://www.python.org/downloads/)

---

## ✅ 2. Create and Activate a Virtual Environment

### **Windows**

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

You should now see `(.venv)` in your terminal prompt.

---

## ✅ 3. Install Dependencies

With the virtual environment active, install all required packages:

```bash
pip install -r requirements.txt
```

---

## ✅ 4. Add Background Videos

Inside your project, you’ll nned to create a folder named:

```
videos/
```

Add **2–10 minute long background videos** to this folder.
These will be used during the final rendering process.

Currently only supporting `.mp4`.

---

## ✅ 5. Running the Program

Run the script using:

```bash
python main.py <youtube_url> <output_name>
```

---

## 📄 How It Works (Script Overview)

Your `main.py` expects **two arguments**:

| Argument      | Description                       |
| ------------- | --------------------------------- |
| `youtube_url` | The URL of the YouTube video      |
| `output_name` | The name of the output video file |

Internally, it calls:

## ⚠️ Error Handling

If required arguments are missing:

```
Missing arguments: youtube_url or output_name
```

If transcript fetching fails, the program exits with an error message.

---

## 🎉 You're Ready!

Once everything is installed, videos added, and the command is run, your video should be created automatically.
