# **Discord Message Deleter**

------------------------------------------------------------------------

## **Overview**

**Discord Message Deleter** is a desktop application built with
**PyQt5** that allows users to manage and delete their Discord messages
easily.  
The program provides a modern interface to browse guilds, select
channels, preview messages, and delete personal messages while tracking
progress in real time.

------------------------------------------------------------------------

## **Features**

-   **Login securely** using your Discord user token  
-   **View guilds and channels** you have access to  
-   **Preview messages** with an option to show only your own  
-   **Delete messages** in a single channel or across an entire server  
-   **Progress tracking** and live status updates  
-   **Dark theme** interface for a consistent look

------------------------------------------------------------------------

## **Requirements**

-   **Python 3.8** or later  

-   **Required packages:**

    ``` bash
    pip install PyQt5 requests
    ```

------------------------------------------------------------------------

## **Usage Instructions**

1.  Run the script:

    ``` bash
    python main.py
    ```

2.  Enter your **Discord token** and click **Login**.  

3.  Select a **Guild (Server)** from the list.  

4.  Choose a **Channel** to view or delete messages.  

5.  Available options:

    -   **Load Messages** — View recent messages (up to 500)  
    -   **Delete My Messages in Channel** — Delete your messages from
        the selected channel  
    -   **Delete My Messages in Guild** — Delete your messages from all
        text channels in the selected guild

------------------------------------------------------------------------

## **Important Notes**

-   The tool communicates directly with the **Discord API**.  
-   **Rate limits** are automatically respected.  
-   Only messages **authored by your account** will be deleted.  
-   Ensure you have the necessary **permissions** to access each channel
    before attempting deletions.

------------------------------------------------------------------------

## **Disclaimer**

This application is provided for **personal and educational purposes
only**.  
Use responsibly and in accordance with **Discord’s Terms of Service**.  
The authors assume **no liability** for misuse, account restrictions, or
data loss.

------------------------------------------------------------------------
