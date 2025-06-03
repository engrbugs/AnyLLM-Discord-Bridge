# AnythingLLM Discord Bot

A Discord bot designed for AnythingLLM. This bot manages threads within a designated `discord` workspace. It can clear existing threads and create new ones, either upon starting or when the `!clear` command is invoked. It enables threaded conversations and allows users to check the bot's operational status using the `!ping` command. Configuration is managed through a `.env` file.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    ```
2.  **Install dependencies:**
    ```bash
    pip install discord.py python-dotenv requests
    ```
3.  **Create a `.env` file** in the root directory of the project with the following content:
    ```env
    DISCORD_TOKEN=your_discord_token
    ANYTHINGLLM_API_KEY=your_api_key
    ANYTHINGLLM_API_URL=http://localhost:3001/api/v1
    CHANNEL_ID=your_channel_id
    ```
4.  **Run the bot:**
    ```bash
    python main.py
    ```

## .env Variables

* `DISCORD_TOKEN`: Your Discord bot token. You can obtain this from the [Discord Developer Portal](https://discord.com/developers/applications). Ensure the Message Content Intent is enabled for your bot.
* `ANYTHINGLLM_API_KEY`: The API key for your AnythingLLM instance (e.g., `your_anythingllm_api_key_example`).
* `ANYTHINGLLM_API_URL`: The base URL for your AnythingLLM API (e.g., `http://localhost:3001/api/v1`).
* `CHANNEL_ID`: The ID of the Discord channel where the bot will operate (e.g., `your_discord_channel_id_example`). To get this, enable Developer Mode in Discord (User Settings > App Settings > Advanced), then right-click the channel and select "Copy ID".

## Commands

* `!ping`: Checks the status of the bot and the AnythingLLM API.
* `!clear`: Clears all existing threads in the `discord` workspace within AnythingLLM and creates a new, empty thread.
* **Messages (no command prefix):** Any message sent in the designated channel (that is not a command) will be forwarded to the latest active thread in the `discord` workspace of your AnythingLLM instance.

## Requirements

* Python 3.8 or newer.
* An instance of AnythingLLM running and accessible (default assumed `http://localhost:3001`).
* A Discord bot token with the Message Content Intent enabled.
* The ID of the Discord channel you want the bot to operate in.
* The Python packages listed in `requirements.txt` (primarily `discord.py`, `python-dotenv`, `requests`).

## License

This project is licensed under the MIT License.
