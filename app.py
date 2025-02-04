import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import streamlit as st # type: ignore
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client (API key from environment variables)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    st.error("OPENROUTER_API_KEY environment variable not set.")
    st.stop()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# Streamlit app title and description
st.title("Website Summarizer")
st.write("Enter a URL to get a summary of the website's content.")

# User input for URL
url = st.text_input("Enter URL:", placeholder="e.g., https://techcrunch.com/")

# Website class (with error handling)
class Website:
    def __init__(self, url):
        self.url = url
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)  # Timeout added
            response.raise_for_status()  # Check for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching URL: {e}")
            st.stop()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()

# System prompt (same as before)
system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

# User prompt function (same as before)
def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

# Messages function (same as before)
def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

# Summarize function (same as before)
def summarize(url):
    website = Website(url)
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=messages_for(website)
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

# Display summary (using st.markdown for Markdown rendering)
def display_summary(url):
    summary = summarize(url)
    if summary:
        st.markdown(summary)  # Use st.markdown for Streamlit

# Button to trigger summarization
if st.button("Get Summary"):
    if url:
        with st.spinner("Generating summary..."):  # Add a spinner
            display_summary(url)
    else:
        st.warning("Please enter a URL.")