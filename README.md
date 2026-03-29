
# DoppelBot - The Easy-to-Set-Up and Optimized Discord AI Bot that Clones Your Voice!

Have you ever wanted to clone and talk to a doppelgänger of yourself with AI? Now you can through Discord!


## Welcome!

This is a complete, GUI-driven Discord Bot program that clones your personality using your Discord chat history, and clones your voice using pocket-tts.

Everything is handled by a gui dashboard (either through the desktop program itself which is recommended, or through a website).

If you have zero coding experience, don't worry. I've simplified and streamlined everything so this install should be as pain-free as possible.

### Note: 
The initial setup does take a bit of time (I'd say around **25-30 minutes** depending on your computer.) It's a lot of gathering all the files required such as the AI models, which are a bit beefy. Most of that time is spend staring at a seemingly-frozen terminal, but I assure you that it isn't frozen. If you close the terminal while it's gathering all the required files prematurely, something may break. Just be patient!

## DoppelBot is very optimized for low-end PCs, and offloads as much as possible off your device itself. While working on this project, I had it running on my old Core i3-5020u CPU laptop with 16 gigs of ram from 2015 in the corner of my room and it worked great. The faster your computer, the faster the responses will typically be of course, but it works great on low-end hardware aswell!
[![JackBJ27 - doppelbot](https://img.shields.io/static/v1?label=JackBJ27&message=doppelbot&color=blue&logo=github)](https://github.com/JackBJ27/doppelbot "Go to GitHub repo")
[![stars - doppelbot](https://img.shields.io/github/stars/JackBJ27/doppelbot?style=social)](https://github.com/JackBJ27/doppelbot)
[![forks - doppelbot](https://img.shields.io/github/forks/JackBJ27/doppelbot?style=social)](https://github.com/JackBJ27/doppelbot)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue)](#license)
[![Buy me a coffee!](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/jackbj)


## Table of Contents

#### Features

- Step 1. The Required Software
- Step 2. Your Personal Data
- Step 3. Getting Your 3 Secret Keys
- Step 4. Putting It All Together
- Step 5. The GUI Dashboard

#### FAQ
#### Credits & Copyright
## Features

**Full GUI Dashboard** - Control everything from an app or web interface, instead of messing with editing py files

**Voice Cloning** - Joins voice channels, listens to what your friends say, and replies out loud using your *own voice*

**AI Brain** - DoppelBot is hooked up to Google's Gemma & Gemini models, so it can talk exactly like you do!

**Web Search** - DoppelBot can actively google things and read websites if someone asks it a question

**Auto-Chat & Auto-Join** - DoppelBot will randomly lurk in voice channels or randomly start conversations in text channels on its own if you enable the setting

**Custom Stat Tracker** - Tell DoppelBot to count how many times your friends say specific trigger words and announce it to the server

**API Key Rotation** - Add additional Google API Keys to bypass strict rate limits *(optional)*
## Step 1. The Required Software

You'll need four things installed on your computer before anything else.

### 1. Python 3.13
Go to python.org and download version 3.13. It **MUST** be version 3.13, other versions are incompatible with DoppelBot at the moment.

**CRITICAL STEP** - When you run the Windows installer, look at the very bottom of the window, and click the *"Add Python.exe to PATH"*. Also, at the end, it will ask if you want to disable the 260 PATH limit, I advise clicking yes.

### 2. Git
Go to git-scm.com and download it. Click next through the installer until it's installed. (Customizing it is not necessary)

### 3. Microsoft C++ Redistributable
DoppelBot's voice AI requires this to run on Windows without crashing. You can download and install it here: *https://aka.ms/vs/17/release/vc_redist.x64.exe*

Even if you have one of these installed, it requires this specific version of it.

### 4. FFmpeg
This helps DoppelBot actually process audio files.

**For Windows** - Open your terminal/cmd prompt *(Windows Key + R, and type cmd)*, and copy/paste this exact command:

`winget install Gyan.FFmpeg --exact --source winget`

Press Enter and let it install.

DoppelBot's code included FFmpeg, but this is the easier way to install it, the one included is just a required file.

## RESTART YOUR COMPUTER after installing these required files!
C++ and FFmpeg require a restart before actually working, so if you try to move on without a restart, it **will not work**!
## Step 2. Your Personal Data

The bot needs to know how you type and what you sound like to function.

### 1. Your Chat History
In Discord, go to **User Settings - Privacy & Safety - Request all of my Data**
This will most likely take a few days for Discord to email your data export to you.

When they do, download the .zip file they email you, extract it, and place the **messages** folder inside DoppelBot's included message folder. You'll be mining your data to create your AI "brain" and "soul" files later from your messages, don't worry about this now.

### 2. Your Voice
Download a program such as Audacity. Record yourself saying this paragraph with 7 different emotions to your voice.

**Yo, it's (your name here). I am recording this quick audio sample so the bot can clone my voice. Is this going to sound incredibly cursed? Yeah, probably. But I need to speak naturally, ask a question, and use a bunch of different syllables so the AI knows exactly how I talk. Hopefully this is enough data to make it work.**

This paragraph goes through all the syllables the AI will need to clone your voice, and the great part is, is that this is all it requires. A simple 15-20 second voice clip!

By recording this same paragraph in 7 different emotional states, it will bring a bit more life to your bot.
`normal` `sad` `angry` `dead inside` `excited` `anxious` and `bored`. Name them all `name_reference.wav` except for normal, which you'll just label as `reference.wav`. That will be your baseline voice.

**CRITICAL STEP** - You **MUST** export them as **Mono audio**, with the **Project Rate** (bottom left corner) to **16000 Hz** (16kHz). Discord can't process normal stereo audio files for some reason, so it will just crash outright if you keep them stereo and at the original Project Rate.


## Step 2. Your Personal Data

The bot needs to know how you type and what you sound like to function.

### 1. Your Chat History
In Discord, go to **User Settings - Privacy & Safety - Request all of my Data**
This will most likely take a few days for Discord to email your data export to you.

When they do, download the .zip file they email you, extract it, and place the **messages** folder inside DoppelBot's included message folder. You'll be mining your data to create your AI "brain" and "soul" files later from your messages, don't worry about this now.

### 2. Your Voice
Download a program such as Audacity. Record yourself saying this paragraph with 7 different emotions to your voice.

**Yo, it's (your name here). I am recording this quick audio sample so the bot can clone my voice. Is this going to sound incredibly cursed? Yeah, probably. But I need to speak naturally, ask a question, and use a bunch of different syllables so the AI knows exactly how I talk. Hopefully this is enough data to make it work.**

This paragraph goes through all the syllables the AI will need to clone your voice, and the great part is, is that this is all it requires. A simple 15-20 second voice clip!

By recording this same paragraph in 7 different emotional states, it will bring a bit more life to your bot.
`normal` `sad` `angry` `dead inside` `excited` `anxious` and `bored`. Name them all `name_reference.wav` except for normal, which you'll just label as `reference.wav`. That will be your baseline voice.

**CRITICAL STEP** - You **MUST** export them as **Mono audio**, with the **Project Rate** (bottom left corner) to **16000 Hz** (16kHz). Discord can't process normal stereo audio files for some reason, so it will just crash outright if you keep them stereo and at the original Project Rate.


## Step 2. Your Personal Data

The bot needs to know how you type and what you sound like to function.

### 1. Your Chat History
In Discord, go to **User Settings - Privacy & Safety - Request all of my Data**
This will most likely take a few days for Discord to email your data export to you.

When they do, download the .zip file they email you, extract it, and place the **messages** folder inside DoppelBot's included message folder. You'll be mining your data to create your AI "brain" and "soul" files later from your messages, don't worry about this now.

### 2. Your Voice
Download a program such as Audacity. Record yourself saying this paragraph with 7 different emotions to your voice.

**Yo, it's (your name here). I am recording this quick audio sample so the bot can clone my voice. Is this going to sound incredibly cursed? Yeah, probably. But I need to speak naturally, ask a question, and use a bunch of different syllables so the AI knows exactly how I talk. Hopefully this is enough data to make it work.**

This paragraph goes through all the syllables the AI will need to clone your voice, and the great part is, is that this is all it requires. A simple 15-20 second voice clip!

By recording this same paragraph in 7 different emotional states, it will bring a bit more life to your bot.
`normal` `sad` `angry` `dead inside` `excited` `anxious` and `bored`. Name them all `name_reference.wav` except for normal, which you'll just label as `reference.wav`. That will be your baseline voice.

**CRITICAL STEP** - You **MUST** export them as **Mono audio**, with the **Project Rate** (bottom left corner) to **16000 Hz** (16kHz). Discord can't process normal stereo audio files for some reason, so it will just crash outright if you keep them stereo and at the original Project Rate.


## Get Your 3 Secret Keys

You'll need 3 different keys to make this work.

### 1. Discord Token
This is when you create your bot. Go to the **Discord Developer Portal** `https://discord.com/developers/applications`.

Click **New Application**, and name your bot.

Go to the **Bot** tab on the left.

Scroll down and **turn on all 3 Privileged Gateway Intents** (Presence, Server Members, Message Content).

Click **Reset Token** and copy the long password it gives you into a notepad. 

This is just temporary, you won't be keeping it here. But make sure you label which is which as more keys will be temporarily stored here aswell.

### 2. Google Gemini Key(s)
Go to **Google AI Studio** `https://aistudio.google.com/app/apikey`.

Sign in with your Google account, click **Create New Project**, and then click **Create API Key**. Copy that to your notepad as well and label it.

*Optional: If you want to have the ability to rotate API keys, create multiple and copy them into your notepad, same as before.*

### 3. Hugging Face Token
Go to **Hugging Face** `https://huggingface.co/`.

Create an account on HuggingFace.

Search the website for **pocket-tts**, and you'll see a section at the top that has you agree to some terms to access their model.

Click **Agree to terms**.

Click your **Profile Picture** in the top right, click **Settings**, and then click **Access Tokens**.

Create a new token, set the type to **Write**, and copy that token as well to your notepad.
## Putting It All Together
Let's get the folder now which is where your bot will be stored in.

### 1. Download this entire repository
Click the green **Code** button, and then click **Download ZIP**. Extract it to your desktop, or wherever you want your bot to be stored.

Drag your **messages** folder from earlier directly into the bot folder.

 **Don't put your messages folder inside your messages folder, that will just create a nested folder which the program won't understand. All the folders in your discord export messages folder must be inside the "messages" folder.** (For example, if I clicked your messages folder, I would see a bunch of other folders, rather than another messages folder.)

 Drag your **7 voice references** into the **voice_references** folder.

**Note**: If you would like the bot to say phrases while it loads up, you may put files named `warming_up.wav`, `wait.wav`, `still_loading.wav`, and `almost_done.wav` into your `voice_references` folder, and it will rotate through those voice clips while the models start up. You can ALSO add `uhhh.wav`, `um.wav`, `hmmm.wav`, `sigh.wav`, `big_sigh.wav`, and `chatter.wav` to make the bot naturally stutter and sigh when the AI is thinking mid-sentence! Just keep in mind they all still must be *Mono* at *16000 Hz*.
## The GUI Dashboard

You're almost there! Launch your dashboard by clicking the **start_dashboard** file.

If you're on Windows, click the **.bat** file.

If you're on Mac/Linux, open your terminal, drag **start_dashboard.sh** into it, and press Enter.

**This is where the time sink happens.** The very first time you run this file, **it will take around 15-25 minutes** to download all the required files, libraries, and AI models.

**Please be patient.** I know staring at a seemingly frozen terminal sounds like a pain, but I can promise you that it's just gathering the files required in the background. *It will move to the* **"Dashboard" options** *once done, so if you don't see that, keep the terminal open and remain patient.*

When the option to choose between the desktop launcher and the web launcher pops up, choose one. I recommend using the desktop program as that is the one I worked on the most and is a bit more polished, but the web launcher works great aswell.

Paste your 3 keys into the top boxes upon start up. You can verify your keys by clicking the **Verify Keys** button to make sure they're working.

Once that is set up, you can start customizing the launcher to your hearts content.

**Note**: You will require various Discord IDs for your friends/channels, so to get the ability to view IDs, go to your **Discord Settings**, click **Advanced**, and then click **Developer Mode**. Once on, you'll be able to right click any member or channel on discord and copy the ID.

## One more step...
Go to the General & Keys tab, click "initial setup* at the top, and click **Mine Discord Data**. That will open up a terminal that will take all of your messages you've ever sent on Discord and put it into a single text file. That will be your **Brain**, which the AI uses to get the style of your messages from.

After that's done, click **Generate Soul**, and wait for that to process. It will take a bit if you have a ton of messages.

# You're done!

Once that's done, you can click "Start Bot". 

**Again, if this is your first time starting up the bot, it will take awhile to load up the AI models, so please be patient.** It may look frozen, but it *is not*. Just wait patiently, it will tell you when it's done.
## FAQ

#### **Q: The terminal opens and instantly closes when I hit start.**

A: You likely forgot to check "Add Python to PATH" during the Python install. Uninstall Python, run the installer again, and make sure that box is checked. Alternatively, you have multiple versions of Python on your computer, or have downloaded the wrong version of Python. It must be Python 3.13.

#### **Q: The voice sounds like static or immediately crashes.**

A: Your audio files are not properly formatted. They must be Mono, and exactly 16000 Hz. Use Audacity to fix them.

#### **Q: Can I run this 24/7?**

A: Yes, but keep in mind that the bot runs locally on your computer. If you turn off your PC or close the terminal associated with the bot, the bot goes offline. This is why I suggest having another spare computer host the bot. I've been tinkering around with this bot privately since early February '26 and have been running it on a spare laptop that has a Core i3-5020u with absolutely no issues. If you have a slow computer, don't worry, it's been optimized for that.

#### **Q: Privacy is a big concern for me. Should I be worried about this bot sending my voice chats to Google?**

A: I take privacy incredibly seriously. In voice channels, it records your voice, processes it to text, and sends it to Google for an answer. It gets the answer back, and then overwrites the response.wav it creates after you say something new. While there is a VC History feature, it's a self destructing feature which means it only keeps the last few sentences in the buffer before they get wiped from the file. The stats file is for fun and can be disabled at any time. Note that it's not saving your conversations, it searches for keywords from a specific person and if that person says that keyword, it changes the number associated with that stat. At this stage of the project, it's not configured to run locally. I don't have a beefy enough computer to test a local model, and offloading as much off device as possible is what makes it relatively speedy to respond to and run.
## Credits & Copyright

-  **Voice-compat module:** Sourced from the `discord-brain-rot` GitHub repository by GabrielAgrela.
-  **Font:** 'League Spartan' by Matt Bailey, Tyler Finck (OFL).

- ### Copyright (c) 2026 JackBJ. Licensed under the GPL-3.0 License.
