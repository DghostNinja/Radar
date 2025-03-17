import os
import requests
import json
from bs4 import BeautifulSoup

# Telegram Bot Credentials (From GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Function to send Telegram notification
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Notification sent successfully.")
    else:
        print(f"❌ Failed to send Telegram message. Status: {response.status_code}, Response: {response.text}")

# Function to scrape BBRadar.io for new bug bounty programs
def scrape_bbradar():
    url = "https://bbradar.io/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch BBRadar (Status Code: {response.status_code})")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")

    # Debugging: Print HTML structure if parsing fails
    with open("bbradar_debug.html", "w", encoding="utf-8") as debug_file:
        debug_file.write(soup.prettify())

    programs = []
    
    # Find all program entries
    for bounty in soup.find_all("div", class_="bounty-card"):  # Adjust class name if needed
        try:
            title = bounty.find("h3").text.strip() if bounty.find("h3") else "Unknown"
            platform = bounty.find("span", class_="bounty-platform").text.strip() if bounty.find("span", class_="bounty-platform") else "Unknown"
            reward_text = bounty.find("span", class_="bounty-reward").text.strip() if bounty.find("span", class_="bounty-reward") else "$0"
            scope = bounty.find("span", class_="bounty-scope").text.strip() if bounty.find("span", class_="bounty-scope") else "Unknown"
            link = bounty.find("a", class_="bounty-link")["href"] if bounty.find("a", class_="bounty-link") else "#"

            # Convert reward range to max number
            reward = [int(s.replace("$", "").replace(",", "")) for s in reward_text.split("-") if s.replace("$", "").replace(",", "").isdigit()]
            max_reward = max(reward) if reward else 0

            # Filtering conditions
            if any(keyword in title.lower() for keyword in ["fintech", "healthcare"]) and \
               any(platform.lower() in bounty_platform for bounty_platform in ["yeswehack", "bugcrowd", "intigriti"]) and \
               "vdp" not in title.lower() and \
               max_reward >= 1000 and \
               any(scope_keyword in scope.lower() for scope_keyword in ["api", "web"]):
                
                programs.append({
                    "title": title,
                    "platform": platform,
                    "reward": max_reward,
                    "scope": scope,
                    "link": link
                })
        except Exception as e:
            print(f"⚠️ Error parsing bounty: {e}")

    return programs

# Load past results to avoid duplicate notifications
def load_previous_results():
    try:
        with open("past_results.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_results(results):
    with open("past_results.json", "w") as file:
        json.dump(results, file, indent=4)

# Main execution
if __name__ == "__main__":
    past_results = load_previous_results()
    new_programs = scrape_bbradar()

    if new_programs:
        print(f"✅ Found {len(new_programs)} matching bounty programs!")
        for program in new_programs:
            if program["link"] not in past_results:
                message = f"🚀 *New Paid Bounty Program Found!*\n\n" \
                          f"*Title:* {program['title']}\n" \
                          f"*Platform:* {program['platform']}\n" \
                          f"*Reward:* ${program['reward']} for critical\n" \
                          f"*Scope:* {program['scope']}\n" \
                          f"*Link:* [View Program]({program['link']})"
                
                send_telegram_message(message)
                past_results.append(program["link"])
        
        save_results(past_results)
    else:
        print("ℹ️ No new matching bounty programs found.")
