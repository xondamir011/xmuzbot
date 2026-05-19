# 🤖 Uy Ishi Tekshiruvchi Telegram Bot

## 📁 Fayllar
```
homework_bot/
├── bot.py           # Asosiy bot fayli
├── database.py      # Ma'lumotlar bazasi (SQLite)
├── ai_checker.py    # AI tekshirish moduli
├── requirements.txt # Kerakli kutubxonalar
└── README.md        # Bu fayl
```

---

## ⚙️ O'rnatish

### 1. Python kutubxonalarini o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Bot tokenini olish
1. Telegramda [@BotFather](https://t.me/BotFather) ga o'ting
2. `/newbot` yozing
3. Bot nomini va username ni kiriting
4. Token nusxalang: `1234567890:ABCdef...`

### 3. Anthropic API kalitini olish
1. [console.anthropic.com](https://console.anthropic.com) ga kiring
2. API Keys bo'limiga o'ting
3. Yangi kalit yarating

### 4. `bot.py` faylida sozlang
```python
BOT_TOKEN = "1234567890:ABCdef..."       # BotFather bergan token
ANTHROPIC_API_KEY = "sk-ant-..."         # Anthropic API kalit
ADMIN_IDS = [123456789]                  # Sizning Telegram ID ingiz
```

> **Telegram ID ni qanday topish?**
> [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring

### 5. Botni ishga tushirish
```bash
python bot.py
```

---

## 🎮 Qanday ishlatish

### O'qituvchi (Admin) uchun:
| Buyruq | Vazifa |
|--------|--------|
| `/set_task Vazifa matni` | Yangi vazifa berish |
| `/set_prompt Yangi prompt` | AI baholash promptini o'zgartirish |
| `/results` | Barcha natijalarni ko'rish |
| `/clear_task` | Vazifani tozalash |
| `/add_admin 123456789` | Yangi admin qo'shish |

### O'quvchilar uchun:
| Buyruq | Vazifa |
|--------|--------|
| `/start` | Botni boshlash |
| `/task` | Joriy vazifani ko'rish |
| `/submit` | Uy ishini topshirish |
| `/rating` | Guruh reytingini ko'rish |
| `/myresults` | O'z natijalarini ko'rish |

---

## 🔄 Ish jarayoni

```
O'qituvchi → /set_task "Vazifa..."
    ↓
O'quvchi → /submit → Uy ishini yozadi
    ↓
Bot → AI ga yuboradi (Claude)
    ↓
AI → 0-100 ball + feedback qaytaradi
    ↓
Bot → O'quvchiga natija yuboradi
    ↓
Reyting yangilanadi
```

---

## 🎯 AI Promptini Sozlash

`/set_prompt` bilan o'z mezonlaringizni qo'shishingiz mumkin:

```
/set_prompt Sen matematika o'qituvchisissan. Yechimning to'g'riligiga 50 ball, 
ko'rsatish usuliga 30 ball, tartibliligiga 20 ball ber. JSON formatda qaytargin.
```

---

## 🌐 Server ga joylashtirish (ixtiyoriy)

**Railway.app** da bepul hosting:
```bash
# railway.toml fayli yarating
[build]
builder = "nixpacks"

[deploy]
startCommand = "python bot.py"
```

**Environment variables** (muhit o'zgaruvchilari) sifatida qo'ying:
- `BOT_TOKEN`
- `ANTHROPIC_API_KEY`

---

## ❓ Muammolar

**Bot javob bermayapti?**
- Token to'g'riligini tekshiring
- Bot guruhga admin sifatida qo'shilganini tekshiring

**AI tekshirmayapti?**
- Anthropic API kaliti to'g'riligini tekshiring
- API limitingiz tugaganini tekshiring

**"Admin emas" deyapti?**
- `ADMIN_IDS` listiga o'z ID ingizni qo'shing