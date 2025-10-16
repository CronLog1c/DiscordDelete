Discord Message Deleter

Overview

Discord Message Deleter is a desktop application built with PyQt5 that
allows users to manage and delete their messages from Discord.
It provides an intuitive interface to browse guilds, select channels,
view messages, and delete personal messages either per channel or across
an entire server.

Features

-   Login using your Discord token
-   View and manage your guilds and channels
-   Load and display recent messages (with optional filtering for your
    own messages)
-   Delete personal messages from a specific channel or entire guild
-   Live progress tracking and status logs
-   Dark themed user interface for better readability

Requirements

-   Python 3.8 or later

-   Required Python packages:

        pip install PyQt5 requests

Usage

1.  Run the script:

        python main.py

2.  Enter your Discord user token and click Login.

3.  Select a guild (server) from the list.

4.  Select a channel to view messages or delete your messages.

5.  Use:

    -   Load Messages to preview messages
    -   Delete My Messages in Channel to remove your messages from the
        selected channel
    -   Delete My Messages in Guild to remove your messages from all
        text channels in the selected guild

Notes

-   This tool communicates directly with the Discord API.
-   Rate limits are respected automatically.
-   Only messages authored by the logged-in user are deleted.
-   Ensure you have permission to access the channels before running
    deletions.

Disclaimer

This project is provided for personal and educational purposes only.
The authors are not responsible for any misuse, account restrictions, or
data loss.
Use responsibly and in accordance with Discord’s terms of service.
