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
    requests.post(url, json=payload)

# Function to scrape BBRadar.io for new bug bounty programs
def scrape_bbradar():
    url = "https://bbradar.io/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch BBRadar")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    programs = []
    
    # Find all program entries
    for bounty in soup.find_all("div", class_="bounty-card"):
        title = bounty.find("h3").text.strip()
        platform = bounty.find("span", class_="bounty-platform").text.strip()
        reward_text = bounty.find("span", class_="bounty-reward").text.strip()
        scope = bounty.find("span", class_="bounty-scope").text.strip()
        link = bounty.find("a", class_="bounty-link")["href"]
        
        # Convert reward range to numbers
        reward = [int(s.replace("$", "").replace(",", "")) for s in reward_text.split("-") if s.replace("$", "").replace(",", "").isdigit()]
        max_reward = max(reward) if reward else 0

        # Filtering conditions
        if ("fintech" in title.lower() or "healthcare" in title.lower()) and \
           ("yeswehack" in platform.lower() or "bugcrowd" in platform.lower() or "intigriti" in platform.lower()) and \
           ("vdp" not in title.lower()) and \
           max_reward >= 1000 and \
           ("api" in scope.lower() or "web" in scope.lower()):
            
            programs.append({
                "title": title,
                "platform": platform,
                "reward": max_reward,
                "scope": scope,
                "link": link
            })
    
    return programs

# Load past results to avoid duplicate notifications
def load_previous_results():
    try:
        with open("past_results.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_results(results):
    with open("past_results.json", "w") as file:
        json.dump(results, file, indent=4)

# Main execution
if __name__ == "__main__":
    past_results = load_previous_results()
    new_programs = scrape_bbradar()

    if new_programs:
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
