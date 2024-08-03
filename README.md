
# Reddit Video Generator

This project is a Reddit video generator that creates video compilations of top comments from a specified subreddit. It utilizes Python scripts and several APIs to fetch comments, convert them to audio, and combine them with videos and images. The final video is uploaded to YouTube.

## Features

- Fetches top comments from a specified subreddit using the Reddit API.
- Converts text to speech using the StreamElements API.
- Captures screenshots of comments using Selenium.
- Creates videos using MoviePy, integrating audio and images.
- Uploads the final video to YouTube via the YouTube Data API.

## Requirements

Before running the project, ensure you have the following software installed:

- Python 3.7 or later
- [Geckodriver](https://github.com/mozilla/geckodriver/releases) for Selenium
- [Firefox](https://www.mozilla.org/en-US/firefox/new/) browser

### Python Dependencies

All required Python packages are listed in `requirements.txt`. You can install them using the following command:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.json` file based on the provided `config_example.json`. Fill in the necessary details such as API keys, file paths, and other configuration settings.

### Example `config.json`

```json
{
    "client_id": "client_id_here",
    "client_secret": "client_secret_here",
    "user_agent": "pc:com.example.myredditapp:v1.2.3",
    "client_secrets_file": "youtube_secrets.json file here",
    "firefox_profile_path": "FireFox profile path here",
    "geckodriver_path": "Absolute path to 'geckodriver' seen in the directory",
    "temp_path": "Absolute path to 'temp' (create a folder named temp, copy it's absolute path and paste it here then delete the folder if you want)",
    "background_video_path": "mc.mp4",
    "video_title": "[post_title] #shorts #questions #redditvideos",
    "video_description": "Description goes here.",
    "video_tags": ["redditvideos", "questions", "shorts"],
    "video_category_id": "22",
    "privacy_status": "public",
    "window_width": "460",
    "window_height": "890",
    "scopes": [
        "https://www.googleapis.com/auth/youtube.upload"
    ],
    "number_of_posts_to_iterate": "12",
    "rounded_corners_radius": "14"
}
```

## Usage

1. **Set Up the Environment**

   - Ensure all dependencies are installed.
   - Update the `config.json` file with the appropriate credentials and settings.

2. **Run the Script**

   Execute the main script to generate and upload the video:

   ```bash
   python main.py
   ```

3. **Video Output**

   - The script generates a video compilation of Reddit comments and uploads it to YouTube.

## Important Notes

- Ensure that your Reddit and YouTube API credentials are correctly set up and stored in the `config.json`.
- Selenium requires a valid Firefox profile and the geckodriver to be set in the config.
- Ensure the `temp` directory path is correct and writable by the script.

## Contributing

Contributions are welcome! Please follow these guidelines when contributing:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Write clear, concise commit messages.
4. Ensure the code is well-documented and tested.
5. Submit a pull request with a description of your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

- [PRAW: The Python Reddit API Wrapper](https://praw.readthedocs.io/en/latest/)
- [StreamElements TTS API](https://streamelements.com/dashboard/bot/settings/tts)
- [Google API Client](https://github.com/googleapis/google-api-python-client)
- [MoviePy](https://zulko.github.io/moviepy/)
- [Selenium](https://www.selenium.dev/)
