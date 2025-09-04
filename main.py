# Requirements:
# pip install telebot requests bs4

import telebot
import requests
from bs4 import BeautifulSoup

# ========== Konfigurasi ==========
BOT_TOKEN = ''

bot = telebot.TeleBot(BOT_TOKEN)

# ========== Fungsi Scraping CVE dari mitre.org ==========
def search_cve(product):
    url = f"https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={product}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        raise Exception("Gagal mengakses mitre.org")

    soup = BeautifulSoup(res.text, 'html.parser')
    results = []

    rows = soup.select("div#TableWithRules table tr")[1:11]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            cve_id = cols[0].text.strip()
            description = cols[1].text.strip()
            link = cols[0].find("a")
            href = f"https://cve.mitre.org{link['href']}" if link else "-"
            # Ambil tanggal rilis dari deskripsi (biasanya di akhir dengan format '... YYYY-MM-DD.')
            date = "-"
            if description and description[-1] == '.' and len(description) > 10:
                last_words = description.split()[-1]
                if len(last_words) == 10 and last_words[4] == '-' and last_words[7] == '-':
                    date = last_words
            results.append({
                "cve_id": cve_id,
                "description": description,
                "reference_link": href,
                "published_date": date
            })
    return results

# ========== Telegram Command Handler ==========
@bot.message_handler(commands=['cve_search'])
def search_cve_handler(message):
    try:
        query = message.text.split(" ", 1)[1] if ' ' in message.text else None
        if not query:
            bot.send_message(message.chat.id, "Gunakan format: /cve_search nama_produk")
            return

        bot.send_message(message.chat.id, f"🔍 Mencari CVE untuk '{query}'...")
        cve_list = search_cve(query)

        if not cve_list:
            bot.send_message(message.chat.id, "Tidak ditemukan CVE.")
            return

        response = '\n\n'.join([
            f"🔐 {c['cve_id']}\n📅 {c['published_date']}\n📎 {c['reference_link']}\n📝 {c['description'][:200]}..."
            for c in cve_list
        ])
        bot.send_message(message.chat.id, response)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# ========== Main ==========
if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(non_stop=True)
