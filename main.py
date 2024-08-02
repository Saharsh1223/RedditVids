import os
import json
import shutil
import praw
import time
import random
from pyt2s.services import stream_elements
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip, ImageClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pydub import AudioSegment
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw

TEMP_FOLDER = 'temp'

def create_temp_folder():
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
        
def get_audio(text, path):
    data = stream_elements.requestTTS(f'{text}', stream_elements.Voice.Brian.value)
    with open(f'{path}', '+wb') as file:
        file.write(data)

def load_config(config_path='config.json'):
    print("Loading configuration...")
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    print(f"Configuration loaded")
    return config

def get_top_comments_details(reddit, post_url=None, subreddit_name='AskReddit', max_duration=59.5):
    print("Fetching top comments details...")
    subreddit = reddit.subreddit(subreddit_name)
    posts = [submission for submission in subreddit.hot(limit=(int(load_config()['number_of_posts_to_iterate']))) if not submission.over_18]

    if not posts:
        raise Exception("No suitable non-NSFW posts found")

    submission = random.choice(posts) if post_url is None else reddit.submission(url=post_url)

    if submission is None or submission.over_18:
        raise Exception("No suitable post found or post is NSFW")

    submission.comment_sort = 'top'
    submission.comments.replace_more(limit=0)
    comments_details = []
    total_duration = 0

    for comment in submission.comments:
        if round(total_duration, 2) >= max_duration:
            break
        comment_details = {
            'post_id': f't3_{submission.id}',
            'comment_id': f't1_{comment.id}',
            'comment_url': f"https://www.reddit.com{comment.permalink}",
            'comment_score': comment.score,
            'comment_text': comment.body,
            'post_title': submission.title
        }
        get_audio(comment_details['comment_text'], os.path.join(TEMP_FOLDER, f"{comment_details['comment_id']}.mp3"))
        comment_duration = MP3(os.path.join(TEMP_FOLDER, f"{comment_details['comment_id']}.mp3")).info.length
        if total_duration + comment_duration > max_duration:
            break
        total_duration += comment_duration
        comments_details.append(comment_details)
        print(total_duration)

    print(f"Top comments details fetched: {comments_details}")
    return comments_details

def setup_selenium(options_path, geckodriver_path):
    print("Setting up Selenium...")
    options = Options()
    options.profile = options_path
    #options.add_argument('--headless')
    service = Service(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    print("Selenium setup complete.")
    return driver

def screenshot_element(driver, selector, output_path):
    print(f"Taking screenshot of element with selector: {selector}")
    element = driver.find_element(By.CSS_SELECTOR, selector)
    element.screenshot(output_path)
    print(f"Screenshot saved to: {output_path}")

def generate_random_clip(video_path, output_path, duration):
    print(f"Generating random clip from video: {video_path}")
    original_clip = VideoFileClip(video_path)
    duration = min(duration, original_clip.duration)
    start_time = random.uniform(0, original_clip.duration - duration)
    ffmpeg_extract_subclip(video_path, start_time, start_time + duration, targetname=output_path)
    original_clip.close()
    print(f"Random clip generated and saved to: {output_path}")

def concatenate_audio(audio_files, output_file):
    print(f"Concatenating audio files: {audio_files}")
    combined = AudioSegment.empty()
    for audio_file in audio_files:
        combined += AudioSegment.from_file(audio_file)
    combined.export(output_file, format='mp3')
    print(f"Concatenated audio saved to: {output_file}")

def add_audio_to_video(video_file, audio_file, output_file):
    print(f"Adding audio to video: {video_file} with audio: {audio_file}")
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)
    video_with_audio = video.set_audio(audio)
    video_with_audio.write_videofile(output_file, codec='libx264', audio_codec='aac')
    print(f"Video with audio saved to: {output_file}")

def process_video_with_audio(video_file, audio_files, output_file):
    concatenated_audio_path = os.path.join(TEMP_FOLDER, 'concatenated_audio.mp3')
    concatenate_audio(audio_files, concatenated_audio_path)
    add_audio_to_video(video_file, concatenated_audio_path, output_file)
    print("Audio and video processing complete.")

def create_rounded_image_clip(image_path, duration, radius):
    """Create an ImageClip with rounded corners."""
    # Open the image using Pillow
    with Image.open(image_path) as img:
        # Create a mask with the same size as the image
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        # Draw a rounded rectangle on the mask
        draw.rounded_rectangle((0, 0, img.width, img.height), radius=radius, fill=255)
        # Apply the mask to the image
        img.putalpha(mask)
        
        # Save the image with rounded corners
        rounded_image_path = os.path.join(TEMP_FOLDER, 'rounded_' + os.path.basename(image_path))
        img.save(rounded_image_path)
        
        # Load the image into MoviePy
        rounded_clip = ImageClip(rounded_image_path, duration=duration)
        return rounded_clip
    
def create_final_video(output_path, title_image, comment_images, video_background, title_duration, comment_durations, comments_details, radius=12):
    print("Creating final video...")
    video_clip = VideoFileClip(video_background).subclip(0, title_duration + sum(comment_durations))
    video_width, video_height = video_clip.size

    title_img_clip = create_rounded_image_clip(os.path.join(TEMP_FOLDER, title_image), duration=title_duration, radius=radius+6).set_position('center').resize(width=video_width-(2*16))
    comment_img_clips = [create_rounded_image_clip(comment_image, duration=comment_duration, radius=radius).set_position('center').resize(width=video_width-(2*24))
                         for comment_image, comment_duration in zip(comment_images, comment_durations)]
    
    final_clip = concatenate_videoclips([title_img_clip] + comment_img_clips)
    final_video = CompositeVideoClip([video_clip.set_opacity(0.6), final_clip.set_position('center')])
    final_video.write_videofile(output_path, fps=60, codec='libx264')
    time.sleep(1)
    print("Done with creating video. Adding audio to video.")
    audio_files = [os.path.join(TEMP_FOLDER, 'postTitle.mp3')] + [os.path.join(TEMP_FOLDER, f"{comment['comment_id']}.mp3") for comment in comments_details]
    process_video_with_audio(os.path.join(TEMP_FOLDER, 'output_video.mp4'), audio_files, 'final_video.mp4')
    print(f"Final video saved to: {output_path}")

def upload_video(youtube, video_file, title, description, tags, category_id, privacy_status):
    print(f"Uploading video: {video_file} to YouTube")
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if 'id' in response:
            print(f'Video uploaded successfully: https://youtu.be/{response["id"]}')
        elif 'error' in response:
            raise Exception(f'An error occurred: {response["error"]["message"]}')

def main():
    create_temp_folder()
    config = load_config()

    reddit = praw.Reddit(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        user_agent=config['user_agent']
    )

    start_time = time.time()
    comments_details = get_top_comments_details(reddit)
    print(f"Fetched top comments details in {time.time() - start_time:.2f} seconds")

    for comment in comments_details:
        for key, value in comment.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

    get_audio(comments_details[0]['post_title'], os.path.join(TEMP_FOLDER, 'postTitle.mp3'))

    driver = setup_selenium(
        options_path=config['firefox_profile_path'],
        geckodriver_path=config['geckodriver_path']
    )

    driver.set_window_size(int(config['window_width']), int(config['window_height']))

    driver.get(comments_details[0]['comment_url'])
    screenshot_element(driver, f"shreddit-post[id='{comments_details[0]['post_id']}']", os.path.join(TEMP_FOLDER, 'title.png'))

    comment_images = []

    for comment in comments_details:
        driver.get(comment['comment_url'])
        time.sleep(2)
        shadow_host = driver.find_element(By.CSS_SELECTOR, f'shreddit-comment[thingid="{comment["comment_id"]}"]')
        try:
            button = driver.execute_script('return arguments[0].shadowRoot', shadow_host).find_element(By.CSS_SELECTOR, 'button[aria-label="Toggle Comment Thread"]')
            button.click()
        except Exception as e:
            print("Error, continuing whatsoever:")
            print(str(e))
        screenshot_path = os.path.join(TEMP_FOLDER, f"{comment['comment_id']}.png")
        screenshot_element(driver, f'shreddit-comment[thingid="{comment["comment_id"]}"]', screenshot_path)
        comment_images.append(os.path.join(TEMP_FOLDER, f"{comment['comment_id']}.png"))

    driver.quit()

    title_duration = MP3(os.path.join(TEMP_FOLDER, 'postTitle.mp3')).info.length
    comment_durations = [MP3(os.path.join(TEMP_FOLDER, f"{comment['comment_id']}.mp3")).info.length for comment in comments_details]

    generate_random_clip(config['background_video_path'], os.path.join(TEMP_FOLDER, 'random_clip.mp4'), title_duration + sum(comment_durations))

    create_final_video(
        output_path=os.path.join(TEMP_FOLDER, 'output_video.mp4'),
        title_image='title.png',
        comment_images=comment_images,
        video_background=os.path.join(TEMP_FOLDER, 'random_clip.mp4'),
        title_duration=title_duration,
        comment_durations=comment_durations,
        comments_details=comments_details,
        radius=int(config['rounded_corners_radius'])
    )

    #audio_files = [os.path.join(TEMP_FOLDER, 'postTitle.mp3')] + [os.path.join(TEMP_FOLDER, f"{comment['comment_id']}.mp3") for comment in comments_details]
    #process_video_with_audio(os.path.join(TEMP_FOLDER, 'output_video.mp4'), audio_files, 'final_video.mp4')

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', config['scopes'])
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('yt_api.json', config['scopes'])
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    youtube = build('youtube', 'v3', credentials=creds)

    upload_video(
        youtube,
        video_file='final_video.mp4',
        title=str(config['video_title']).replace('[post_title]', f"{comments_details[0]['post_title']}"),
        description=config['video_description'],
        tags=config['video_tags'],
        category_id=config['video_category_id'],
        privacy_status=config['privacy_status']
    )
    
    time.sleep(1)

    shutil.rmtree(config['temp_path'])
    # os.remove('final_video.mp4')

main()