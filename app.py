import base64
import hashlib
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import folium
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

from models.risk_engine import calculate_risk



# ============================================================
# MULTI-LANGUAGE UI
# ============================================================

LANGUAGE_OPTIONS = {
    "English": "en",
    "ಕನ್ನಡ": "kn",
    "हिन्दी": "hi",
    "தமிழ்": "ta",
    "অসমীয়া": "as",          # Assam
    "বাংলা": "bn",            # Tripura / wider NE
    "মৈতৈলোন্ (Manipuri)": "mni",  # Manipur
    "Mizo": "lus",             # Mizoram
    "Khasi": "kha",            # Meghalaya
    "Garo": "grt",             # Meghalaya
    "Bodo": "brx",             # Assam
    "नेपाली": "ne",            # Sikkim / Darjeeling region
    "➕ Add Language": "add",
}

TRANSLATIONS = {
    "Dashboard": {
        "kn":"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "hi":"डैशबोर्ड", "ta":"டாஷ்போர்டு",
        "as":"ড্যাশবোর্ড", "bn":"ড্যাশবোর্ড", "mni":"ড্যাশবোর্ড",
        "lus":"Dashboard", "kha":"Dashboard", "grt":"Dashboard",
        "brx":"ड्यासबर्ड", "ne":"ड्यासबोर्ड"
    },
    "Risk Map": {
        "kn":"ಅಪಾಯ ನಕ್ಷೆ", "hi":"जोखिम मानचित्र", "ta":"ஆபத்து வரைபடம்",
        "as":"ঝুঁকি মানচিত্ৰ", "bn":"ঝুঁকি মানচিত্র", "mni":"ꯔꯤꯁ꯭ꯛ ꯃꯥꯞ",
        "lus":"Risk Map", "kha":"Risk Map", "grt":"Risk Map", "brx":"जोखिम नक्सा", "ne":"जोखिम नक्सा"
    },
    "Alerts": {
        "kn":"ಎಚ್ಚರಿಕೆಗಳು", "hi":"चेतावनियाँ", "ta":"எச்சரிக்கைகள்",
        "as":"সতৰ্কবাণী", "bn":"সতর্কতা", "mni":"ꯍꯦꯜꯄꯣꯟ", "lus":"Alerts",
        "kha":"Alerts", "grt":"Alerts", "brx":"सावधानि", "ne":"सतर्कताहरू"
    },
    "Predicted Landslide Risk": {
        "kn":"ಮುನ್ಸೂಚಿತ ಭೂಕುಸಿತ ಅಪಾಯ", "hi":"पूर्वानुमानित भूस्खलन जोखिम", "ta":"கணிக்கப்பட்ட நிலச்சரிவு ஆபத்து",
        "as":"পূৰ্বানুমানিত ভূমিস্খলন ঝুঁকি", "bn":"পূর্বাভাসিত ভূমিধস ঝুঁকি", "mni":"ꯄ꯭ꯔꯤꯗꯤꯛꯇꯦꯗ ꯂꯥꯟꯁ꯭ꯂꯥꯏꯗ ꯔꯤꯁ꯭ꯛ",
        "lus":"Predicted Landslide Risk", "kha":"Predicted Landslide Risk", "grt":"Predicted Landslide Risk", "brx":"गोसोखानाय भुस्खलन जोखिम", "ne":"पूर्वानुमानित पहिरो जोखिम"
    },
    "Early Alert Systems": {
        "kn":"ಮುಂಚಿತ ಎಚ್ಚರಿಕೆ ವ್ಯವಸ್ಥೆಗಳು", "hi":"प्रारंभिक चेतावनी प्रणालियाँ", "ta":"முன்கூட்டிய எச்சரிக்கை அமைப்புகள்",
        "as":"আগতীয়া সতৰ্কতা ব্যৱস্থা", "bn":"প্রাথমিক সতর্কতা ব্যবস্থা", "mni":"ꯑꯔꯤ ꯑꯂꯥꯔꯠ ꯁꯤꯁꯇꯦꯝ",
        "lus":"Early Alert Systems", "kha":"Early Alert Systems", "grt":"Early Alert Systems",
        "brx":"आगोनि सावधानि बिदाय", "ne":"प्रारम्भिक चेतावनी प्रणाली"
    },
    "Sensors": {
        "kn":"ಸೆನ್ಸರ್‌ಗಳು", "hi":"सेंसर", "ta":"சென்சார்கள்",
        "as":"চেন্সৰসমূহ", "bn":"সেন্সর", "mni":"ꯁꯦꯟꯁꯔ", "lus":"Sensors",
        "kha":"Sensors", "grt":"Sensors", "brx":"सेन्सर", "ne":"सेन्सरहरू"
    },
    "Analytics": {
        "kn":"ವಿಶ್ಲೇಷಣೆ", "hi":"विश्लेषण", "ta":"பகுப்பாய்வு",
        "as":"বিশ্লেষণ", "bn":"বিশ্লেষণ", "mni":"ꯑꯦꯅꯥꯂꯤꯇꯤꯛꯁ",
        "lus":"Analytics", "kha":"Analytics", "grt":"Analytics", "brx":"विश्लेषण", "ne":"विश्लेषण"
    },
    "Incident Reporting": {
        "kn":"ಘಟನೆ ವರದಿ", "hi":"घटना रिपोर्टिंग", "ta":"சம்பவ அறிக்கை",
        "as":"ঘটনা প্ৰতিবেদন", "bn":"ঘটনা রিপোর্ট", "mni":"ꯏꯟꯁꯤꯗꯦꯟꯇ ꯔꯤꯄꯣꯔꯇ",
        "lus":"Incident Reporting", "kha":"Incident Reporting", "grt":"Incident Reporting",
        "brx":"घटना रिपोर्ट", "ne":"घटना प्रतिवेदन"
    },
    "Reports": {
        "kn":"ವರದಿಗಳು", "hi":"रिपोर्ट", "ta":"அறிக்கைகள்",
        "as":"প্ৰতিবেদনসমূহ", "bn":"রিপোর্ট", "mni":"ꯔꯤꯄꯣꯔꯠꯁ",
        "lus":"Reports", "kha":"Reports", "grt":"Reports", "brx":"रिपोर्ट", "ne":"प्रतिवेदनहरू"
    },
    "Settings": {
        "kn":"ಸೆಟ್ಟಿಂಗ್‌ಗಳು", "hi":"सेटिंग्स", "ta":"அமைப்புகள்",
        "as":"ছেটিংছ", "bn":"সেটিংস", "mni":"ꯁꯦꯇꯤꯡꯁ",
        "lus":"Settings", "kha":"Settings", "grt":"Settings", "brx":"सेटिङ", "ne":"सेटिङहरू"
    },
    "Navigation": {
        "kn":"ನ್ಯಾವಿಗೇಶನ್", "hi":"नेविगेशन", "ta":"வழிசெலுத்தல்",
        "as":"নেভিগেশ্যন", "bn":"নেভিগেশন", "mni":"ꯅꯦꯚꯤꯒꯦꯁꯟ",
        "lus":"Navigation", "kha":"Navigation", "grt":"Navigation", "brx":"नेभिगेसन", "ne":"नेभिगेसन"
    },
    "Active Module": {
        "kn":"ಸಕ್ರಿಯ ಮಾಡ್ಯೂಲ್", "hi":"सक्रिय मॉड्यूल", "ta":"செயலில் உள்ள தொகுதி",
        "as":"সক্ৰিয় মডিউল", "bn":"সক্রিয় মডিউল", "mni":"ꯑꯦꯛꯇꯤꯕ ꯃꯣꯗ꯭ꯌꯨꯜ",
        "lus":"Active Module", "kha":"Active Module", "grt":"Active Module", "brx":"सक्रिय मोड्युल", "ne":"सक्रिय मोड्युल"
    },
    "Purpose": {
        "kn":"ಉದ್ದೇಶ", "hi":"उद्देश्य", "ta":"நோக்கம்",
        "as":"উদ্দেশ্য", "bn":"উদ্দেশ্য", "mni":"ꯄꯔꯣꯃꯣꯁ",
        "lus":"Purpose", "kha":"Purpose", "grt":"Purpose", "brx":"उद्देश्य", "ne":"उद्देश्य"
    },
    "Information shown": {
        "kn":"ತೋರಿಸಲಾದ ಮಾಹಿತಿ", "hi":"दिखाई गई जानकारी", "ta":"காட்டப்படும் தகவல்",
        "as":"দেখুওৱা তথ্য", "bn":"দেখানো তথ্য", "mni":"ꯎꯇꯂꯤꯕ ꯏꯟꯐꯣꯔꯃꯦꯁꯟ",
        "lus":"Information shown", "kha":"Information shown", "grt":"Information shown",
        "brx":"दिन्थिनाय फोरमायथिहोग्रा", "ne":"देखाइएको जानकारी"
    },
    "Live Situation Summary": {
        "kn":"ಲೈವ್ ಪರಿಸ್ಥಿತಿ ಸಾರಾಂಶ", "hi":"लाइव स्थिति सारांश", "ta":"நேரடி நிலை சுருக்கம்",
        "as":"লাইভ পৰিস্থিতিৰ সাৰাংশ", "bn":"লাইভ পরিস্থিতির সারাংশ", "mni":"ꯂꯥꯏꯕ ꯁꯤꯊꯤꯜ ꯁꯥꯔꯥꯡꯁ",
        "lus":"Live Situation Summary", "kha":"Live Situation Summary", "grt":"Live Situation Summary",
        "brx":"लाइभ सिथिं सारांस", "ne":"प्रत्यक्ष अवस्थाको सारांश"
    },
    "Last refreshed": {
        "kn":"ಕೊನೆಯ ನವೀಕರಣ", "hi":"अंतिम अपडेट", "ta":"கடைசியாக புதுப்பிக்கப்பட்டது",
        "as":"শেষবাৰৰ বাবে সতেজ কৰা", "bn":"সর্বশেষ আপডেট", "mni":"ꯑꯔꯤꯕ ꯍꯟꯖꯤꯟꯕ",
        "lus":"Last refreshed", "kha":"Last refreshed", "grt":"Last refreshed", "brx":"जोबोद अपडेट", "ne":"अन्तिम अद्यावधिक"
    },
    "System Settings": {
        "kn":"ಸಿಸ್ಟಮ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳು", "hi":"सिस्टम सेटिंग्स", "ta":"கணினி அமைப்புகள்",
        "as":"চিষ্টেম ছেটিংছ", "bn":"সিস্টেম সেটিংস", "mni":"ꯁꯤꯁꯇꯦꯝ ꯁꯦꯇꯤꯡꯁ",
        "lus":"System Settings", "kha":"System Settings", "grt":"System Settings", "brx":"सिस्टम सेटिङ", "ne":"सिस्टम सेटिङहरू"
    },
    "Notification Control": {
        "kn":"ಅಧಿಸೂಚನೆ ನಿಯಂತ್ರಣ", "hi":"अधिसूचना नियंत्रण", "ta":"அறிவிப்பு கட்டுப்பாடு",
        "as":"জাননী নিয়ন্ত্ৰণ", "bn":"বিজ্ঞপ্তি নিয়ন্ত্রণ", "mni":"ꯅꯣꯇꯤꯐꯤꯀꯦꯁꯟ ꯀꯟꯇ꯭ꯔꯣꯜ",
        "lus":"Notification Control", "kha":"Notification Control", "grt":"Notification Control", "brx":"फोरमायथिहोग्रा कन्ट्रोल", "ne":"सूचना नियन्त्रण"
    },
    "AI-Assisted Priority Weights": {
        "kn":"AI ಸಹಾಯದ ಆದ್ಯತಾ ತೂಕಗಳು", "hi":"AI-सहायता प्राप्त प्राथमिकता भार", "ta":"AI உதவியுடன் முன்னுரிமை எடைகள்",
        "as":"AI-সহায়ক অগ্ৰাধিকাৰ ওজন", "bn":"AI-সহায়ক অগ্রাধিকার ওজন", "mni":"AI-ꯑꯁꯤꯗꯥ ꯄ꯭ꯔꯥꯏꯣꯔꯤꯇꯤ ꯋꯦꯏꯇꯁ",
        "lus":"AI-Assisted Priority Weights", "kha":"AI-Assisted Priority Weights", "grt":"AI-Assisted Priority Weights",
        "brx":"AI-सहायता प्राथमिकता भार", "ne":"AI-सहायता प्राथमिकता भार"
    },
    "Language": {
        "kn":"ಭಾಷೆ", "hi":"भाषा", "ta":"மொழி", "as":"ভাষা", "bn":"ভাষা", "mni":"ꯂꯣꯟ",
        "lus":"Language", "kha":"Language", "grt":"Language", "brx":"राव", "ne":"भाषा"
    },
    "Select interface language": {
        "kn":"ಇಂಟರ್ಫೇಸ್ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ", "hi":"इंटरफेस भाषा चुनें", "ta":"இடைமுக மொழியைத் தேர்ந்தெடுக்கவும்",
        "as":"ইন্টাৰফেচৰ ভাষা বাছনি কৰক", "bn":"ইন্টারফেসের ভাষা নির্বাচন করুন", "mni":"ꯏꯟꯇꯔꯐꯦꯁ ꯂꯣꯟ ꯈꯟꯅꯕ",
        "lus":"Select interface language", "kha":"Select interface language", "grt":"Select interface language",
        "brx":"इन्टारफेस राव सायखां", "ne":"इन्टरफेस भाषा छान्नुहोस्"
    },
    "English": {
        "kn":"ಇಂಗ್ಲಿಷ್", "hi":"अंग्रेज़ी", "ta":"ஆங்கிலம்", "as":"ইংৰাজী", "bn":"ইংরেজি", "mni":"ꯏꯪꯂꯤꯁ",
        "lus":"English", "kha":"English", "grt":"English", "brx":"इंग्लिस", "ne":"अंग्रेजी"
    },
    "SMS Alerts": {"kn":"SMS ಎಚ್ಚರಿಕೆಗಳು", "hi":"SMS चेतावनियाँ", "ta":"SMS எச்சரிக்கைகள்", "as":"SMS সতৰ্কবাণী", "bn":"SMS সতর্কতা", "mni":"SMS ꯍꯦꯜꯄꯣꯟ", "brx":"SMS सावधानि", "ne":"SMS सतर्कताहरू"},
    "Mobile Notifications": {"kn":"ಮೊಬೈಲ್ ಅಧಿಸೂಚನೆಗಳು", "hi":"मोबाइल सूचनाएँ", "ta":"மொபைல் அறிவிப்புகள்", "as":"ম'বাইল জাননী", "bn":"মোবাইল বিজ্ঞপ্তি", "mni":"ꯃꯣꯕꯥꯏꯜ ꯅꯣꯇꯤꯐꯤꯀꯦꯁꯟ", "brx":"मोबाइल फोरमायथिहोग्रा", "ne":"मोबाइल सूचनाहरू"},
    "Dashboard Alerts": {"kn":"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಎಚ್ಚರಿಕೆಗಳು", "hi":"डैशबोर्ड चेतावनियाँ", "ta":"டாஷ்போர்டு எச்சரிக்கைகள்", "as":"ড্যাশবোর্ড সতৰ্কবাণী", "bn":"ড্যাশবোর্ড সতর্কতা", "mni":"ꯗꯥꯁꯕꯣꯔꯗ ꯍꯦꯜꯄꯣꯟ", "brx":"ड्यासबर्ड सावधानि", "ne":"ड्यासबोर्ड सतर्कताहरू"},
    "Enable SMS channel": {"kn":"SMS ಚಾನೆಲ್ ಸಕ್ರಿಯಗೊಳಿಸಿ", "hi":"SMS चैनल सक्षम करें", "ta":"SMS சேனலை இயக்கவும்", "as":"SMS চেনেল সক্ৰিয় কৰক", "bn":"SMS চ্যানেল সক্রিয় করুন", "mni":"SMS ꯆꯦꯅꯦꯜ ꯁꯛꯇꯥꯛꯎ", "brx":"SMS चेनेल जागाय", "ne":"SMS च्यानल सक्षम गर्नुहोस्"},
    "Enable mobile channel": {"kn":"ಮೊಬೈಲ್ ಚಾನೆಲ್ ಸಕ್ರಿಯಗೊಳಿಸಿ", "hi":"मोबाइल चैनल सक्षम करें", "ta":"மொபைல் சேனலை இயக்கவும்", "as":"ম'বাইল চেনেল সক্ৰিয় কৰক", "bn":"মোবাইল চ্যানেল সক্রিয় করুন", "mni":"ꯃꯣꯕꯥꯏꯜ ꯆꯦꯅꯦꯜ ꯁꯛꯇꯥꯛꯎ", "brx":"मोबाइल चेनेल जागाय", "ne":"मोबाइल च्यानल सक्षम गर्नुहोस्"},
    "Enable dashboard channel": {"kn":"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಚಾನೆಲ್ ಸಕ್ರಿಯಗೊಳಿಸಿ", "hi":"डैशबोर्ड चैनल सक्षम करें", "ta":"டாஷ்போர்டு சேனலை இயக்கவும்", "as":"ড্যাশবোর্ড চেনেল সক্ৰিয় কৰক", "bn":"ড্যাশবোর্ড চ্যানেল সক্রিয় করুন", "mni":"ꯗꯥꯁꯕꯣꯔꯗ ꯆꯦꯅꯦꯜ ꯁꯛꯇꯥꯛꯎ", "brx":"ड्यासबर्ड चेनेल जागाय", "ne":"ड्यासबोर्ड च्यानल सक्षम गर्नुहोस्"},
    "AI Landslide Risk Weight": {"kn":"AI ಭೂಕುಸಿತ ಅಪಾಯ ತೂಕ", "hi":"AI भूस्खलन जोखिम भार", "ta":"AI நிலச்சரிவு ஆபத்து எடை", "as":"AI ভূমিস্খলন ঝুঁকি ওজন", "bn":"AI ভূমিধস ঝুঁকি ওজন", "mni":"AI ꯂꯥꯟꯁ꯭ꯂꯥꯏꯗ ꯔꯤꯁ꯭ꯛ ꯋꯦꯏꯇ", "brx":"AI भुस्खलन जोखिम भार", "ne":"AI पहिरो जोखिम भार"},
    "Current configuration": {"kn":"ಪ್ರಸ್ತುತ ಸಂರಚನೆ", "hi":"वर्तमान कॉन्फ़िगरेशन", "ta":"தற்போதைய அமைப்பு", "as":"বৰ্তমান বিন্যাস", "bn":"বর্তমান কনফিগারেশন", "mni":"ꯍꯧꯖꯤꯛꯇꯤ ꯀꯟꯐꯤꯒꯨꯔꯦꯁꯟ", "brx":"दानाय कन्फिगारेशन", "ne":"हालको कन्फिगरेसन"},
    "Reset settings to default": {"kn":"ಡೀಫಾಲ್ಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಿಗೆ ಮರುಹೊಂದಿಸಿ", "hi":"डिफ़ॉल्ट सेटिंग्स पर रीसेट करें", "ta":"இயல்புநிலை அமைப்புகளுக்கு மீட்டமைக்கவும்", "as":"ডিফল্ট ছেটিংছলৈ পুনৰ সংহতি কৰক", "bn":"ডিফল্ট সেটিংসে রিসেট করুন", "mni":"ꯗꯤꯐꯣꯜꯇ ꯁꯦꯇꯤꯡꯁꯗꯥ ꯐꯝꯁꯤꯟꯕ", "brx":"डिफल्ट सेटिङआव थादे", "ne":"डिफल्ट सेटिङमा रिसेट गर्नुहोस्"},
    "Current mode": {"kn":"ಪ್ರಸ್ತುತ ಮೋಡ್", "hi":"वर्तमान मोड", "ta":"தற்போதைய பயன்முறை", "as":"বৰ্তমান মোড", "bn":"বর্তমান মোড", "mni":"ꯍꯧꯖꯤꯛꯀꯤ ꯃꯣꯗ", "brx":"दानाय मोड", "ne":"हालको मोड"},
    "SIH Demonstration Prototype": {"kn":"SIH ಪ್ರದರ್ಶನ ಪ್ರೋಟೋಟೈಪ್", "hi":"SIH प्रदर्शन प्रोटोटाइप", "ta":"SIH செயல்விளக்க முன்மாதிரி", "as":"SIH প্ৰদৰ্শনী প্ৰ'টোটাইপ", "bn":"SIH প্রদর্শনী প্রোটোটাইপ", "mni":"SIH ꯁꯦꯜꯐꯃꯦꯟꯇ ꯄ꯭ꯔꯣꯇꯣꯇꯥꯏꯞ", "brx":"SIH दिन्थिनाय प्रोटोटाइप", "ne":"SIH प्रदर्शन प्रोटोटाइप"},
    "Alert channels": {"kn":"ಎಚ್ಚರಿಕೆ ಚಾನೆಲ್‌ಗಳು", "hi":"अलर्ट चैनल", "ta":"எச்சரிக்கை சேனல்கள்", "as":"সতৰ্কবাণী চেনেল", "bn":"সতর্কতা চ্যানেল", "mni":"ꯍꯦꯜꯄꯣꯟ ꯆꯦꯅꯦꯜ", "brx":"सावधानि चेनेल", "ne":"सतर्कता च्यानलहरू"},
    "AI weight": {"kn":"AI ತೂಕ", "hi":"AI भार", "ta":"AI எடை", "as":"AI ওজন", "bn":"AI ওজন", "mni":"AI ꯋꯦꯏꯇ", "brx":"AI भार", "ne":"AI भार"},
    "Villages": {"kn":"ಗ್ರಾಮಗಳು", "hi":"गाँव", "ta":"கிராமங்கள்", "as":"গাঁওসমূহ", "bn":"গ্রাম", "mni":"ꯈꯣꯡ", "brx":"हाबा", "ne":"गाउँहरू"},
    "AI engine": {"kn":"AI ಎಂಜಿನ್", "hi":"AI इंजन", "ta":"AI இயந்திரம்", "as":"AI ইঞ্জিন", "bn":"AI ইঞ্জিন", "mni":"AI ꯏꯟꯖꯤꯟ", "brx":"AI इन्जिन", "ne":"AI इन्जिन"},
    "Loaded": {"kn":"ಲೋಡ್ ಆಗಿದೆ", "hi":"लोडेड", "ta":"ஏற்றப்பட்டது", "as":"লোড কৰা হৈছে", "bn":"লোড হয়েছে", "mni":"ꯂꯣꯗ ꯇꯧꯔꯦ", "brx":"लोड जाबाय", "ne":"लोड भयो"},
    "Fallback": {"kn":"ಫಾಲ್‌ಬ್ಯಾಕ್", "hi":"फॉलबैक", "ta":"மாற்று முறை", "as":"বিকল্প", "bn":"বিকল্প", "mni":"ꯐꯥꯜꯕꯦꯛ", "brx":"फलबेक", "ne":"फलब्याक"},
}


if "language" not in st.session_state:
    st.session_state.language = "en"


def t(text):
    """Translate a UI phrase while keeping English as the default language."""
    if not isinstance(text, str):
        return text
    return TRANSLATIONS.get(text, {}).get(st.session_state.language, text)


# ---------------------------------------------------------------------------
# Whole-interface translation helper
# ---------------------------------------------------------------------------
# Streamlit widgets are created throughout the application.  Instead of
# requiring every existing call to be rewritten, the display wrappers below
# translate all exact phrases that exist in TRANSLATIONS before they are sent
# to Streamlit.  This also covers text inside longer markdown/HTML blocks.
# ---------------------------------------------------------------------------
def translate_ui_text(value):
    """Translate visible UI text without touching CSS classes, HTML attributes or code."""
    if not isinstance(value, str) or st.session_state.language == "en":
        return value

    replacements = []
    for source, translations in TRANSLATIONS.items():
        target = translations.get(st.session_state.language)
        if target and target != source:
            replacements.append((source, target))
    replacements.sort(key=lambda item: len(item[0]), reverse=True)

    def replace_text(text):
        result = text
        for source, target in replacements:
            result = result.replace(source, target)
        return result

    # Never translate CSS/JS blocks. For HTML, translate only visible text
    # between tags so selectors, classes and attributes remain valid.
    protected = []
    import re

    def protect(match):
        protected.append(match.group(0))
        return f"\x00PROTECTED_{len(protected)-1}\x00"

    work = re.sub(r"<style\b[^>]*>.*?</style\s*>", protect, value, flags=re.I | re.S)
    work = re.sub(r"<script\b[^>]*>.*?</script\s*>", protect, work, flags=re.I | re.S)

    parts = re.split(r"(<[^>]+>)", work)
    for i, part in enumerate(parts):
        if part.startswith("<") and part.endswith(">"):
            continue
        parts[i] = replace_text(part)
    result = "".join(parts)

    for i, original in enumerate(protected):
        result = result.replace(f"\x00PROTECTED_{i}\x00", original)
    return result


# Keep the original Streamlit methods so the wrappers can be installed once.
_ST_MARKDOWN = st.markdown
_ST_CAPTION = st.caption
_ST_TITLE = st.title
_ST_HEADER = st.header
_ST_SUBHEADER = st.subheader
_ST_WRITE = st.write
_ST_INFO = st.info
_ST_WARNING = st.warning
_ST_SUCCESS = st.success
_ST_ERROR = st.error

def _translated_markdown(body, *args, **kwargs):
    return _ST_MARKDOWN(translate_ui_text(body), *args, **kwargs)

def _translated_caption(body, *args, **kwargs):
    return _ST_CAPTION(translate_ui_text(body), *args, **kwargs)

def _translated_title(body, *args, **kwargs):
    return _ST_TITLE(translate_ui_text(body), *args, **kwargs)

def _translated_header(body, *args, **kwargs):
    return _ST_HEADER(translate_ui_text(body), *args, **kwargs)

def _translated_subheader(body, *args, **kwargs):
    return _ST_SUBHEADER(translate_ui_text(body), *args, **kwargs)

def _translated_write(body, *args, **kwargs):
    if isinstance(body, str):
        body = translate_ui_text(body)
    elif isinstance(body, (list, tuple)):
        body = type(body)(translate_ui_text(x) if isinstance(x, str) else x for x in body)
    return _ST_WRITE(body, *args, **kwargs)

def _translated_info(body, *args, **kwargs):
    return _ST_INFO(translate_ui_text(body), *args, **kwargs)

def _translated_warning(body, *args, **kwargs):
    return _ST_WARNING(translate_ui_text(body), *args, **kwargs)

def _translated_success(body, *args, **kwargs):
    return _ST_SUCCESS(translate_ui_text(body), *args, **kwargs)

def _translated_error(body, *args, **kwargs):
    return _ST_ERROR(translate_ui_text(body), *args, **kwargs)

st.markdown = _translated_markdown
st.caption = _translated_caption
st.title = _translated_title
st.header = _translated_header
st.subheader = _translated_subheader
st.write = _translated_write
st.info = _translated_info
st.warning = _translated_warning
st.success = _translated_success
st.error = _translated_error


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

IMAGE_PATH = BASE_DIR / "assets" / "background.jpg"
MODEL_PATH = BASE_DIR / "models" / "landslide_model.pkl"
DB_PATH = BASE_DIR / "data" / "incidents.db"

RISK_DATA_PATH = BASE_DIR / "data" / "risk_locations.csv"
ROAD_DATA_PATH = BASE_DIR / "data" / "road_risk.csv"
INFRA_DATA_PATH = BASE_DIR / "data" / "infrastructure_risk.csv"
VILLAGE_DATA_PATH = BASE_DIR / "data" / "village_risk.csv"


st.set_page_config(
    page_title="NER AI Landslide Early Warning System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# UI / BACKGROUND
# ============================================================

def set_background(image_path: Path):
    """Apply the landslide image as a top hero background and dark glass UI."""
    encoded = ""
    if image_path.exists():
        try:
            encoded = base64.b64encode(image_path.read_bytes()).decode()
        except Exception:
            encoded = ""

    # Use the local project image when available. Otherwise use a remote
    # mountain/landslide-style image as a fallback so the Dashboard still
    # has a visual hero background.
    bg = (
        f'url("data:image/jpeg;base64,{encoded}")'
        if encoded
        else 'url("https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=2200&q=85")'
    )

    st.markdown(
        f"""
        <style>
        :root {{
            --bg: #07111d;
            --panel: rgba(7, 22, 39, 0.86);
            --panel2: rgba(11, 31, 52, 0.72);
            --border: rgba(120, 180, 230, 0.22);
            --text: #f5f7fb;
            --muted: #9fb1c4;
        }}

        .stApp {{
            background: #06101c;
            color: var(--text);
        }}

        /* Dashboard hero image: visible behind the top of the page.
           The image is separated from the main app background so it does
           not get hidden by Streamlit's page container. */
        .dashboard-image-bg {{
            position: fixed;
            z-index: 0;
            top: 0;
            left: 0;
            right: 0;
            height: 650px;
            pointer-events: none;
            background-image:
                linear-gradient(180deg,
                    rgba(3, 12, 22, 0.08) 0%,
                    rgba(3, 12, 22, 0.22) 28%,
                    rgba(3, 12, 22, 0.55) 62%,
                    rgba(6, 16, 28, 0.98) 100%),
                {bg};
            background-size: cover;
            background-position: center 25%;
            background-repeat: no-repeat;
            border-bottom: 1px solid rgba(74, 195, 255, 0.24);
            box-shadow: inset 0 -100px 110px rgba(3, 12, 22, 0.55);
        }}

        .dashboard-image-bg::after {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 18% 22%, rgba(0, 212, 255, 0.16), transparent 30%),
                radial-gradient(circle at 82% 20%, rgba(99, 102, 241, 0.14), transparent 32%);
        }}

        /* ==========================================================
           INDEPENDENT MAIN-CONTENT SCROLL
           Keep the browser viewport fixed and make only the Streamlit
           main content area scroll. The sidebar has its own scrollbar.
           ========================================================== */
        [data-testid="stAppViewContainer"] {{
            position: relative;
            z-index: 1;
            height: 100vh !important;
            max-height: 100vh !important;
            overflow: hidden !important;
        }}

        [data-testid="stAppViewContainer"] > .main {{
            height: 100vh !important;
            max-height: 100vh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain;
            scrollbar-width: thin;
        }}

        [data-testid="stAppViewContainer"] > .main > div {{
            min-height: 100% !important;
        }}

        .block-container {{
            position: relative;
            z-index: 2;
        }}

        [data-testid="stHeader"] {{ background: transparent; }}
        .block-container {{
            max-width: 1500px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(3,14,27,.98), rgba(2,10,20,.98));
            border-right: 1px solid rgba(120,180,230,.16);
            height: 100vh !important;
            max-height: 100vh !important;
            overflow: hidden !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            height: 100vh !important;
            max-height: 100vh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain;
            scrollbar-width: thin;
        }}

        section[data-testid="stSidebar"] * {{ color: #eaf2fa; }}
        section[data-testid="stSidebar"] .stRadio label {{
            padding: 8px 10px;
            border-radius: 10px;
        }}

        h1, h2, h3 {{ letter-spacing: -.02em; }}

        .glass {{
            background: linear-gradient(135deg, rgba(11,31,52,.86), rgba(5,18,32,.74));
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 12px 35px rgba(0,0,0,.22);
            padding: 16px;
        }}

        .risk-card {{
            border-radius: 15px;
            padding: 15px 17px;
            min-height: 90px;
            border: 1px solid rgba(255,255,255,.12);
            background: rgba(8,24,41,.86);
            box-shadow: 0 10px 28px rgba(0,0,0,.18);
        }}
        .risk-card .label {{ color: #b9c9d9; font-size: .88rem; }}
        .risk-card .value {{ font-size: 1.9rem; font-weight: 750; margin-top: 4px; }}
        .red {{ border-color: rgba(255,55,80,.55); }}
        .orange {{ border-color: rgba(255,153,40,.50); }}
        .yellow {{ border-color: rgba(255,207,54,.48); }}
        .green {{ border-color: rgba(43,211,126,.48); }}
        .cyan {{ border-color: rgba(55,199,255,.48); }}
        .purple {{ border-color: rgba(170,112,255,.48); }}

        .section-title {{ font-size: 1.22rem; font-weight: 750; margin: 8px 0 12px; }}
        .small-muted {{ color: var(--muted); font-size: .83rem; }}

        .map-controls-panel {{
            margin-top: 14px;
            margin-bottom: 8px;
            padding: 14px 18px 8px;
            background: linear-gradient(135deg, rgba(10,42,48,.88), rgba(5,24,37,.88));
            border: 1px solid rgba(34,197,94,.30);
        }}
        .map-controls-panel .section-title {{ margin-bottom: 2px; }}
        .map-controls-subtitle {{
            color: #a9bdc9;
            font-size: .88rem;
            margin-bottom: 4px;
        }}
        .map-control-status {{
            margin-top: 7px;
            padding: 8px 11px;
            border-radius: 10px;
            background: rgba(34,197,94,.10);
            border: 1px solid rgba(34,197,94,.25);
            color: #bcefd1;
            font-size: .78rem;
            font-weight: 700;
            text-align: center;
        }}
        .map-control-status span {{
            color: #39e68a;
            text-shadow: 0 0 9px rgba(57,230,138,.75);
        }}
        .map-help-card {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin: 4px 0 14px;
            padding: 11px 14px;
            border-radius: 12px;
            background: linear-gradient(90deg, rgba(34,197,94,.08), rgba(34,211,238,.06));
            border: 1px solid rgba(96,165,250,.20);
            color: #b8c9d8;
            font-size: .82rem;
            line-height: 1.45;
        }}
        .map-help-card b {{ color: #eaf5ff; }}
        .map-help-icon {{ font-size: 1.15rem; line-height: 1.2; }}


        .ai-panel {{
            border: 1px solid rgba(69,170,255,.40);
            border-radius: 18px;
            background: radial-gradient(circle at 25% 20%, rgba(20,91,145,.25), transparent 36%), rgba(5,19,34,.91);
            padding: 20px;
            min-height: 285px;
        }}
        .ai-number {{ font-size: 3.4rem; font-weight: 850; line-height: 1; }}
        .ai-risk {{ font-size: 1.2rem; font-weight: 800; margin-top: 5px; }}
        .pill {{ display:inline-block; padding: 5px 10px; border-radius: 999px; background: rgba(38,213,125,.14); border:1px solid rgba(38,213,125,.45); color:#6ff0ae; font-size:.78rem; }}

        .alert-item {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,.08);
        }}
        .alert-item:last-child {{ border-bottom: 0; }}

        [data-testid="stMetric"] {{
            background: rgba(8,25,43,.72);
            border: 1px solid rgba(120,180,230,.16);
            border-radius: 14px;
            padding: 12px 14px;
        }}
        [data-testid="stMetricValue"] {{ font-weight: 800; }}

        div[data-testid="stButton"] > button {{
            border-radius: 10px;
            min-height: 44px;
            font-weight: 650;
        }}

        /* Live section summary UI */
        .live-summary {{
            position:relative; overflow:hidden; padding:18px 20px; margin:0 0 16px;
            border-radius:18px; background:linear-gradient(135deg, rgba(9,30,50,.94), rgba(5,17,30,.90));
            border:1px solid rgba(95,195,255,.22); box-shadow:0 10px 30px rgba(0,0,0,.16);
        }}
        .live-summary::after {{ content:""; position:absolute; width:150px; height:150px; right:-65px; top:-85px; border-radius:50%; border:1px solid rgba(104,214,255,.14); box-shadow:0 0 0 18px rgba(104,214,255,.025), 0 0 0 36px rgba(104,214,255,.018); }}
        .live-summary-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:14px; flex-wrap:wrap; }}
        .live-summary-kicker {{ color:#68d6ff; font-size:.67rem; font-weight:900; letter-spacing:.14em; text-transform:uppercase; }}
        .live-summary-title {{ font-size:1.12rem; font-weight:850; margin-top:3px; }}
        .live-summary-text {{ color:#a7b8c8; font-size:.82rem; line-height:1.48; margin-top:5px; max-width:900px; }}
        .live-summary-status {{ display:inline-flex; align-items:center; gap:7px; padding:7px 10px; border-radius:999px; background:rgba(61,224,145,.09); border:1px solid rgba(61,224,145,.28); color:#73efaa; font-size:.70rem; font-weight:850; white-space:nowrap; }}
        .live-summary-dot {{ width:7px; height:7px; border-radius:50%; background:#57e99b; box-shadow:0 0 11px rgba(87,233,155,.85); display:inline-block; }}
        .live-summary-grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:9px; margin-top:13px; }}
        .live-summary-stat {{ padding:10px 11px; border-radius:12px; background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.065); }}
        .live-summary-stat-label {{ color:#8197aa; font-size:.64rem; text-transform:uppercase; letter-spacing:.06em; font-weight:800; }}
        .live-summary-stat-value {{ color:#f4f8fc; font-size:1rem; font-weight:850; margin-top:2px; }}
        .live-summary-stat-note {{ color:#71899e; font-size:.64rem; margin-top:1px; }}
        .live-summary-update {{ color:#71899e; font-size:.66rem; margin-top:10px; }}
        @media (max-width: 900px) {{ .live-summary-grid {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}

        /* Sensor monitoring UI */
        .sensor-hero {{
            padding: 22px 24px;
            border-radius: 20px;
            background: radial-gradient(circle at 85% 15%, rgba(48,170,255,.16), transparent 30%), linear-gradient(135deg, rgba(9,31,51,.96), rgba(4,17,30,.92));
            border: 1px solid rgba(91,190,255,.28);
            box-shadow: 0 14px 38px rgba(0,0,0,.20);
            margin-bottom: 16px;
        }}
        .sensor-kicker {{ color:#68d6ff; font-size:.72rem; font-weight:850; letter-spacing:.15em; text-transform:uppercase; }}
        .sensor-title {{ font-size:2rem; font-weight:850; margin-top:5px; }}
        .sensor-subtitle {{ color:#9fb1c4; margin-top:5px; }}
        .sensor-live {{ display:inline-flex; align-items:center; gap:7px; padding:8px 12px; border-radius:999px; background:rgba(57,225,141,.10); border:1px solid rgba(57,225,141,.35); color:#70efad; font-weight:800; font-size:.78rem; }}
        .sensor-dot {{ width:8px; height:8px; border-radius:50%; background:#55e99b; box-shadow:0 0 12px rgba(85,233,155,.8); display:inline-block; }}
        .sensor-stat {{ padding:16px; min-height:108px; border-radius:16px; background:linear-gradient(135deg, rgba(9,30,49,.94), rgba(5,18,31,.88)); border:1px solid rgba(120,180,230,.18); box-shadow:0 10px 28px rgba(0,0,0,.16); }}
        .sensor-stat-label {{ color:#9fb1c4; font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }}
        .sensor-stat-value {{ font-size:1.9rem; font-weight:850; margin-top:5px; }}
        .sensor-stat-note {{ color:#6fe9aa; font-size:.75rem; margin-top:4px; }}
        .sensor-tile {{ padding:15px; border-radius:15px; background:rgba(7,24,41,.82); border:1px solid rgba(120,180,230,.16); margin-bottom:10px; }}
        .sensor-tile-head {{ display:flex; justify-content:space-between; align-items:center; gap:10px; }}
        .sensor-name {{ font-weight:800; }}
        .sensor-location {{ color:#8fa4b8; font-size:.76rem; margin-top:3px; }}
        .sensor-reading {{ font-size:1.55rem; font-weight:850; margin-top:9px; }}
        .sensor-status {{ padding:4px 9px; border-radius:999px; font-size:.7rem; font-weight:850; }}
        .sensor-progress {{ height:7px; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden; margin-top:9px; }}
        .sensor-progress-fill {{ height:100%; border-radius:999px; }}
        .sensor-section-label {{ font-size:1.15rem; font-weight:800; margin:18px 0 10px; }}
        .sensor-ai-card {{ padding:20px; border-radius:18px; background:radial-gradient(circle at 20% 20%, rgba(42,155,230,.18), transparent 38%), linear-gradient(135deg, rgba(8,29,49,.95), rgba(4,16,29,.94)); border:1px solid rgba(74,178,255,.34); }}
        .sensor-ai-value {{ font-size:3rem; font-weight:900; line-height:1; }}
        .sensor-ai-label {{ color:#9fb1c4; font-size:.82rem; margin-top:7px; }}
        .sensor-badge {{ display:inline-block; margin-top:10px; padding:5px 10px; border-radius:999px; font-weight:800; font-size:.75rem; }}
        .reports-hero {{
            position:relative; overflow:hidden; padding:26px 28px; border-radius:22px;
            background:radial-gradient(circle at 88% 16%, rgba(82,190,255,.20), transparent 31%), radial-gradient(circle at 10% 95%, rgba(135,78,255,.15), transparent 35%), linear-gradient(135deg, rgba(8,30,50,.98), rgba(5,17,30,.94));
            border:1px solid rgba(101,193,255,.30); box-shadow:0 16px 42px rgba(0,0,0,.24); margin:8px 0 18px;
        }}
        .reports-hero::after {{ content:""; position:absolute; width:210px; height:210px; right:-80px; bottom:-120px; border-radius:50%; border:1px solid rgba(112,204,255,.18); box-shadow:0 0 0 24px rgba(112,204,255,.035), 0 0 0 48px rgba(112,204,255,.022); }}
        .reports-kicker {{ color:#68d6ff; font-size:.70rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }}
        .reports-title {{ font-size:2rem; font-weight:900; margin:4px 0; }}
        .reports-subtitle {{ color:#9fb1c4; font-size:.90rem; max-width:780px; line-height:1.5; }}
        .reports-live {{ display:inline-flex; align-items:center; gap:8px; margin-top:14px; padding:7px 11px; border-radius:999px; background:rgba(61,224,145,.10); border:1px solid rgba(61,224,145,.30); color:#75efae; font-size:.75rem; font-weight:850; }}
        .reports-dot {{ width:8px; height:8px; border-radius:50%; background:#57e99b; box-shadow:0 0 12px rgba(87,233,155,.8); }}
        .reports-section {{ margin:20px 0 10px; font-size:1.08rem; font-weight:850; }}
        .report-scope {{ padding:11px 14px; border-radius:13px; margin:12px 0 14px; background:rgba(70,181,255,.07); border:1px solid rgba(70,181,255,.20); color:#b9cfe0; font-size:.78rem; }}
        .report-scope b {{ color:#70d5ff; letter-spacing:.08em; font-size:.68rem; }}
        .report-scope-count {{ float:right; color:#f3f7fb; font-weight:850; }}
        .report-kpi {{ min-height:105px; padding:15px 16px; border-radius:16px; background:linear-gradient(145deg, rgba(9,31,50,.94), rgba(5,18,31,.88)); border:1px solid rgba(120,180,230,.16); box-shadow:0 10px 28px rgba(0,0,0,.15); }}
        .report-kpi.red {{ border-color:rgba(255,55,80,.46); }}
        .report-kpi.orange {{ border-color:rgba(255,153,40,.45); }}
        .report-kpi.cyan {{ border-color:rgba(55,199,255,.45); }}
        .report-kpi.purple {{ border-color:rgba(170,112,255,.45); }}
        .report-kpi.green {{ border-color:rgba(43,211,126,.45); }}
        .report-kpi-label {{ color:#91a6ba; font-size:.70rem; text-transform:uppercase; letter-spacing:.07em; font-weight:800; }}
        .report-kpi-value {{ font-size:1.75rem; font-weight:900; margin-top:3px; }}
        .report-kpi-note {{ color:#7f96aa; font-size:.70rem; margin-top:2px; }}
        .report-insight {{ padding:17px; min-height:125px; border-radius:16px; background:rgba(7,24,41,.82); border:1px solid rgba(120,180,230,.15); }}
        .report-insight-icon {{ font-size:1.35rem; margin-bottom:7px; }}
        .report-insight p {{ color:#9fb1c4; font-size:.78rem; line-height:1.5; margin:6px 0 0; }}
        .executive-card {{ padding:20px; border-radius:18px; background:radial-gradient(circle at 5% 0%, rgba(73,177,255,.12), transparent 34%), linear-gradient(135deg, rgba(9,31,51,.94), rgba(5,18,31,.90)); border:1px solid rgba(92,181,245,.20); box-shadow:0 10px 30px rgba(0,0,0,.16); }}
        .executive-card.compact {{ min-height:180px; }}
        .executive-label {{ color:#68d6ff; font-size:.69rem; font-weight:900; letter-spacing:.12em; }}
        .executive-title {{ font-size:1.22rem; font-weight:850; margin:5px 0 10px; }}
        .executive-card p {{ color:#9fb1c4; font-size:.82rem; line-height:1.58; }}
        .metadata-row {{ display:flex; justify-content:space-between; gap:15px; padding:9px 0; border-bottom:1px solid rgba(255,255,255,.07); color:#8fa4b8; font-size:.78rem; }}
        .metadata-row:last-child {{ border-bottom:0; }}
        .metadata-row b {{ color:#f3f7fb; text-align:right; }}
        .report-action-banner {{ margin-top:14px; padding:15px 17px; border-radius:15px; background:linear-gradient(90deg, rgba(255,153,40,.10), rgba(255,75,90,.07)); border:1px solid rgba(255,153,40,.22); color:#f4d8b0; font-size:.82rem; line-height:1.5; }}
        .report-action-banner span {{ color:#a9b9c8; }}
        .settings-hero {{
            position:relative; overflow:hidden; padding:24px 26px; border-radius:22px;
            background:radial-gradient(circle at 88% 18%, rgba(77,184,255,.22), transparent 32%), radial-gradient(circle at 15% 100%, rgba(125,76,255,.16), transparent 34%), linear-gradient(135deg, rgba(8,30,50,.98), rgba(5,17,30,.94));
            border:1px solid rgba(101,193,255,.30); box-shadow:0 16px 42px rgba(0,0,0,.24); margin:8px 0 18px;
        }}
        .settings-hero::after {{ content:""; position:absolute; width:180px; height:180px; right:-70px; bottom:-90px; border-radius:50%; border:1px solid rgba(112,204,255,.18); box-shadow:0 0 0 22px rgba(112,204,255,.035), 0 0 0 44px rgba(112,204,255,.025); }}
        .settings-kicker {{ color:#68d6ff; font-size:.70rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }}
        .settings-title {{ font-size:2rem; font-weight:900; margin:4px 0 4px; }}
        .settings-subtitle {{ color:#9fb1c4; font-size:.90rem; max-width:720px; }}
        .settings-status {{ display:inline-flex; align-items:center; gap:8px; margin-top:14px; padding:7px 11px; border-radius:999px; background:rgba(61,224,145,.10); border:1px solid rgba(61,224,145,.30); color:#75efae; font-size:.75rem; font-weight:850; }}
        .settings-status-dot {{ width:8px; height:8px; border-radius:50%; background:#57e99b; box-shadow:0 0 12px rgba(87,233,155,.8); }}
        .settings-section {{ margin:18px 0 10px; font-size:1.05rem; font-weight:850; }}
        .settings-card {{ padding:17px; min-height:142px; border-radius:17px; background:linear-gradient(145deg, rgba(9,31,50,.92), rgba(5,18,31,.88)); border:1px solid rgba(120,180,230,.16); box-shadow:0 10px 28px rgba(0,0,0,.15); }}
        .settings-card-title {{ font-weight:850; font-size:.96rem; }}
        .settings-card-icon {{ font-size:1.35rem; margin-bottom:7px; }}
        .settings-card-desc {{ color:#8fa4b8; font-size:.76rem; line-height:1.45; margin-top:5px; }}
        .settings-mini {{ padding:13px 15px; border-radius:14px; background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.08); }}
        .settings-mini-label {{ color:#91a6ba; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }}
        .settings-mini-value {{ font-size:1.35rem; font-weight:900; margin-top:2px; }}
        .weight-panel {{ padding:18px; border-radius:18px; background:radial-gradient(circle at 0% 0%, rgba(82,183,255,.12), transparent 35%), rgba(6,22,38,.90); border:1px solid rgba(82,183,255,.20); }}
        .weight-badge {{ display:inline-block; padding:5px 9px; border-radius:999px; background:rgba(84,187,255,.10); border:1px solid rgba(84,187,255,.25); color:#75d7ff; font-size:.72rem; font-weight:850; }}
        .preview-card {{ padding:18px; border-radius:18px; background:linear-gradient(135deg, rgba(18,44,65,.82), rgba(7,24,41,.90)); border:1px solid rgba(120,180,230,.16); }}
        .preview-label {{ color:#91a6ba; font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }}
        .preview-value {{ font-size:1.75rem; font-weight:900; margin-top:4px; }}
        .settings-divider {{ height:1px; background:rgba(255,255,255,.08); margin:20px 0; }}
                
        /* ==========================================================
           SECTION-SPECIFIC BACKGROUND IMAGES
           Each page gets a different visual background while the
           glass overlay keeps Streamlit text readable.
           ========================================================== */
        .stApp:has(.section-marker) {{
            position:relative;
            background-color:#06111d !important;
        }}

        .stApp:has(.section-marker)::before {{
            content:"";
            position:fixed;
            inset:0;
            z-index:0;
            pointer-events:none;
            background-position:center;
            background-size:cover;
            background-repeat:no-repeat;
            opacity:.42;
            filter:saturate(1.08) contrast(1.03);
            transition:opacity .35s ease, background-image .35s ease;
        }}

        .stApp:has(.section-marker.dashboard)::before {{
            background-image:linear-gradient(180deg,rgba(2,12,24,.20),rgba(3,13,25,.70) 78%,rgba(3,13,25,.96)), url("https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=2200&q=85");
            opacity:.52;
        }}
        .stApp:has(.section-marker.riskmap)::before {{
            background-image:linear-gradient(180deg,rgba(2,22,17,.20),rgba(3,25,20,.70) 78%,rgba(3,17,18,.96)), url("https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=2200&q=85");
            opacity:.48;
        }}
        .stApp:has(.section-marker.alerts)::before {{
            background-image:linear-gradient(180deg,rgba(35,7,13,.18),rgba(38,10,16,.72) 78%,rgba(22,10,14,.97)), url("https://images.unsplash.com/photo-1534088568595-a066f410bcda?auto=format&fit=crop&w=2200&q=85");
            opacity:.45;
        }}
        .stApp:has(.section-marker.predictions)::before {{
            background-image:
                linear-gradient(180deg,rgba(20,7,2,.12),rgba(35,10,4,.58) 58%,rgba(12,7,10,.96) 100%),
                url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=2200&q=85");
            opacity:.50;
        }}
        .stApp:has(.section-marker.earlyalerts)::before {{
            background-image:
                linear-gradient(180deg,rgba(24,18,2,.10),rgba(38,20,4,.62) 55%,rgba(14,10,8,.97) 100%),
                url("https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=2200&q=85");
            opacity:.48;
        }}
        .stApp:has(.section-marker.sensors)::before {{
            background-image:linear-gradient(180deg,rgba(3,18,28,.18),rgba(3,23,35,.72) 78%,rgba(7,15,30,.97)), url("https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=2200&q=85");
            opacity:.44;
        }}
        .stApp:has(.section-marker.analytics)::before {{
            background-image:linear-gradient(180deg,rgba(20,6,34,.18),rgba(31,8,38,.73) 78%,rgba(25,10,24,.97)), url("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=2200&q=85");
            opacity:.40;
        }}
        .stApp:has(.section-marker.incidents)::before {{
            background-image:linear-gradient(180deg,rgba(37,16,4,.18),rgba(42,13,13,.72) 78%,rgba(27,9,18,.97)), url("https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=2200&q=85");
            opacity:.44;
        }}
        .stApp:has(.section-marker.reports)::before {{
            background-image:linear-gradient(180deg,rgba(3,24,25,.18),rgba(4,30,37,.72) 78%,rgba(6,17,29,.97)), url("https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=2200&q=85");
            opacity:.40;
        }}
        .stApp:has(.section-marker.settings)::before {{
            background-image:linear-gradient(180deg,rgba(12,10,31,.18),rgba(24,12,43,.72) 78%,rgba(19,9,29,.97)), url("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=2200&q=85");
            opacity:.40;
        }}

        /* Keep all real content above the image layer. */
        .stApp .main,
        .stApp [data-testid="stAppViewContainer"],
        .stApp [data-testid="stMain"],
        .stApp .block-container {{
            position:relative;
            z-index:1;
            background:transparent !important;
        }}

        /* Give every section a slightly translucent surface so the image
           remains visible instead of being hidden by opaque panels. */
        .stApp:has(.section-marker) .glass,
        .stApp:has(.section-marker) .risk-card,
        .stApp:has(.section-marker) .sensor-stat,
        .stApp:has(.section-marker) .sensor-tile,
        .stApp:has(.section-marker) .report-kpi,
        .stApp:has(.section-marker) .settings-card,
        .stApp:has(.section-marker) .preview-card,
        .stApp:has(.section-marker) .weight-panel,
        .stApp:has(.section-marker) .live-summary {{
            backdrop-filter:blur(12px);
            -webkit-backdrop-filter:blur(12px);
        }}

        /* SECTION COLOR SYSTEM — each module has its own visual identity */
        .section-accent {{ height:5px; width:100%; border-radius:999px; margin:4px 0 14px; box-shadow:0 0 18px rgba(255,255,255,.10); }}
        .section-accent.dashboard {{ background:linear-gradient(90deg,#00d4ff,#3b82f6,#8b5cf6); }}
        .section-accent.riskmap {{ background:linear-gradient(90deg,#00e5a8,#00b894,#22c55e); }}
        .section-accent.alerts {{ background:linear-gradient(90deg,#ff3d5a,#ff7a18,#ffd23f); }}
        .section-accent.predictions {{ background:linear-gradient(90deg,#f97316,#ef4444,#ec4899); box-shadow:0 0 24px rgba(249,115,22,.25); }}
        .section-accent.earlyalerts {{ background:linear-gradient(90deg,#facc15,#f97316,#ef4444); box-shadow:0 0 26px rgba(250,204,21,.24); }}
        .section-accent.sensors {{ background:linear-gradient(90deg,#06b6d4,#38bdf8,#6366f1); }}
        .section-accent.analytics {{ background:linear-gradient(90deg,#a855f7,#ec4899,#f43f5e); }}
        .section-accent.incidents {{ background:linear-gradient(90deg,#f59e0b,#ef4444,#ec4899); }}
        .section-accent.reports {{ background:linear-gradient(90deg,#14b8a6,#06b6d4,#3b82f6); }}
        .section-accent.settings {{ background:linear-gradient(90deg,#6366f1,#8b5cf6,#d946ef); }}

        /* Colorful module headers */
        .module-intro {{ position:relative; overflow:hidden; }}
        .module-intro::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:linear-gradient(180deg,#22d3ee,#8b5cf6); border-radius:16px 0 0 16px; }}
        .page-dashboard .module-intro::before {{ background:linear-gradient(180deg,#00d4ff,#6366f1); }}
        .page-riskmap .module-intro::before {{ background:linear-gradient(180deg,#00e5a8,#22c55e); }}
        .page-alerts .module-intro::before {{ background:linear-gradient(180deg,#ff3d5a,#ff9f1c); }}
        .page-predictions .module-intro::before {{ background:linear-gradient(180deg,#f97316,#ef4444,#ec4899); }}
        .page-sensors .module-intro::before {{ background:linear-gradient(180deg,#06b6d4,#3b82f6); }}
        .page-analytics .module-intro::before {{ background:linear-gradient(180deg,#a855f7,#ec4899); }}
        .page-incidents .module-intro::before {{ background:linear-gradient(180deg,#f59e0b,#ef4444); }}
        .page-reports .module-intro::before {{ background:linear-gradient(180deg,#14b8a6,#06b6d4); }}
        .page-settings .module-intro::before {{ background:linear-gradient(180deg,#6366f1,#d946ef); }}

        /* Colorful sidebar navigation */
        section[data-testid="stSidebar"] .stRadio > div {{ gap:5px; }}
        section[data-testid="stSidebar"] .stRadio label {{ transition:all .18s ease; border:1px solid transparent; }}
        section[data-testid="stSidebar"] .stRadio label:hover {{ background:rgba(255,255,255,.07); border-color:rgba(255,255,255,.10); transform:translateX(2px); }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(1) {{ border-left:3px solid #38bdf8; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(2) {{ border-left:3px solid #22c55e; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(3) {{ border-left:3px solid #ff4d6d; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(4) {{ border-left:3px solid #06b6d4; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(5) {{ border-left:3px solid #c084fc; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(6) {{ border-left:3px solid #f59e0b; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(7) {{ border-left:3px solid #14b8a6; }}
        section[data-testid="stSidebar"] .stRadio label:nth-of-type(8) {{ border-left:3px solid #8b5cf6; }}

        /* Give common cards more visual depth */
        .risk-card, .sensor-stat, .report-kpi, .glass {{ transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }}
        .risk-card:hover, .sensor-stat:hover, .report-kpi:hover, .glass:hover {{ transform:translateY(-2px); box-shadow:0 15px 35px rgba(0,0,0,.28); }}
        .section-title {{ display:flex; align-items:center; gap:8px; }}
        .section-title::before {{ content:""; width:8px; height:8px; border-radius:50%; background:linear-gradient(135deg,#22d3ee,#a855f7); box-shadow:0 0 10px rgba(34,211,238,.55); }}

        /* Dedicated Predicted Landslide Risk interface */
        .prediction-hero {{
            display:flex; align-items:center; gap:20px; padding:24px; margin:8px 0 16px;
            border:1px solid rgba(249,115,22,.34);
            background:radial-gradient(circle at 8% 50%,rgba(249,115,22,.18),transparent 32%),linear-gradient(135deg,rgba(53,18,9,.88),rgba(39,12,27,.88));
            box-shadow:0 18px 50px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.05);
        }}
        .prediction-orbit {{ width:66px;height:66px;border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2rem;
            background:linear-gradient(135deg,rgba(249,115,22,.28),rgba(236,72,153,.22)); border:1px solid rgba(255,170,100,.35);
            box-shadow:0 0 30px rgba(249,115,22,.18); animation:predictionPulse 2.8s ease-in-out infinite; }}
        .prediction-kicker {{ color:#ffae73;font-size:.72rem;font-weight:900;letter-spacing:.15em;text-transform:uppercase; }}
        .prediction-title {{ font-size:2rem;font-weight:900;margin-top:3px; }}
        .prediction-subtitle {{ color:#c8d3de;margin-top:5px; }}
        .prediction-pills {{ display:flex;gap:8px;flex-wrap:wrap;margin-top:13px; }}
        .prediction-pills span {{ padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);color:#f5f8ff;font-size:.72rem;font-weight:750; }}
        .prediction-control-panel {{ padding:13px 15px 3px;border-radius:18px;margin-bottom:14px;
            background:linear-gradient(135deg,rgba(46,17,8,.88),rgba(31,12,24,.86));border:1px solid rgba(249,115,22,.22); }}
        .prediction-lock-note {{ margin:10px 0 15px;padding:11px 14px;border-radius:13px;background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.20);color:#cfeede;font-size:.80rem; }}
        .prediction-card {{ --prediction-accent:#f97316; margin:10px 0;padding:17px 18px;border-radius:18px;
            background:linear-gradient(135deg,rgba(8,22,36,.94),rgba(32,15,22,.92));border:1px solid color-mix(in srgb,var(--prediction-accent) 32%, transparent);
            border-left:4px solid var(--prediction-accent);box-shadow:0 10px 30px rgba(0,0,0,.18);transition:.18s ease; }}
        .prediction-card:hover {{ transform:translateY(-2px);box-shadow:0 16px 34px rgba(0,0,0,.28); }}
        .prediction-card-top {{ display:flex;justify-content:space-between;align-items:center;gap:16px; }}
        .prediction-location {{ font-weight:900;font-size:1rem; }}
        .prediction-meta {{ display:flex;gap:8px;flex-wrap:wrap;margin-top:7px;color:#aebdcc;font-size:.73rem; }}
        .prediction-badge {{ padding:5px 9px;border-radius:999px;background:color-mix(in srgb,var(--prediction-accent) 15%, transparent);color:var(--prediction-accent);font-weight:900; }}
        .prediction-score {{ font-size:2rem;font-weight:950;color:var(--prediction-accent);white-space:nowrap; }}
        .prediction-score small {{ font-size:.9rem; }}
        .prediction-bar {{ height:7px;border-radius:99px;background:rgba(255,255,255,.08);margin:14px 0 12px;overflow:hidden; }}
        .prediction-bar span {{ display:block;height:100%;border-radius:99px; }}
        .prediction-mini-grid {{ display:grid;grid-template-columns:repeat(3,1fr);gap:9px; }}
        .prediction-mini-grid div {{ padding:8px 10px;border-radius:11px;background:rgba(255,255,255,.035); }}
        .prediction-mini-grid span {{ display:block;color:#8197aa;font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;font-weight:800; }}
        .prediction-mini-grid b {{ display:block;margin-top:2px;font-size:.9rem; }}
        .prediction-detail {{ --prediction-accent:#f97316; padding:20px;border:1px solid color-mix(in srgb,var(--prediction-accent) 34%, transparent);background:linear-gradient(145deg,rgba(47,17,10,.88),rgba(34,12,26,.90)); }}
        .detail-orb {{ font-size:1.5rem; }}
        .detail-level {{ color:var(--prediction-accent);font-weight:900;font-size:.72rem;letter-spacing:.12em;margin-top:5px; }}
        .detail-risk {{ font-size:3rem;font-weight:950;color:var(--prediction-accent);line-height:1;margin-top:5px; }}
        .detail-label {{ color:#93a6b7;font-size:.72rem;margin:4px 0 15px; }}
        .detail-row {{ display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-top:1px solid rgba(255,255,255,.07);font-size:.78rem; }}
        .detail-row span {{ color:#94a8ba; }} .detail-row b {{ text-align:right; }}
        .prediction-disclaimer {{ margin-top:16px;padding:14px 16px;border-radius:15px;background:rgba(255,193,7,.07);border:1px solid rgba(255,193,7,.20);color:#ead9ad;font-size:.78rem;line-height:1.5; }}
        @keyframes predictionPulse {{ 0%,100% {{ transform:scale(1);box-shadow:0 0 25px rgba(249,115,22,.14); }} 50% {{ transform:scale(1.045);box-shadow:0 0 35px rgba(236,72,153,.22); }} }}
        @media (max-width:700px) {{ .prediction-title {{font-size:1.5rem;}} .prediction-mini-grid {{grid-template-columns:1fr;}} .prediction-card-top {{align-items:flex-start;}} }}


        /* ==========================================================
           STRONG SECTION THEMES
           The marker lets CSS theme the native Streamlit widgets and
           custom cards for the currently selected module.
           ========================================================== */
        .section-marker {{ display:none; }}

        .stApp:has(.section-marker.dashboard) {{
            --section-main:#22d3ee; --section-main2:#3b82f6; --section-soft:rgba(34,211,238,.16); --section-soft2:rgba(59,130,246,.10); --section-border:rgba(34,211,238,.42);
        }}
        .stApp:has(.section-marker.riskmap) {{
            --section-main:#22c55e; --section-main2:#00e5a8; --section-soft:rgba(34,197,94,.17); --section-soft2:rgba(0,229,168,.10); --section-border:rgba(34,197,94,.44);
        }}
        .stApp:has(.section-marker.alerts) {{
            --section-main:#ff4d6d; --section-main2:#ff9f1c; --section-soft:rgba(255,77,109,.18); --section-soft2:rgba(255,159,28,.11); --section-border:rgba(255,77,109,.46);
        }}
        .stApp:has(.section-marker.predictions) {{
            --section-main:#f97316; --section-main2:#ec4899; --section-soft:rgba(249,115,22,.18); --section-soft2:rgba(236,72,153,.11); --section-border:rgba(249,115,22,.46);
        }}
        .stApp:has(.section-marker.earlyalerts) {{
            --section-main:#facc15; --section-main2:#f97316; --section-soft:rgba(250,204,21,.18); --section-soft2:rgba(249,115,22,.11); --section-border:rgba(250,204,21,.46);
        }}
        .stApp:has(.section-marker.sensors) {{
            --section-main:#06b6d4; --section-main2:#6366f1; --section-soft:rgba(6,182,212,.17); --section-soft2:rgba(99,102,241,.11); --section-border:rgba(6,182,212,.44);
        }}
        .stApp:has(.section-marker.analytics) {{
            --section-main:#a855f7; --section-main2:#ec4899; --section-soft:rgba(168,85,247,.18); --section-soft2:rgba(236,72,153,.11); --section-border:rgba(168,85,247,.46);
        }}
        .stApp:has(.section-marker.incidents) {{
            --section-main:#f59e0b; --section-main2:#ef4444; --section-soft:rgba(245,158,11,.18); --section-soft2:rgba(239,68,68,.11); --section-border:rgba(245,158,11,.46);
        }}
        .stApp:has(.section-marker.reports) {{
            --section-main:#14b8a6; --section-main2:#3b82f6; --section-soft:rgba(20,184,166,.17); --section-soft2:rgba(59,130,246,.11); --section-border:rgba(20,184,166,.44);
        }}
        .stApp:has(.section-marker.settings) {{
            --section-main:#8b5cf6; --section-main2:#d946ef; --section-soft:rgba(139,92,246,.18); --section-soft2:rgba(217,70,239,.11); --section-border:rgba(139,92,246,.46);
        }}

        /* STRONG SECTION BACKGROUNDS — the full page changes colour */
        .stApp:has(.section-marker.dashboard) {{ background:radial-gradient(circle at 10% 12%,rgba(0,212,255,.30),transparent 30%),radial-gradient(circle at 90% 20%,rgba(59,130,246,.28),transparent 34%),radial-gradient(circle at 55% 92%,rgba(139,92,246,.20),transparent 40%),linear-gradient(135deg,#061827,#071b31 50%,#10102b) !important; }}
        .stApp:has(.section-marker.riskmap) {{ background:radial-gradient(circle at 10% 12%,rgba(0,229,168,.30),transparent 30%),radial-gradient(circle at 90% 20%,rgba(34,197,94,.28),transparent 34%),radial-gradient(circle at 55% 92%,rgba(16,185,129,.20),transparent 40%),linear-gradient(135deg,#061b1a,#082a24 50%,#071d20) !important; }}
        .stApp:has(.section-marker.alerts) {{ background:radial-gradient(circle at 10% 12%,rgba(255,61,90,.32),transparent 30%),radial-gradient(circle at 90% 20%,rgba(255,122,24,.30),transparent 34%),radial-gradient(circle at 55% 92%,rgba(255,210,63,.16),transparent 40%),linear-gradient(135deg,#220d18,#32151b 50%,#211617) !important; }}
        .stApp:has(.section-marker.predictions) {{ background:radial-gradient(circle at 10% 8%,rgba(249,115,22,.34),transparent 28%),radial-gradient(circle at 92% 18%,rgba(236,72,153,.28),transparent 32%),radial-gradient(circle at 55% 88%,rgba(239,68,68,.18),transparent 38%),linear-gradient(135deg,#241006,#35130e 48%,#1f0b17) !important; }}
        .stApp:has(.section-marker.earlyalerts) {{ background:radial-gradient(circle at 8% 10%,rgba(250,204,21,.28),transparent 28%),radial-gradient(circle at 92% 16%,rgba(249,115,22,.30),transparent 31%),radial-gradient(circle at 55% 90%,rgba(239,68,68,.18),transparent 40%),linear-gradient(135deg,#211707,#30200a 50%,#1e1010) !important; }}
        .stApp:has(.section-marker.sensors) {{ background:radial-gradient(circle at 10% 12%,rgba(6,182,212,.32),transparent 30%),radial-gradient(circle at 90% 20%,rgba(99,102,241,.30),transparent 34%),radial-gradient(circle at 55% 92%,rgba(56,189,248,.18),transparent 40%),linear-gradient(135deg,#061a25,#08283b 50%,#101b3b) !important; }}
        .stApp:has(.section-marker.analytics) {{ background:radial-gradient(circle at 10% 12%,rgba(168,85,247,.32),transparent 30%),radial-gradient(circle at 90% 20%,rgba(236,72,153,.30),transparent 34%),radial-gradient(circle at 55% 92%,rgba(244,63,94,.18),transparent 40%),linear-gradient(135deg,#180b2b,#2b1038 50%,#24121f) !important; }}
        .stApp:has(.section-marker.incidents) {{ background:radial-gradient(circle at 10% 12%,rgba(245,158,11,.32),transparent 30%),radial-gradient(circle at 90% 20%,rgba(239,68,68,.30),transparent 34%),radial-gradient(circle at 55% 92%,rgba(236,72,153,.18),transparent 40%),linear-gradient(135deg,#28140a,#35151a 50%,#27101d) !important; }}
        .stApp:has(.section-marker.reports) {{ background:radial-gradient(circle at 10% 12%,rgba(20,184,166,.31),transparent 30%),radial-gradient(circle at 90% 20%,rgba(59,130,246,.29),transparent 34%),radial-gradient(circle at 55% 92%,rgba(6,182,212,.18),transparent 40%),linear-gradient(135deg,#061c20,#082d35 50%,#0a1d32) !important; }}
        .stApp:has(.section-marker.settings) {{ background:radial-gradient(circle at 10% 12%,rgba(99,102,241,.32),transparent 30%),radial-gradient(circle at 90% 20%,rgba(217,70,239,.30),transparent 34%),radial-gradient(circle at 55% 92%,rgba(139,92,246,.19),transparent 40%),linear-gradient(135deg,#11102d,#20153b 50%,#28122d) !important; }}

        /* Make the content area transparent so the section background is visible */
        .stApp .main, .stApp [data-testid="stAppViewContainer"], .stApp [data-testid="stMain"] {{ background:transparent !important; }}
        .stApp .block-container {{ background:transparent !important; }}

        /* Stronger colourful card surfaces */
        .stApp:has(.section-marker.dashboard) .glass,
        .stApp:has(.section-marker.dashboard) .risk-card {{ background:linear-gradient(145deg,rgba(0,174,239,.22),rgba(15,45,75,.88)); }}
        .stApp:has(.section-marker.riskmap) .glass,
        .stApp:has(.section-marker.riskmap) .risk-card {{ background:linear-gradient(145deg,rgba(0,210,150,.22),rgba(8,55,43,.88)); }}
        .stApp:has(.section-marker.alerts) .glass,
        .stApp:has(.section-marker.alerts) .risk-card {{ background:linear-gradient(145deg,rgba(255,55,80,.23),rgba(65,25,28,.88)); }}
        .stApp:has(.section-marker.predictions) .glass,
        .stApp:has(.section-marker.predictions) .risk-card {{ background:linear-gradient(145deg,rgba(249,115,22,.22),rgba(64,22,18,.88)); }}
        .stApp:has(.section-marker.earlyalerts) .glass,
        .stApp:has(.section-marker.earlyalerts) .risk-card {{ background:linear-gradient(145deg,rgba(250,204,21,.18),rgba(58,30,8,.90)); }}
        .stApp:has(.section-marker.sensors) .glass,
        .stApp:has(.section-marker.sensors) .risk-card {{ background:linear-gradient(145deg,rgba(6,182,212,.22),rgba(13,39,70,.88)); }}
        .stApp:has(.section-marker.analytics) .glass,
        .stApp:has(.section-marker.analytics) .risk-card {{ background:linear-gradient(145deg,rgba(168,85,247,.23),rgba(55,22,66,.88)); }}
        .stApp:has(.section-marker.incidents) .glass,
        .stApp:has(.section-marker.incidents) .risk-card {{ background:linear-gradient(145deg,rgba(245,158,11,.23),rgba(66,28,25,.88)); }}
        .stApp:has(.section-marker.reports) .glass,
        .stApp:has(.section-marker.reports) .risk-card {{ background:linear-gradient(145deg,rgba(20,184,166,.22),rgba(10,48,60,.88)); }}
        .stApp:has(.section-marker.settings) .glass,
        .stApp:has(.section-marker.settings) .risk-card {{ background:linear-gradient(145deg,rgba(139,92,246,.23),rgba(38,27,70,.88)); }}

        /* Strong theme wash over the active page */
        .stApp:has(.section-marker) .block-container {{
            position:relative;
        }}
        .stApp:has(.section-marker) .block-container::before {{
            content:""; position:fixed; pointer-events:none; z-index:0;
            top:0; right:0; width:48vw; height:70vh;
            background:radial-gradient(circle at 80% 12%, var(--section-soft), transparent 62%);
            opacity:.55;
        }}
        .stApp:has(.section-marker) .block-container > div {{ position:relative; z-index:1; }}

        /* Headings and common native components */
        .stApp:has(.section-marker) h1,
        .stApp:has(.section-marker) h2,
        .stApp:has(.section-marker) h3 {{ text-shadow:0 0 24px var(--section-soft); }}
        .stApp:has(.section-marker) h2 {{ border-left:4px solid var(--section-main); padding-left:12px; }}
        .stApp:has(.section-marker) [data-testid="stMetric"] {{
            background:linear-gradient(145deg,var(--section-soft),rgba(7,24,41,.88) 62%);
            border:1px solid var(--section-border);
            box-shadow:0 10px 30px rgba(0,0,0,.22), 0 0 20px var(--section-soft2);
        }}
        .stApp:has(.section-marker) [data-testid="stMetricValue"] {{ color:#ffffff; text-shadow:0 0 16px var(--section-soft); }}
        .stApp:has(.section-marker) [data-testid="stMetricLabel"] {{ color:#b8cad9; }}

        /* Buttons */
        .stApp:has(.section-marker) div[data-testid="stButton"] > button,
        .stApp:has(.section-marker) div[data-testid="stDownloadButton"] > button {{
            background:linear-gradient(135deg,var(--section-main),var(--section-main2));
            color:#06111d; border:0; font-weight:850;
            box-shadow:0 7px 22px var(--section-soft2);
            transition:all .18s ease;
        }}
        .stApp:has(.section-marker) div[data-testid="stButton"] > button:hover,
        .stApp:has(.section-marker) div[data-testid="stDownloadButton"] > button:hover {{
            filter:brightness(1.13); transform:translateY(-2px); box-shadow:0 11px 28px var(--section-soft);
        }}

        /* Select boxes, sliders, toggles, text inputs and text areas */
        .stApp:has(.section-marker) div[data-baseweb="select"] > div,
        .stApp:has(.section-marker) div[data-baseweb="input"],
        .stApp:has(.section-marker) textarea,
        .stApp:has(.section-marker) input {{
            border-color:var(--section-border) !important;
            box-shadow:0 0 0 1px var(--section-soft2);
        }}
        .stApp:has(.section-marker) div[data-baseweb="select"] > div:focus-within,
        .stApp:has(.section-marker) div[data-baseweb="input"]:focus-within,
        .stApp:has(.section-marker) textarea:focus,
        .stApp:has(.section-marker) input:focus {{
            border-color:var(--section-main) !important;
            box-shadow:0 0 0 2px var(--section-soft2), 0 0 18px var(--section-soft2) !important;
        }}
        .stApp:has(.section-marker) [data-testid="stSlider"] [role="slider"] {{ background:var(--section-main); border-color:var(--section-main); }}
        .stApp:has(.section-marker) [data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {{ background:linear-gradient(90deg,var(--section-main),var(--section-main2)); }}
        .stApp:has(.section-marker) [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div,
        .stApp:has(.section-marker) [data-testid="stToggle"] [data-baseweb="checkbox"] > div {{ border-color:var(--section-border); }}

        /* Tabs and expanders */
        .stApp:has(.section-marker) button[data-baseweb="tab"] {{ color:#9fb1c4; }}
        .stApp:has(.section-marker) button[data-baseweb="tab"][aria-selected="true"] {{ color:var(--section-main); border-bottom-color:var(--section-main) !important; }}
        .stApp:has(.section-marker) [data-testid="stExpander"] {{
            border:1px solid var(--section-border); border-radius:16px; background:linear-gradient(145deg,var(--section-soft2),rgba(5,18,31,.78));
        }}

        /* Custom cards used throughout the application */
        .stApp:has(.section-marker) .glass,
        .stApp:has(.section-marker) .risk-card,
        .stApp:has(.section-marker) .sensor-stat,
        .stApp:has(.section-marker) .sensor-tile,
        .stApp:has(.section-marker) .report-kpi,
        .stApp:has(.section-marker) .report-insight,
        .stApp:has(.section-marker) .executive-card,
        .stApp:has(.section-marker) .settings-card,
        .stApp:has(.section-marker) .settings-mini,
        .stApp:has(.section-marker) .preview-card,
        .stApp:has(.section-marker) .weight-panel,
        .stApp:has(.section-marker) .live-summary {{
            background:linear-gradient(145deg,var(--section-soft),rgba(8,27,45,.90) 55%,var(--section-soft2));
            border-color:var(--section-border);
            box-shadow:0 12px 34px rgba(0,0,0,.23), 0 0 24px var(--section-soft2);
        }}
        .stApp:has(.section-marker) .live-summary-kicker,
        .stApp:has(.section-marker) .reports-kicker,
        .stApp:has(.section-marker) .settings-kicker,
        .stApp:has(.section-marker) .sensor-kicker {{ color:var(--section-main); }}
        .stApp:has(.section-marker) .live-summary-stat {{ background:rgba(255,255,255,.045); border-color:var(--section-border); }}
        .stApp:has(.section-marker) .section-title::before {{ background:linear-gradient(135deg,var(--section-main),var(--section-main2)); box-shadow:0 0 13px var(--section-main); }}

        /* Tables/dataframes get the active section border */
        .stApp:has(.section-marker) [data-testid="stDataFrame"] {{
            border:1px solid var(--section-border); border-radius:14px; overflow:hidden; box-shadow:0 10px 28px rgba(0,0,0,.20);
        }}

        /* Per-module custom hero overrides */
        .stApp:has(.section-marker.dashboard) .ai-panel {{ background:radial-gradient(circle at 20% 20%,rgba(34,211,238,.25),transparent 38%),linear-gradient(135deg,rgba(10,48,72,.96),rgba(5,18,32,.92)); border-color:rgba(34,211,238,.48); }}
        .stApp:has(.section-marker.riskmap) .glass {{ background:linear-gradient(145deg,rgba(0,229,168,.16),rgba(5,30,25,.92)); }}
        .stApp:has(.section-marker.alerts) .glass {{ background:linear-gradient(145deg,rgba(255,77,109,.16),rgba(42,20,24,.92)); }}
        .stApp:has(.section-marker.sensors) .sensor-hero,
        .stApp:has(.section-marker.sensors) .sensor-ai-card {{ background:radial-gradient(circle at 82% 15%,rgba(6,182,212,.24),transparent 35%),linear-gradient(135deg,rgba(7,42,58,.96),rgba(8,20,42,.92)); border-color:rgba(6,182,212,.48); }}
        .stApp:has(.section-marker.analytics) .glass {{ background:linear-gradient(145deg,rgba(168,85,247,.17),rgba(37,17,47,.92)); }}
        .stApp:has(.section-marker.incidents) .glass {{ background:linear-gradient(145deg,rgba(245,158,11,.17),rgba(45,22,22,.92)); }}
        .stApp:has(.section-marker.reports) .reports-hero {{ background:radial-gradient(circle at 88% 16%,rgba(20,184,166,.25),transparent 31%),radial-gradient(circle at 10% 95%,rgba(59,130,246,.18),transparent 35%),linear-gradient(135deg,rgba(7,47,50,.98),rgba(5,18,34,.94)); border-color:rgba(20,184,166,.48); }}
        .stApp:has(.section-marker.settings) .settings-hero {{ background:radial-gradient(circle at 88% 18%,rgba(139,92,246,.28),transparent 32%),radial-gradient(circle at 15% 100%,rgba(217,70,239,.20),transparent 34%),linear-gradient(135deg,rgba(35,24,67,.98),rgba(12,17,35,.94)); border-color:rgba(139,92,246,.48); }}

         /* ==========================================================
            SCROLL + TEXT VISIBILITY FIX
            Keep the decorative background in the page flow so it
            scrolls naturally with the Streamlit content. Prevent
            horizontal overflow from wide charts/cards.
            ========================================================== */
         html, body, .stApp {{
             max-width:100%;
             overflow-x:hidden !important;
         }}

         /* Keep decorative layers out of document flow so they never
            create extra scrollable height. Only the actual Streamlit
            content determines the page length. */
         .stApp:has(.section-marker)::before {{
             position:fixed;
             inset:0;
             width:100%;
             height:100%;
             pointer-events:none;
             background-attachment:fixed;
         }}

         .dashboard-image-bg {{
             position:fixed;
             top:0;
             left:0;
             right:0;
             width:100%;
             height:650px;
             max-height:650px;
             background-attachment:fixed;
             pointer-events:none;
         }}

         /* ==========================================================
            FINAL MAIN SCROLL CONTAINER
            The app shell stays fixed to the browser viewport while the
            actual Streamlit main column gets its own vertical scrollbar.
            This keeps the main display independent from the sidebar.
            ========================================================== */
         html, body, .stApp {{
             width:100%;
             max-width:100%;
             min-height:100%;
             overflow-x:hidden !important;
         }}

         [data-testid="stAppViewContainer"] {{
             position:relative !important;
             height:100vh !important;
             max-height:100vh !important;
             min-height:0 !important;
             overflow:hidden !important;
         }}

         [data-testid="stAppViewContainer"] > .main {{
             height:100vh !important;
             max-height:100vh !important;
             min-height:0 !important;
             overflow-y:auto !important;
             overflow-x:hidden !important;
             overscroll-behavior:contain;
             -webkit-overflow-scrolling:touch;
             scrollbar-width:auto;
         }}

         [data-testid="stAppViewContainer"] > .main > div,
         [data-testid="stMain"],
         [data-testid="stMainBlockContainer"] {{
             min-height:0 !important;
             height:auto !important;
             overflow-x:hidden !important;
         }}

         [data-testid="stAppViewContainer"] > .main .block-container {{
             min-height:0 !important;
             height:auto !important;
             padding-bottom:5rem !important;
         }}

         /* High-contrast text for every active section. */
         .stApp:has(.section-marker) [data-testid="stMarkdownContainer"],
         .stApp:has(.section-marker) [data-testid="stCaptionContainer"],
         .stApp:has(.section-marker) [data-testid="stText"],
         .stApp:has(.section-marker) .stMarkdown,
         .stApp:has(.section-marker) p,
         .stApp:has(.section-marker) li,
         .stApp:has(.section-marker) label,
         .stApp:has(.section-marker) [data-testid="stWidgetLabel"],
         .stApp:has(.section-marker) [data-testid="stWidgetLabel"] p,
         .stApp:has(.section-marker) [data-baseweb="select"] *,
         .stApp:has(.section-marker) [data-baseweb="input"] *,
         .stApp:has(.section-marker) textarea,
         .stApp:has(.section-marker) input {{
             color:#f5f8ff !important;
         }}

         .stApp:has(.section-marker) [data-testid="stCaptionContainer"],
         .stApp:has(.section-marker) [data-testid="stCaptionContainer"] *,
         .stApp:has(.section-marker) small {{
             color:#c4d3e2 !important;
         }}

         .stApp:has(.section-marker) [data-testid="stWidgetLabel"] p,
         .stApp:has(.section-marker) [data-testid="stWidgetLabel"] {{
             font-weight:700 !important;
             color:#eef5ff !important;
         }}

         /* Section-aware muted text: bright enough against the image,
            but still visually secondary to headings. */
         .stApp:has(.section-marker.dashboard) .small-muted,
         .stApp:has(.section-marker.dashboard) .live-summary-stat-note {{ color:#aee9ff !important; }}
         .stApp:has(.section-marker.riskmap) .small-muted,
         .stApp:has(.section-marker.riskmap) .live-summary-stat-note {{ color:#b6f7d8 !important; }}
         .stApp:has(.section-marker.alerts) .small-muted,
         .stApp:has(.section-marker.alerts) .live-summary-stat-note {{ color:#ffd0d7 !important; }}
         .stApp:has(.section-marker.predictions) .small-muted,
         .stApp:has(.section-marker.predictions) .live-summary-stat-note {{ color:#ffd3b5 !important; }}
         .stApp:has(.section-marker.sensors) .small-muted,
         .stApp:has(.section-marker.sensors) .live-summary-stat-note {{ color:#bcefff !important; }}
         .stApp:has(.section-marker.analytics) .small-muted,
         .stApp:has(.section-marker.analytics) .live-summary-stat-note {{ color:#f0d5ff !important; }}
         .stApp:has(.section-marker.incidents) .small-muted,
         .stApp:has(.section-marker.incidents) .live-summary-stat-note {{ color:#ffe1c2 !important; }}
         .stApp:has(.section-marker.reports) .small-muted,
         .stApp:has(.section-marker.reports) .live-summary-stat-note {{ color:#c5f7ef !important; }}
         .stApp:has(.section-marker.settings) .small-muted,
         .stApp:has(.section-marker.settings) .live-summary-stat-note {{ color:#e3d6ff !important; }}

         /* Make native inputs readable on every theme. */
         .stApp:has(.section-marker) [data-baseweb="select"] > div,
         .stApp:has(.section-marker) [data-baseweb="input"] > div,
         .stApp:has(.section-marker) textarea,
         .stApp:has(.section-marker) input {{
             background:rgba(8,18,32,.82) !important;
         }}

         .stApp:has(.section-marker) [data-baseweb="select"] span,
         .stApp:has(.section-marker) [data-baseweb="select"] input {{
             color:#f5f8ff !important;
         }}

         /* Dropdown menu text. */
         [data-baseweb="popover"], [data-baseweb="menu"] {{
             color:#f5f8ff !important;
         }}
         [data-baseweb="menu"] * {{ color:#f5f8ff !important; }}

         /* Improve readability of tables and dataframe text. */
         .stApp:has(.section-marker) [data-testid="stDataFrame"] *,
         .stApp:has(.section-marker) [data-testid="stTable"] *,
         .stApp:has(.section-marker) code {{
             color:#f4f8ff !important;
         }}

         /* Keep normal vertical page scrolling and eliminate accidental
            horizontal scrolling from wide elements. */
         .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"],
         [data-testid="stMain"], .main, .block-container {{
             overflow-x:hidden !important;
         }}
</style>
        """,
        unsafe_allow_html=True,
    )


set_background(IMAGE_PATH)


# DATABASE
# ============================================================

def init_incident_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reported_at TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                severity TEXT NOT NULL,
                road_blocked TEXT NOT NULL,
                village TEXT,
                description TEXT,
                photo_name TEXT,
                photo_data BLOB,
                verification_status TEXT DEFAULT 'UNVERIFIED',
                verification_confidence REAL DEFAULT 0,
                camera_source TEXT DEFAULT '',
                notification_status TEXT DEFAULT 'NOT SENT'
            )
            """
        )
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(incidents)").fetchall()}
        migrations = {
            "verification_status": "ALTER TABLE incidents ADD COLUMN verification_status TEXT DEFAULT 'UNVERIFIED'",
            "verification_confidence": "ALTER TABLE incidents ADD COLUMN verification_confidence REAL DEFAULT 0",
            "camera_source": "ALTER TABLE incidents ADD COLUMN camera_source TEXT DEFAULT ''",
            "notification_status": "ALTER TABLE incidents ADD COLUMN notification_status TEXT DEFAULT 'NOT SENT'",
        }
        for column, statement in migrations.items():
            if column not in existing_columns:
                conn.execute(statement)
        conn.commit()


def save_incident(
    latitude,
    longitude,
    severity,
    road_blocked,
    village,
    description,
    photo_name,
    photo_data,
    verification_status="UNVERIFIED",
    verification_confidence=0.0,
    camera_source="",
    notification_status="NOT SENT",
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO incidents
            (
                reported_at,
                latitude,
                longitude,
                severity,
                road_blocked,
                village,
                description,
                photo_name,
                photo_data,
                verification_status,
                verification_confidence,
                camera_source,
                notification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                float(latitude),
                float(longitude),
                severity,
                road_blocked,
                village,
                description,
                photo_name,
                photo_data,
                verification_status,
                float(verification_confidence),
                camera_source,
                notification_status,
            ),
        )
        conn.commit()


def load_incidents(include_photo=False):
    columns = (
        "id, reported_at, latitude, longitude, severity, "
        "road_blocked, village, description, photo_name, verification_status, "
        "verification_confidence, camera_source, notification_status"
    )

    if include_photo:
        columns += ", photo_data"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(
                f"SELECT {columns} FROM incidents ORDER BY id DESC",
                conn,
            )
    except Exception:
        return pd.DataFrame()


init_incident_db()


# ============================================================
# DATA / MODEL
# ============================================================

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        return None

    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


@st.cache_data
def load_csv(path: Path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


model = load_model()

risk_df = load_csv(RISK_DATA_PATH)
road_df = load_csv(ROAD_DATA_PATH)
infra_df = load_csv(INFRA_DATA_PATH)
village_df = load_csv(VILLAGE_DATA_PATH)


# ============================================================
# AI RISK ENGINE
# ============================================================

FEATURE_COLUMNS = [
    "rainfall_mm",
    "soil_moisture",
    "slope_deg",
    "ground_movement_mm",
    "elevation_m",
]


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_ai_probability(row):
    rainfall = safe_float(row.get("rainfall_mm", 100), 100)
    moisture = safe_float(row.get("soil_moisture", 60), 60)
    slope = safe_float(row.get("slope_deg", 30), 30)
    movement = safe_float(row.get("ground_movement_mm", 5), 5)
    elevation = safe_float(row.get("elevation_m", 1500), 1500)

    if model is not None:
        try:
            input_data = pd.DataFrame(
                [[rainfall, moisture, slope, movement, elevation]],
                columns=FEATURE_COLUMNS,
            )

            probability = (
                model.predict_proba(input_data)[0][1] * 100
            )

            return round(max(0.0, min(100.0, float(probability))), 2)

        except Exception:
            pass

    try:
        score, _ = calculate_risk(
            rainfall,
            moisture,
            slope,
            movement,
            elevation,
        )
        return round(max(0.0, min(100.0, float(score))), 2)
    except Exception:
        return 0.0


def get_risk_level(probability):
    probability = safe_float(probability)

    if probability >= 80:
        return "CRITICAL"
    if probability >= 60:
        return "HIGH"
    if probability >= 40:
        return "MODERATE"
    return "LOW"


def risk_color(level):
    return {
        "CRITICAL": "red",
        "HIGH": "orange",
        "MODERATE": "beige",
        "LOW": "green",
    }.get(level, "blue")


def risk_message(level):
    return {
        "CRITICAL": (
            "🚨 VERY HIGH PROBABILITY — Immediate field assessment "
            "and emergency preparedness are recommended."
        ),
        "HIGH": (
            "⚠️ HIGH PROBABILITY — Increase monitoring and keep "
            "response teams prepared."
        ),
        "MODERATE": (
            "🟡 MODERATE PROBABILITY — Continue close monitoring "
            "of rainfall, soil moisture and ground movement."
        ),
        "LOW": (
            "🟢 LOW PROBABILITY — Continue routine environmental monitoring."
        ),
    }.get(level, "Continue monitoring.")


def get_recommended_action(level):
    return {
        "CRITICAL": (
            "Immediate field assessment recommended. Prepare community "
            "warning and inspect vulnerable roads."
        ),
        "HIGH": (
            "Increase monitoring, inspect slopes and keep emergency "
            "response teams prepared."
        ),
        "MODERATE": (
            "Continue monitoring rainfall, soil moisture and ground movement."
        ),
        "LOW": "Continue routine environmental monitoring.",
    }.get(level, "Continue monitoring.")


# ============================================================
# REAL-TIME PROTOTYPE SENSOR ENGINE
# ============================================================

def get_live_sensor_values():
    if "live_sensors" not in st.session_state:
        st.session_state.live_sensors = {
            "rainfall_mm": 164.0,
            "soil_moisture": 68.0,
            "slope_deg": 28.0,
            "ground_movement_mm": 6.4,
            "elevation_m": 1320.0,
        }
    return st.session_state.live_sensors


def refresh_live_sensor_values():
    import random
    values = get_live_sensor_values()
    values["rainfall_mm"] = round(max(0, values["rainfall_mm"] + random.uniform(-8, 14)), 1)
    values["soil_moisture"] = round(max(0, min(100, values["soil_moisture"] + random.uniform(-2, 2))), 1)
    values["slope_deg"] = round(max(0, values["slope_deg"] + random.uniform(-0.4, 0.4)), 1)
    values["ground_movement_mm"] = round(max(0, values["ground_movement_mm"] + random.uniform(-0.8, 1.2)), 1)
    values["elevation_m"] = round(max(0, values["elevation_m"] + random.uniform(-2, 2)), 1)


def get_live_risk():
    values = get_live_sensor_values()
    probability = get_ai_probability(pd.Series(values))
    return probability, get_risk_level(probability), values


live_probability, live_risk_level, live_values = get_live_risk()


# ============================================================
# GEOGRAPHIC HELPERS
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1 = math.radians(safe_float(lat1))
    lat2 = math.radians(safe_float(lat2))
    delta_lat = lat2 - lat1
    delta_lon = math.radians(
        safe_float(lon2) - safe_float(lon1)
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(max(0.0, 1 - a)),
    )

    return radius * c


# ============================================================
# VILLAGE PRIORITY ENGINE
# ============================================================

@st.cache_data
def calculate_village_priorities(risk_data, village_data):
    if village_data.empty:
        return pd.DataFrame()

    risk_points = []

    if not risk_data.empty:
        for _, row in risk_data.iterrows():
            try:
                probability = get_ai_probability(row)

                risk_points.append(
                    {
                        "latitude": safe_float(row.get("latitude")),
                        "longitude": safe_float(row.get("longitude")),
                        "probability": probability,
                        "risk_level": get_risk_level(probability),
                    }
                )
            except Exception:
                continue

    results = []

    for _, row in village_data.iterrows():
        village_lat = safe_float(row.get("latitude"))
        village_lon = safe_float(row.get("longitude"))

        nearest_probability = 0.0
        nearest_risk_level = "LOW"
        nearest_distance = None

        for point in risk_points:
            distance = calculate_distance(
                village_lat,
                village_lon,
                point["latitude"],
                point["longitude"],
            )

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_probability = point["probability"]
                nearest_risk_level = point["risk_level"]

        population = safe_float(row.get("population", 0))

        population_score = min(
            population / 20000 * 100,
            100,
        )

        connectivity = str(
            row.get("road_connectivity", "Medium")
        ).lower()

        connectivity_score = {
            "low": 100,
            "medium": 60,
            "high": 30,
        }.get(connectivity, 60)

        importance = str(
            row.get("importance", "Medium")
        ).lower()

        importance_score = {
            "critical": 100,
            "high": 70,
            "medium": 40,
        }.get(importance, 40)

        ai_score = nearest_probability

        priority_score = (
            ai_score * 0.40
            + population_score * 0.20
            + connectivity_score * 0.20
            + importance_score * 0.20
        )

        priority_score = round(
            max(0.0, min(100.0, priority_score)),
            2,
        )

        if priority_score >= 75:
            priority = "PRIORITY 1"
        elif priority_score >= 50:
            priority = "PRIORITY 2"
        else:
            priority = "PRIORITY 3"

        if nearest_probability >= 80 or priority_score >= 85:
            alert_level = "CRITICAL"
        elif nearest_probability >= 60 or priority_score >= 70:
            alert_level = "HIGH"
        elif nearest_probability >= 40 or priority_score >= 50:
            alert_level = "MODERATE"
        else:
            alert_level = "LOW"

        results.append(
            {
                "Village": row.get("village", "Unknown"),
                "State": row.get("state", "Unknown"),
                "Latitude": village_lat,
                "Longitude": village_lon,
                "Population": int(population),
                "AI Risk (%)": round(nearest_probability, 2),
                "Risk Level": nearest_risk_level,
                "Distance to Risk Zone (km)": (
                    round(nearest_distance, 2)
                    if nearest_distance is not None
                    else None
                ),
                "Road Connectivity": row.get(
                    "road_connectivity", "Unknown"
                ),
                "Importance": row.get(
                    "importance", "Unknown"
                ),
                "Priority": priority,
                "Priority Score": priority_score,
                "Alert": alert_level,
                "Recommended Action": get_recommended_action(
                    alert_level
                ),
                "Nearest Hospital": row.get(
                    "nearest_hospital", "Unknown"
                ),
            }
        )

    return pd.DataFrame(results)


village_results_df = calculate_village_priorities(
    risk_df,
    village_df,
)


def render_live_summary(page_name, title, message, stats, status="LIVE • UPDATING"):
    """Show a compact live operational summary at the top of every module."""
    updated_at = datetime.now().strftime("%d %b %Y • %I:%M:%S %p")
    stats_html = "".join(
        f"<div class=\"live-summary-stat\"><div class=\"live-summary-stat-label\">{label}</div>"
        f"<div class=\"live-summary-stat-value\">{value}</div>"
        f"<div class=\"live-summary-stat-note\">{note}</div></div>"
        for label, value, note in stats[:4]
    )
    st.markdown(
        f"""
        <div class=\"live-summary\">
            <div class=\"live-summary-head\">
                <div>
                    <div class=\"live-summary-kicker\">LIVE SITUATION SUMMARY • {page_name.upper()}</div>
                    <div class=\"live-summary-title\">{title}</div>
                    <div class=\"live-summary-text\">{message}</div>
                </div>
                <div class=\"live-summary-status\"><span class=\"live-summary-dot\"></span>{status}</div>
            </div>
            <div class=\"live-summary-grid\">{stats_html}</div>
            <div class=\"live-summary-update\">Last refreshed: {updated_at} • Values update when the dashboard reruns or you use Refresh in the sidebar.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# INCIDENT VERIFICATION + PREDICTION HELPERS
# ============================================================

def nearest_risk_probability(latitude, longitude):
    """Return the AI risk of the nearest configured risk point."""
    if risk_df.empty:
        return live_probability
    best_probability = live_probability
    best_distance = None
    for _, row in risk_df.iterrows():
        point_lat = safe_float(row.get("latitude"))
        point_lon = safe_float(row.get("longitude"))
        distance = calculate_distance(latitude, longitude, point_lat, point_lon)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_probability = safe_float(
                row.get("probability", row.get("risk", live_probability)),
                live_probability,
            )
    return round(max(0.0, min(100.0, best_probability)), 2)


def verify_incident_evidence(description, severity, latitude, longitude, camera_present):
    """Evidence-assisted triage for the prototype, not a production vision model."""
    nearby_risk = nearest_risk_probability(latitude, longitude)
    score = 35 if camera_present else 0
    score += {"Low": 5, "Moderate": 12, "High": 20, "Critical": 25}.get(severity, 5)
    text = (description or "").lower()
    visual_cues = ["crack", "debris", "mud", "soil", "rock", "slope", "landslide", "slide", "collapse", "fallen", "blocked", "road", "earth"]
    score += min(20, sum(4 for cue in visual_cues if cue in text))
    score += min(20, nearby_risk * 0.20)
    confidence = round(min(99.0, score), 1)
    if not camera_present:
        status = "UNVERIFIED — CAMERA CHECK REQUIRED"
    elif confidence >= 70:
        status = "LIKELY TRUE INCIDENT — RESPONSE RECOMMENDED"
    elif confidence >= 50:
        status = "REVIEW REQUIRED — POSSIBLE INCIDENT"
    else:
        status = "LOW EVIDENCE — POSSIBLE FALSE ALARM"
    return status, confidence, nearby_risk


def predicted_landslide_rows(limit=5):
    """Rank locations and show a prototype estimated warning window."""
    if village_results_df.empty:
        return []
    ranked = village_results_df.sort_values(["AI Risk (%)", "Priority Score"], ascending=False).head(limit)
    rows = []
    now = datetime.now()
    for _, row in ranked.iterrows():
        risk = safe_float(row.get("AI Risk (%)"))
        level = str(row.get("Alert", row.get("Risk Level", "LOW")))
        hours = {"CRITICAL": 2, "HIGH": 6, "MODERATE": 12, "LOW": 24}.get(level, 24)
        predicted_at = now + timedelta(hours=hours)
        rows.append({
            "Location": f"{row.get('Village', 'Unknown')}, {row.get('State', 'Unknown')}",
            "Risk": risk,
            "Level": level,
            "Predicted Time": predicted_at.strftime("%d %b %Y • %I:%M %p"),
        })
    return rows


# ============================================================
# MODULE NAVIGATION METADATA
# ============================================================

MODULE_INFO = {
    "Dashboard": {"icon":"🏠", "tagline":"Command center for the complete NER landslide situation.", "purpose":"Combines AI risk, weather, sensors, communities and alerts in one operational view.", "data":"AI probability, environmental indicators, village priority and active warning status."},
    "Risk Map": {"icon":"🗺️", "tagline":"GIS-based spatial view of hazards and exposed locations.", "purpose":"Locate vulnerable communities, risk zones, roads, infrastructure and field incidents.", "data":"Latitude/longitude, AI risk, road risk, infrastructure and geo-tagged reports."},
    "Alerts": {"icon":"🚨", "tagline":"Early-warning center for prioritizing locations that need attention.", "purpose":"Turn AI predictions into understandable warning levels and recommended actions.", "data":"Risk probability, response priority, population exposure, connectivity and hospital access."},
    "Predicted Landslide Risk": {"icon":"🔮", "tagline":"Dedicated forecast view for locations with elevated landslide risk.", "purpose":"Present AI-ranked locations, risk levels and estimated warning windows in one focused section.", "data":"Predicted location, AI risk probability, warning level and prototype estimated date/time."},
    "Early Alert Systems": {"icon":"📢", "tagline":"Broadcast warnings for predicted disaster conditions.", "purpose":"Turn existing AI risk predictions into clear, time-aware warning messages for monitoring and response teams.", "data":"Predicted location, risk level, estimated warning window and recommended response channels."},
    "Sensors": {"icon":"📡", "tagline":"Monitor environmental signals that influence landslide risk.", "purpose":"Inspect rainfall, soil moisture, slope, movement and elevation inputs used by the AI engine.", "data":"Prototype sensor values with live-style refresh and AI scenario testing."},
    "Analytics": {"icon":"📊", "tagline":"Explore risk patterns and response priorities across communities.", "purpose":"Compare AI risk, priority scores and warning distribution to support decisions.", "data":"Village-level risk, priority, population, alert level and regional breakdowns."},
    "Incident Reporting": {"icon":"📸", "tagline":"Capture field observations with location and evidence.", "purpose":"Create a geo-tagged incident record that can appear on the GIS map and support response.", "data":"Coordinates, severity, road status, village, description and optional photo."},
    "Reports": {"icon":"📄", "tagline":"Generate decision-ready monitoring summaries.", "purpose":"Review, filter and export early-warning information for teams and presentations.", "data":"Risk, alert, priority, population, recommended action and monitoring statistics."},
    "Settings": {"icon":"⚙️", "tagline":"Configure prototype monitoring and notification behavior.", "purpose":"Control alert channels, simulation settings and AI-assisted priority configuration.", "data":"Local prototype settings; production deployment would connect these to secure services."},
}

def render_module_info(page_name, compact=False):
    info = MODULE_INFO[page_name]
    if compact:
        st.caption(f"{info['icon']} {info['tagline']}")
        return
    st.markdown(
        f"""<div class=\"glass module-intro\">
        <div style=\"font-size:.75rem;color:#63c8ff;font-weight:800;letter-spacing:.12em;text-transform:uppercase;\">ACTIVE MODULE</div>
        <div style=\"font-size:1.4rem;font-weight:800;margin:4px 0;\">{info['icon']} {page_name}</div>
        <div style=\"color:#dce8f3;margin-bottom:10px;\">{info['tagline']}</div>
        <div style=\"display:grid;grid-template-columns:1fr 1fr;gap:10px;\">
          <div style=\"padding:10px;border-radius:10px;background:rgba(255,255,255,.035);\"><b>Purpose</b><br><span style=\"color:#9fb1c4;font-size:.86rem;\">{info['purpose']}</span></div>
          <div style=\"padding:10px;border-radius:10px;background:rgba(255,255,255,.035);\"><b>Information shown</b><br><span style=\"color:#9fb1c4;font-size:.86rem;\">{info['data']}</span></div>
        </div></div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# SIDEBAR
# ============================================================

# Persistent controls used across the application.
# Quick-action buttons use a separate pending target so they never
# directly mutate a Streamlit widget key after that widget is created.
if "navigation" not in st.session_state:
    st.session_state.navigation = "Dashboard"
if "_pending_navigation" in st.session_state:
    st.session_state.navigation = st.session_state.pop("_pending_navigation")

# Recover safely if an older app version left an invalid navigation value.
# This prevents KeyError/invalid widget state after replacing app.py.
if st.session_state.navigation not in MODULE_INFO:
    st.session_state.navigation = "Dashboard"

if "selected_region" not in st.session_state:
    st.session_state.selected_region = "All NER"
if "sidebar_risk_threshold" not in st.session_state:
    st.session_state.sidebar_risk_threshold = 60
if "live_monitoring" not in st.session_state:
    st.session_state.live_monitoring = True
if "compact_mode" not in st.session_state:
    st.session_state.compact_mode = False
if "demo_role" not in st.session_state:
    st.session_state.demo_role = "Public Viewer"
if "private_access" not in st.session_state:
    st.session_state.private_access = None
if "private_login_target" not in st.session_state:
    st.session_state.private_login_target = None
if "private_login_nonce" not in st.session_state:
    st.session_state.private_login_nonce = 0

# Enhanced sidebar styling — keeps the original dark/glass visual language.
st.markdown(
    """
    <style>
    /* Sidebar has its own viewport and scroll position. */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(2,12,25,.99), rgba(3,18,34,.98));
        border-right: 1px solid rgba(110,180,235,.22);
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        scrollbar-width: thin;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        min-height: 100%;
    }
    /* Main display gets its own independent scrollbar. */
    [data-testid="stAppViewContainer"] {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
    }
    [data-testid="stAppViewContainer"] > .main .block-container {
        min-height: 0 !important;
        height: auto !important;
        padding-bottom: 5rem !important;
    }
    .sidebar-brand {
        padding: 14px 8px 18px 8px;
        border-bottom: 1px solid rgba(150,200,240,.16);
        margin-bottom: 14px;
    }
    .sidebar-brand h2 { margin:0; font-size:1.35rem; }
    .sidebar-brand p { margin:5px 0 0 0; color:#91abc1; font-size:.78rem; }
    .sidebar-section {
        color:#7fa7c8; font-size:.72rem; font-weight:800;
        letter-spacing:.12em; text-transform:uppercase;
        margin:15px 0 7px 0;
    }
    .status-card {
        padding:9px 11px; margin:5px 0; border-radius:10px;
        background:rgba(13,35,57,.72); border:1px solid rgba(120,180,230,.13);
        font-size:.78rem;
    }
    .module-intro { margin-bottom: 16px; }
    section[data-testid="stSidebar"] .stRadio > div { gap: 6px; }
    section[data-testid="stSidebar"] .stRadio label { border:1px solid transparent; transition:.2s ease; background:rgba(255,255,255,.018); }
    section[data-testid="stSidebar"] .stRadio label:hover { border-color:rgba(95,199,255,.35); background:rgba(50,120,170,.14); transform:translateX(2px); }

    /* ==========================================================
       RESTORE ORIGINAL STREAMLIT PAGE SCROLL
       Main content and sidebar return to the normal Streamlit/browser
       scrolling behavior used before the independent-scroll change.
       ========================================================== */
    html, body, .stApp {
        height: auto !important;
        min-height: 100% !important;
        overflow-x: hidden !important;
        overflow-y: auto !important;
    }

    [data-testid="stAppViewContainer"] {
        height: auto !important;
        min-height: 100vh !important;
        max-height: none !important;
        overflow: visible !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        height: auto !important;
        min-height: 100vh !important;
        max-height: none !important;
        overflow: visible !important;
        overscroll-behavior: auto !important;
    }

    [data-testid="stAppViewContainer"] > .main > div,
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"] > .main .block-container {
        height: auto !important;
        min-height: 0 !important;
        max-height: none !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] {
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] > div:first-child {
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        min-height: 0 !important;
    }

    /* Keep the decorative layers fixed without creating a second scroll area. */
    .stApp:has(.section-marker)::before {
        position: fixed !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        pointer-events: none !important;
    }

    .dashboard-image-bg {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        height: 650px !important;
        max-height: 650px !important;
        pointer-events: none !important;
    }

    /* ==========================================================
       DEMO / EVALUATION ACCESS PANEL
       ========================================================== */
    .demo-access-panel {
        margin: 0 0 22px 0; padding: 20px; border-radius: 20px;
        border: 1px solid rgba(88, 205, 255, .28);
        background: linear-gradient(135deg, rgba(7,25,45,.92), rgba(11,31,52,.78));
        box-shadow: 0 16px 42px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.06);
        position: relative; overflow: hidden;
    }
    .demo-access-panel::before {
        content: ""; position:absolute; inset:0; pointer-events:none;
        background: radial-gradient(circle at 8% 0%, rgba(46,211,255,.14), transparent 34%),
                    radial-gradient(circle at 95% 100%, rgba(142,84,255,.12), transparent 32%);
    }
    .demo-access-kicker {
        color:#6edcff; font-size:.70rem; font-weight:900; letter-spacing:.13em;
        text-transform:uppercase; margin-bottom:5px; position:relative;
    }
    .demo-access-title {
        color:#f5fbff; font-size:1.28rem; font-weight:900; margin-bottom:4px; position:relative;
    }
    .demo-access-copy {
        color:#a9bfd0; font-size:.84rem; line-height:1.5; position:relative;
    }
    .demo-role-card {
        padding:14px 15px; border-radius:15px; min-height:126px;
        border:1px solid rgba(255,255,255,.09);
        background:rgba(255,255,255,.035); position:relative;
        transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    }
    .demo-role-card:hover { transform:translateY(-2px); border-color:rgba(89,207,255,.38); box-shadow:0 12px 28px rgba(0,0,0,.18); }
    .demo-role-icon { font-size:1.45rem; margin-bottom:4px; }
    .demo-role-name { color:#f4f8ff; font-weight:850; font-size:.92rem; }
    .demo-role-desc { color:#94acc0; font-size:.72rem; line-height:1.4; margin-top:3px; }
    .demo-public-strip {
        margin-top:12px; padding:11px 13px; border-radius:13px;
        background:rgba(52,211,153,.06); border:1px solid rgba(52,211,153,.20);
        color:#bcefdc; font-size:.76rem;
    }
    .demo-active-badge {
        display:inline-block; margin-top:9px; padding:4px 9px; border-radius:999px;
        background:rgba(56,217,255,.10); border:1px solid rgba(56,217,255,.22);
        color:#8fe6ff; font-size:.67rem; font-weight:800;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """<div class="sidebar-brand">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#1d8cff,#45d7b1);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 22px rgba(29,140,255,.25);">
                <svg width="25" height="25" viewBox="0 0 64 64" aria-hidden="true">
                    <path d="M5 50 L24 20 L35 34 L43 25 L59 50 Z" fill="#ffffff" opacity=".95"/>
                    <path d="M5 50 Q20 44 32 50 T59 50 V57 H5 Z" fill="#153d67"/>
                    <path d="M24 20 L19 28 L27 27 L31 34 L35 34 Z" fill="#bfe8ff"/>
                </svg>
            </div>
            <div>
                <h2 style="margin:0;">NER Landslide AI</h2>
                <p style="margin:2px 0 0 0;">Real-Time Disaster Intelligence</p>
            </div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Sidebar web search with live autocomplete suggestions
# ------------------------------------------------------------
# The search field is rendered as a small HTML component so suggestions can
# update on every keystroke, just like a modern search engine.
sidebar_search_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #f7fbff;
}
.search-wrap {
    position: relative;
    width: 100%;
}
.search-label {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .03em;
    margin: 0 0 6px 2px;
    color: #dcecff;
}
.search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-height: 42px;
    padding: 0 10px;
    border: 1px solid rgba(110, 205, 255, .48);
    border-radius: 12px;
    background: rgba(3, 13, 25, .92);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 0 18px rgba(30,160,255,.08);
}
.search-box:focus-within {
    border-color: #38d9ff;
    box-shadow: 0 0 0 2px rgba(56,217,255,.12), 0 0 22px rgba(56,217,255,.16);
}
.search-icon { font-size: 16px; opacity: .9; }
#query {
    flex: 1;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    color: #f7fbff;
    font-size: 13px;
    font-weight: 600;
}
#query::placeholder { color: #7891a7; }
.clear-btn {
    display: none;
    border: 0;
    background: transparent;
    color: #91abc1;
    cursor: pointer;
    font-size: 15px;
    padding: 2px 3px;
}
.suggestions {
    position: absolute;
    z-index: 9999;
    top: 69px;
    left: 0;
    right: 0;
    overflow: hidden;
    border: 1px solid rgba(93, 190, 244, .30);
    border-radius: 11px;
    background: rgba(7, 20, 34, .985);
    box-shadow: 0 14px 30px rgba(0,0,0,.42), 0 0 18px rgba(30,160,255,.08);
    display: none;
}
.suggestion {
    display: flex;
    align-items: center;
    gap: 9px;
    width: 100%;
    padding: 9px 11px;
    border: 0;
    border-bottom: 1px solid rgba(255,255,255,.045);
    background: transparent;
    color: #eaf5ff;
    text-align: left;
    cursor: pointer;
    font-size: 12px;
}
.suggestion:last-child { border-bottom: 0; }
.suggestion:hover, .suggestion.active { background: rgba(56,217,255,.10); }
.suggestion-icon { color: #5fdcff; font-size: 13px; }
.suggestion-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.status {
    min-height: 16px;
    padding: 5px 2px 0;
    color: #7f9bb1;
    font-size: 10px;
}
.engine-row {
    display: flex;
    gap: 6px;
    margin-top: 3px;
}
.engine {
    flex: 1;
    border: 1px solid rgba(110,180,230,.18);
    border-radius: 8px;
    padding: 5px 6px;
    background: rgba(255,255,255,.025);
    color: #9eb5c9;
    cursor: pointer;
    font-size: 10px;
    font-weight: 700;
}
.engine.active {
    border-color: rgba(56,217,255,.55);
    background: rgba(56,217,255,.10);
    color: #effcff;
}
.hint { margin-top: 4px; color: #718ca2; font-size: 9px; }
</style>
</head>
<body>
<div class="search-wrap">
    <div class="search-label">🔎 Search the web</div>
    <div class="search-box">
        <span class="search-icon">⌕</span>
        <input id="query" autocomplete="off" spellcheck="false" placeholder="Search anything…">
        <button id="clear" class="clear-btn" type="button">✕</button>
    </div>
    <div id="suggestions" class="suggestions"></div>
    <div id="status" class="status">Start typing to see suggestions</div>
    <div class="engine-row">
        <button id="google" class="engine active" type="button">Google</button>
        <button id="bing" class="engine" type="button">Bing</button>
    </div>
    <div class="hint">↑ ↓ to navigate • Enter to search</div>
</div>
<script>
const input = document.getElementById('query');
const list = document.getElementById('suggestions');
const status = document.getElementById('status');
const clearBtn = document.getElementById('clear');
const googleBtn = document.getElementById('google');
const bingBtn = document.getElementById('bing');
let engine = 'google';
let activeIndex = -1;
let timer = null;
let lastRequest = 0;

const fallbackSuggestions = [
  'India', 'India landslide', 'India weather today', 'India rainfall',
  'Northeast India landslide', 'Northeast India weather', 'landslide early warning system',
  'landslide risk map', 'landslide prediction AI', 'rainfall landslide risk',
  'soil moisture monitoring', 'GIS risk mapping', 'earthquake risk India',
  'Assam landslide', 'Arunachal Pradesh landslide', 'Manipur landslide',
  'Meghalaya landslide', 'Mizoram landslide', 'Nagaland landslide', 'Sikkim landslide',
  'Tripura landslide', 'road safety India', 'disaster management India'
];

function showSuggestions(items) {
    const clean = [...new Set(items)].filter(Boolean).slice(0, 7);
    list.innerHTML = '';
    activeIndex = -1;
    if (!input.value.trim() || !clean.length) {
        list.style.display = 'none';
        status.textContent = input.value.trim() ? 'No suggestions found' : 'Start typing to see suggestions';
        return;
    }
    clean.forEach((item, index) => {
        const row = document.createElement('button');
        row.type = 'button';
        row.className = 'suggestion';
        row.innerHTML = '<span class="suggestion-icon">⌕</span><span class="suggestion-text"></span>';
        row.querySelector('.suggestion-text').textContent = item;
        row.addEventListener('mousedown', (event) => {
            event.preventDefault();
            input.value = item;
            openSearch(item);
        });
        list.appendChild(row);
    });
    list.style.display = 'block';
    status.textContent = 'Suggestions';
}

function openSearch(term) {
    const q = (term || input.value).trim();
    if (!q) return;
    const encoded = encodeURIComponent(q);
    const url = engine === 'google'
        ? 'https://www.google.com/search?q=' + encoded
        : 'https://www.bing.com/search?q=' + encoded;
    window.open(url, '_blank', 'noopener,noreferrer');
    list.style.display = 'none';
}

async function fetchSuggestions(value) {
    const q = value.trim();
    if (!q) { showSuggestions([]); return; }
    const requestId = ++lastRequest;
    status.textContent = 'Getting suggestions…';
    try {
        const url = 'https://suggestqueries.google.com/complete/search?client=firefox&q=' + encodeURIComponent(q);
        const response = await fetch(url, { method: 'GET' });
        if (!response.ok) throw new Error('suggestion request failed');
        const data = await response.json();
        if (requestId !== lastRequest) return;
        const remote = Array.isArray(data) && Array.isArray(data[1]) ? data[1] : [];
        const local = fallbackSuggestions.filter(item => item.toLowerCase().includes(q.toLowerCase()));
        showSuggestions([...remote, ...local]);
    } catch (error) {
        if (requestId !== lastRequest) return;
        const local = fallbackSuggestions.filter(item => item.toLowerCase().includes(q.toLowerCase()));
        showSuggestions(local);
    }
}

input.addEventListener('input', () => {
    clearBtn.style.display = input.value ? 'block' : 'none';
    clearTimeout(timer);
    timer = setTimeout(() => fetchSuggestions(input.value), 120);
});
input.addEventListener('keydown', (event) => {
    const rows = [...list.querySelectorAll('.suggestion')];
    if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (!rows.length) return;
        activeIndex = Math.min(activeIndex + 1, rows.length - 1);
        rows.forEach((row, i) => row.classList.toggle('active', i === activeIndex));
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (!rows.length) return;
        activeIndex = Math.max(activeIndex - 1, 0);
        rows.forEach((row, i) => row.classList.toggle('active', i === activeIndex));
    } else if (event.key === 'Enter') {
        event.preventDefault();
        const chosen = activeIndex >= 0 && rows[activeIndex]
            ? rows[activeIndex].querySelector('.suggestion-text').textContent
            : input.value;
        openSearch(chosen);
    } else if (event.key === 'Escape') {
        list.style.display = 'none';
    }
});

clearBtn.addEventListener('click', () => {
    input.value = '';
    clearBtn.style.display = 'none';
    showSuggestions([]);
    input.focus();
});

googleBtn.addEventListener('click', () => {
    engine = 'google';
    googleBtn.classList.add('active');
    bingBtn.classList.remove('active');
});
bingBtn.addEventListener('click', () => {
    engine = 'bing';
    bingBtn.classList.add('active');
    googleBtn.classList.remove('active');
});

document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-wrap')) list.style.display = 'none';
});
</script>
</body>
</html>
"""

with st.sidebar:
    components.html(sidebar_search_html, height=245, scrolling=False)

# ------------------------------------------------------------
# Demo / Evaluation Access — sidebar quick login
# ------------------------------------------------------------
st.sidebar.markdown(
    """<div class="sidebar-demo-card">
        <div class="sidebar-demo-kicker">● DEMO / EVALUATION</div>
        <div class="sidebar-demo-title">Quick role access</div>
        <div class="sidebar-demo-copy">One-click routes for judges to explore the operational views.</div>
    </div>""",
    unsafe_allow_html=True,
)

_demo_col1, _demo_col2 = st.sidebar.columns(2)
with _demo_col1:
    if st.button("🏛️ NDMA Official", key="sidebar_demo_ndma", use_container_width=True):
        st.session_state.private_login_target = "NDMA Official"
        st.session_state.private_login_nonce += 1
        st.rerun()
with _demo_col2:
    if st.button("🧭 Field Geologist", key="sidebar_demo_geologist", use_container_width=True):
        st.session_state.private_login_target = "Field Geologist"
        st.session_state.private_login_nonce += 1
        st.rerun()

if st.sidebar.button("🗺️ Skip / View Public Map", key="sidebar_demo_public", use_container_width=True):
    st.session_state.demo_role = "Public Viewer"
    st.session_state.private_access = None
    st.session_state.private_login_target = None
    st.session_state._pending_navigation = "Risk Map"
    st.rerun()

# Alerts and Sensors are private operational areas. They are not exposed in public navigation.
if st.session_state.private_login_target:
    _login_role = st.session_state.private_login_target
    _login_module = "Alerts" if _login_role == "NDMA Official" else "Sensors"
    st.sidebar.markdown(
        f"""<div class="sidebar-demo-card" style="margin-top:10px;">
            <div class="sidebar-demo-kicker">🔒 PRIVATE ACCESS</div>
            <div class="sidebar-demo-title">{_login_role}</div>
            <div class="sidebar-demo-copy">Enter the evaluation password to unlock {_login_module}.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    _password_key = f"private_access_password_{_login_role.lower().replace(' ', '_')}_{st.session_state.private_login_nonce}"
    _private_password = st.sidebar.text_input(
        "Private access password", type="password", key=_password_key,
        placeholder="Enter password", label_visibility="collapsed",
    )
    _login_col1, _login_col2 = st.sidebar.columns(2)
    with _login_col1:
        if st.button("🔓 Unlock", key="private_unlock_btn", use_container_width=True):
            _password_hash = hashlib.sha256(_private_password.encode("utf-8")).hexdigest()
            _expected_hash = hashlib.sha256("123456".encode("utf-8")).hexdigest()
            if _password_hash == _expected_hash:
                st.session_state.private_access = _login_role
                st.session_state.demo_role = _login_role
                st.session_state.private_login_target = None
                st.session_state._pending_navigation = _login_module
                st.rerun()
            else:
                st.sidebar.error("Incorrect password.")
    with _login_col2:
        if st.button("✕ Cancel", key="private_cancel_btn", use_container_width=True):
            st.session_state.private_login_target = None
            st.session_state.private_login_nonce += 1
            st.rerun()

_PUBLIC_NAV_OPTIONS = [name for name in MODULE_INFO if name not in {"Alerts", "Sensors"}]
if st.session_state.private_access == "NDMA Official":
    NAV_OPTIONS = _PUBLIC_NAV_OPTIONS + ["Alerts"]
elif st.session_state.private_access == "Field Geologist":
    NAV_OPTIONS = _PUBLIC_NAV_OPTIONS + ["Sensors"]
else:
    NAV_OPTIONS = _PUBLIC_NAV_OPTIONS

if st.session_state.navigation not in NAV_OPTIONS:
    st.session_state.navigation = "Risk Map" if "Risk Map" in NAV_OPTIONS else NAV_OPTIONS[0]

st.sidebar.caption(
    f"🔐 Access: {st.session_state.demo_role}" if st.session_state.private_access
    else "🌐 Public access — operational modules are locked"
)
if st.session_state.private_access:
    if st.sidebar.button("🔒 Lock private access", key="lock_private_access", use_container_width=True):
        st.session_state.private_access = None
        st.session_state.demo_role = "Public Viewer"
        st.session_state._pending_navigation = "Risk Map"
        st.rerun()

st.sidebar.markdown(f'<div class="sidebar-section">{t("Navigation")}</div>', unsafe_allow_html=True)
page = st.sidebar.radio(
    "Navigation", NAV_OPTIONS,
    format_func=lambda name: f"{MODULE_INFO[name]['icon']}  {t(name)}",
    key="navigation", label_visibility="collapsed",
)
_selected_info = MODULE_INFO[page]

# Reset the main page scroll position whenever the user switches modules.
# Streamlit reruns the script but normally preserves the browser's previous
# scroll position, so a small component asks the parent Streamlit page to
# return to the top after navigation changes.
_previous_page = st.session_state.get("_last_rendered_page")
_page_changed = _previous_page is not None and _previous_page != page
st.session_state._last_rendered_page = page
if _page_changed:
    components.html(
        """
        <script>
        (function() {
            function resetParentScroll() {
                try {
                    var parentDoc = window.parent.document;
                    var candidates = [
                        parentDoc.querySelector('[data-testid=\"stAppViewContainer\"] > .main'),
                        parentDoc.querySelector('[data-testid=\"stAppViewContainer\"]'),
                        parentDoc.scrollingElement,
                        parentDoc.documentElement,
                        parentDoc.body
                    ];
                    candidates.forEach(function(el) {
                        if (el) {
                            el.scrollTop = 0;
                            el.scrollTo && el.scrollTo({top: 0, left: 0, behavior: 'instant'});
                        }
                    });
                    window.parent.scrollTo(0, 0);
                } catch (e) {
                    try { window.scrollTo(0, 0); } catch (_) {}
                }
            }
            setTimeout(resetParentScroll, 20);
            setTimeout(resetParentScroll, 120);
            setTimeout(resetParentScroll, 300);
        })();
        </script>
        """,
        height=1,
        scrolling=False,
    )

# Dynamic sidebar theme — the sidebar follows the active module colour palette.
SIDEBAR_THEMES = {
    "Dashboard": {"main":"#22d3ee", "main2":"#3b82f6", "soft":"rgba(34,211,238,.16)", "bg1":"#061a2b", "bg2":"#071225"},
    "Risk Map": {"main":"#22c55e", "main2":"#00b894", "soft":"rgba(34,197,94,.16)", "bg1":"#061d18", "bg2":"#06151a"},
    "Alerts": {"main":"#ff4d6d", "main2":"#ff9f1c", "soft":"rgba(255,77,109,.17)", "bg1":"#241018", "bg2":"#17101a"},
    "Predicted Landslide Risk": {"main":"#f97316", "main2":"#ef4444", "soft":"rgba(249,115,22,.17)", "bg1":"#241208", "bg2":"#1b0d12"},
    "Early Alert Systems": {"main":"#facc15", "main2":"#f97316", "soft":"rgba(250,204,21,.17)", "bg1":"#241b08", "bg2":"#1b1010"},
    "Sensors": {"main":"#06b6d4", "main2":"#6366f1", "soft":"rgba(6,182,212,.16)", "bg1":"#061a25", "bg2":"#0b1022"},
    "Analytics": {"main":"#a855f7", "main2":"#ec4899", "soft":"rgba(168,85,247,.17)", "bg1":"#180d25", "bg2":"#180d1b"},
    "Incident Reporting": {"main":"#f59e0b", "main2":"#ef4444", "soft":"rgba(245,158,11,.17)", "bg1":"#21150a", "bg2":"#1d1016"},
    "Reports": {"main":"#14b8a6", "main2":"#3b82f6", "soft":"rgba(20,184,166,.17)", "bg1":"#061d1c", "bg2":"#071326"},
    "Settings": {"main":"#8b5cf6", "main2":"#d946ef", "soft":"rgba(139,92,246,.17)", "bg1":"#130d25", "bg2":"#1b0d20"},
}
_theme = SIDEBAR_THEMES[page]
st.sidebar.markdown(
    f"""
    <style>
    section[data-testid="stSidebar"] {{
        background:
            radial-gradient(circle at 15% 0%, {_theme['soft']} 0%, transparent 34%),
            radial-gradient(circle at 100% 70%, rgba(255,255,255,.025) 0%, transparent 30%),
            linear-gradient(180deg, {_theme['bg1']} 0%, {_theme['bg2']} 100%);
        border-right: 1px solid {_theme['main']}55;
        box-shadow: 8px 0 35px rgba(0,0,0,.20);
    }}
    section[data-testid="stSidebar"]::before {{
        content:""; display:block; height:4px; margin:-1rem -1rem 1rem -1rem;
        background:linear-gradient(90deg, {_theme['main']}, {_theme['main2']}, transparent);
        box-shadow:0 0 18px {_theme['main']}66;
    }}
    section[data-testid="stSidebar"] .sidebar-brand {{
        position:relative; overflow:hidden; padding:15px 12px 18px;
        border:1px solid {_theme['main']}35; border-radius:16px;
        background:linear-gradient(135deg, {_theme['soft']}, rgba(255,255,255,.025));
        box-shadow:0 10px 28px rgba(0,0,0,.20);
    }}
    section[data-testid="stSidebar"] .sidebar-brand::after {{
        content:""; position:absolute; width:90px; height:90px; right:-40px; top:-40px;
        border-radius:50%; border:1px solid {_theme['main']}28;
        box-shadow:0 0 0 14px {_theme['main']}10, 0 0 0 28px {_theme['main']}07;
    }}
    section[data-testid="stSidebar"] .sidebar-brand h2 {{ color:#f7fbff; }}
    section[data-testid="stSidebar"] .sidebar-brand p {{ color:#a9bfd0; }}
    section[data-testid="stSidebar"] .sidebar-brand > div > div:first-child {{
        background:linear-gradient(135deg, {_theme['main']}, {_theme['main2']}) !important;
        box-shadow:0 8px 24px {_theme['main']}40 !important;
    }}
    section[data-testid="stSidebar"] .sidebar-section {{
        color:{_theme['main']};
        text-shadow:0 0 12px {_theme['main']}35;
    }}
    section[data-testid="stSidebar"] .sidebar-search-card {{
        position:relative; overflow:hidden; margin:4px 0 8px; padding:13px 14px;
        border:1px solid {_theme['main']}45; border-radius:15px;
        background:linear-gradient(135deg, {_theme['soft']}, rgba(255,255,255,.035));
        box-shadow:0 10px 28px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.05);
    }}
    section[data-testid="stSidebar"] .sidebar-search-card::after {{
        content:""; position:absolute; width:70px; height:70px; right:-25px; top:-30px;
        border-radius:50%; border:1px solid {_theme['main']}30;
        box-shadow:0 0 0 10px {_theme['main']}0b, 0 0 0 20px {_theme['main']}06;
    }}
    section[data-testid="stSidebar"] .sidebar-search-title {{
        color:#f7fbff; font-weight:850; font-size:.92rem; letter-spacing:.01em;
    }}
    section[data-testid="stSidebar"] .sidebar-search-subtitle {{
        color:#9eb5c9; font-size:.69rem; line-height:1.35; margin-top:3px;
    }}
    section[data-testid="stSidebar"] .sidebar-search-button {{
        display:flex; align-items:center; justify-content:center; gap:8px;
        width:100%; box-sizing:border-box; margin:7px 0 2px; padding:9px 12px;
        border:1px solid {_theme['main']}70; border-radius:11px;
        color:#f8fbff !important; text-decoration:none !important; font-weight:800; font-size:.82rem;
        background:linear-gradient(135deg, {_theme['main']}32, {_theme['main2']}28);
        box-shadow:0 7px 20px rgba(0,0,0,.16), 0 0 14px {_theme['main']}14;
        transition:all .18s ease;
    }}
    section[data-testid="stSidebar"] .sidebar-search-button:hover {{
        transform:translateY(-1px); border-color:{_theme['main']};
        box-shadow:0 9px 24px rgba(0,0,0,.20), 0 0 20px {_theme['main']}2a;
        background:linear-gradient(135deg, {_theme['main']}48, {_theme['main2']}38);
    }}
    section[data-testid="stSidebar"] .sidebar-search-button .search-arrow {{
        margin-left:auto; font-size:1rem; opacity:.9;
    }}
    section[data-testid="stSidebar"] .stTextInput > div > div {{
        border:1px solid {_theme['main']}40 !important; border-radius:11px !important;
        background:rgba(3,13,25,.72) !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
    }}
    section[data-testid="stSidebar"] .stTextInput input {{
        color:#f5f8ff !important; font-weight:600;
    }}
    section[data-testid="stSidebar"] .stTextInput input::placeholder {{ color:#7f97aa !important; opacity:1; }}
    section[data-testid="stSidebar"] .stTextInput > div > div:focus-within {{
        border-color:{_theme['main']} !important; box-shadow:0 0 0 2px {_theme['main']}18, 0 0 16px {_theme['main']}18 !important;
    }}
    section[data-testid="stSidebar"] .stRadio label {{
        min-height:42px; padding:9px 11px !important; margin:2px 0;
        border:1px solid rgba(255,255,255,.055) !important;
        border-left:3px solid rgba(255,255,255,.12) !important;
        border-radius:12px !important;
        background:rgba(255,255,255,.025) !important;
        transition:all .18s ease;
    }}
    section[data-testid="stSidebar"] .stRadio label:hover {{
        transform:translateX(3px); background:{_theme['soft']} !important;
        border-color:{_theme['main']}55 !important; border-left-color:{_theme['main']} !important;
        box-shadow:0 6px 18px rgba(0,0,0,.16);
    }}
    section[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
        background:linear-gradient(90deg, {_theme['soft']}, rgba(255,255,255,.045)) !important;
        border-color:{_theme['main']}66 !important; border-left:4px solid {_theme['main']} !important;
        box-shadow:inset 0 0 22px {_theme['main']}0d, 0 7px 20px rgba(0,0,0,.18);
        font-weight:800;
    }}
    section[data-testid="stSidebar"] .stRadio label:has(input:checked) div[role="radio"] {{
        border-color:{_theme['main']} !important; background:{_theme['main']} !important;
        box-shadow:0 0 12px {_theme['main']}88;
    }}
    section[data-testid="stSidebar"] .prediction-note {{
        margin:4px 0 8px; padding:8px 10px; border-radius:10px;
        background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.07);
        color:#9eb5c9; font-size:.66rem; line-height:1.35;
    }}
    section[data-testid="stSidebar"] .prediction-card {{
        margin:6px 0; padding:9px 10px; border-radius:11px;
        background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.08);
        box-shadow:0 6px 16px rgba(0,0,0,.14);
    }}
    section[data-testid="stSidebar"] .prediction-top {{ display:flex; justify-content:space-between; gap:8px; color:#f5f8ff; font-size:.70rem; }}
    section[data-testid="stSidebar"] .prediction-top span {{ color:{_theme['main']}; font-weight:900; }}
    section[data-testid="stSidebar"] .prediction-level {{ margin-top:3px; font-size:.62rem; font-weight:900; letter-spacing:.04em; color:#ffd38a; }}
    section[data-testid="stSidebar"] .prediction-time {{ margin-top:3px; color:#a9bfd0; font-size:.63rem; }}
    section[data-testid="stSidebar"] .prediction-critical {{ border-left:3px solid #ef4444; }}
    section[data-testid="stSidebar"] .prediction-high {{ border-left:3px solid #f59e0b; }}
    section[data-testid="stSidebar"] .prediction-moderate {{ border-left:3px solid #eab308; }}
    section[data-testid="stSidebar"] .prediction-low {{ border-left:3px solid #22c55e; }}

    section[data-testid="stSidebar"] .sidebar-demo-card {{
        position:relative; overflow:hidden; margin:8px 0 9px; padding:12px 13px;
        border:1px solid {_theme['main']}55; border-radius:15px;
        background:linear-gradient(135deg, {_theme['soft']}, rgba(255,255,255,.025));
        box-shadow:0 9px 25px rgba(0,0,0,.17), inset 0 1px 0 rgba(255,255,255,.05);
    }}
    section[data-testid="stSidebar"] .sidebar-demo-card::after {{
        content:""; position:absolute; width:60px; height:60px; right:-25px; top:-24px;
        border-radius:50%; border:1px solid {_theme['main']}30;
        box-shadow:0 0 0 9px {_theme['main']}09;
    }}
    section[data-testid="stSidebar"] .sidebar-demo-kicker {{
        color:{_theme['main']}; font-size:.60rem; font-weight:900; letter-spacing:.12em;
    }}
    section[data-testid="stSidebar"] .sidebar-demo-title {{
        color:#f7fbff; font-size:.88rem; font-weight:900; margin-top:2px;
    }}
    section[data-testid="stSidebar"] .sidebar-demo-copy {{
        color:#9eb5c9; font-size:.65rem; line-height:1.35; margin-top:3px;
    }}

    section[data-testid="stSidebar"] .status-card {{
        background:linear-gradient(135deg, {_theme['soft']}, rgba(255,255,255,.025));
        border:1px solid {_theme['main']}55 !important;
        border-left:4px solid {_theme['main']} !important;
        border-radius:13px; box-shadow:0 8px 22px rgba(0,0,0,.16);
    }}
    section[data-testid="stSidebar"] .status-card b {{ color:#f8fbff; }}
    section[data-testid="stSidebar"] .stButton > button {{
        border:1px solid {_theme['main']}45 !important;
        background:linear-gradient(135deg, {_theme['soft']}, rgba(255,255,255,.035)) !important;
        box-shadow:0 6px 18px rgba(0,0,0,.14);
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        border-color:{_theme['main']} !important;
        background:linear-gradient(135deg, {_theme['main']}28, {_theme['main2']}18) !important;
        box-shadow:0 0 18px {_theme['main']}25; transform:translateY(-1px);
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="slider"] {{
        border-color:{_theme['main']}35 !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background:rgba(255,255,255,.045) !important;
        border-radius:10px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{
        background:{_theme['main']} !important; border-color:{_theme['main']} !important;
        box-shadow:0 0 10px {_theme['main']}66;
    }}
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
    section[data-testid="stSidebar"] [data-testid="stToggle"] label {{ color:#dce8f2 !important; }}
    section[data-testid="stSidebar"] [data-testid="stCheckbox"] input:checked + div,
    section[data-testid="stSidebar"] [data-testid="stToggle"] input:checked + div {{ background:{_theme['main']} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    f"""<div class="status-card" style="margin-top:8px;border-color:rgba(95,199,255,.28);"><b>{_selected_info['icon']} {page}</b><br><span style="color:#91abc1;font-size:.72rem;">{_selected_info['tagline']}</span></div>""",
    unsafe_allow_html=True,
)
# Page theme marker used by the CSS above. It lets the active module
# control card, button and input accents without changing functionality.
st.markdown(f'<div class="page-theme page-theme-{page.lower().replace(" ", "-")}" style="display:none;"></div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-section">Quick Actions</div>', unsafe_allow_html=True)
q1, q2 = st.sidebar.columns(2)
with q1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with q2:
    if st.button("🚨 Alerts", use_container_width=True):
        if st.session_state.private_access == "NDMA Official":
            st.session_state._pending_navigation = "Alerts"
        else:
            st.session_state.private_login_target = "NDMA Official"
        st.rerun()

st.sidebar.markdown('<div class="sidebar-section">Monitoring Controls</div>', unsafe_allow_html=True)
st.session_state.selected_region = st.sidebar.selectbox(
    "Monitoring region",
    ["All NER", "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"],
    index=["All NER", "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"].index(st.session_state.selected_region),
    label_visibility="visible",
)
st.session_state.sidebar_risk_threshold = st.sidebar.slider(
    "Alert threshold", 40, 90, int(st.session_state.sidebar_risk_threshold), 5,
)
st.session_state.live_monitoring = st.sidebar.toggle(
    "🟢 Live monitoring", value=st.session_state.live_monitoring
)
st.session_state.compact_mode = st.sidebar.toggle(
    "📐 Compact dashboard", value=st.session_state.compact_mode
)

st.sidebar.markdown('<div class="sidebar-section">System Status</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="status-card">🤖 AI Model &nbsp; <b>{"ONLINE" if model is not None else "FALLBACK"}</b></div>'
    f'<div class="status-card">🌦️ Weather &nbsp; <b>CONNECTED</b></div>'
    f'<div class="status-card">📡 Sensor Channels &nbsp; <b>5 ACTIVE</b></div>'
    f'<div class="status-card">🏘️ Communities &nbsp; <b>{len(village_df)}</b></div>',
    unsafe_allow_html=True,
)

sidebar_risk_level = get_risk_level(live_probability)
st.sidebar.markdown('<div class="sidebar-section">Current AI Risk</div>', unsafe_allow_html=True)
st.sidebar.metric("AI probability", f"{live_probability:.1f}%", sidebar_risk_level)
st.sidebar.caption(f"Alert threshold: {st.session_state.sidebar_risk_threshold}%")

# ============================================================

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.markdown('<div class="dashboard-image-bg"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-marker dashboard"></div><div class="section-accent dashboard"></div>', unsafe_allow_html=True)

    # PREMIUM DASHBOARD HEADER — native Streamlit components
    # (avoids raw HTML rendering issues across Streamlit versions)
    h1, h2 = st.columns([3.4, 1.35])

    with h1:
        st.markdown(
            '<div class="dashboard-kicker">● &nbsp; AI EARLY WARNING &nbsp;•&nbsp; LIVE MONITORING</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "# NER Landslide Early Warning",
        )
        st.markdown(
            "AI-powered disaster intelligence for rainfall, soil moisture, terrain, "
            "ground movement, communities, roads and critical infrastructure."
        )

    with h2:
        st.markdown(
            "**SYSTEM STATUS**\n\n"
            "🟢 Monitoring System Active  \n"
            "🟢 AI Risk Engine Online  \n"
            "🟢 GIS Monitoring Ready",
        )

    st.markdown(
        '<div class="dashboard-feature-row">'
        '<span>📡 Real-Time Monitoring</span>'
        '<span>🤖 AI Risk Prediction</span>'
        '<span>🗺️ GIS Risk Mapping</span>'
        '<span>🚨 Early Warning</span>'
        '<span>🏘️ Community Protection</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # LIVE SITUATION SUMMARY
    if not village_results_df.empty:
        _dash_critical = int((village_results_df["Alert"] == "CRITICAL").sum())
        _dash_high = int((village_results_df["Alert"] == "HIGH").sum())
        _dash_avg = float(village_results_df["AI Risk (%)"].mean())
        render_live_summary(
            "Dashboard",
            "The system is continuously assessing landslide conditions.",
            f"AI risk is currently averaging {_dash_avg:.1f}% across {len(village_results_df)} monitored communities. {_dash_critical} critical and {_dash_high} high-priority warning conditions are currently detected. Use the modules below to investigate, respond and document incidents.",
            [("AI risk", f"{live_probability:.1f}%", live_risk_level), ("Critical", _dash_critical, "communities"), ("High", _dash_high, "communities"), ("Monitoring", "ACTIVE" if st.session_state.live_monitoring else "PAUSED", "live mode")],
            "LIVE • MONITORING" if st.session_state.live_monitoring else "PAUSED • MANUAL REFRESH",
        )

    # FILTER BAR
    filter_box = st.container()
    with filter_box:
        f1, f2, f3 = st.columns([1.2, 1.2, .75])
        states = ["All Regions"]
        if not village_df.empty and "state" in village_df.columns:
            states += sorted(village_df["state"].dropna().astype(str).unique().tolist())

        with f1:
            selected_state = st.selectbox("📍 Monitoring Region", states, key="dashboard_state")
        with f2:
            selected_risk = st.selectbox("🚦 Risk Filter", ["All Risks", "CRITICAL", "HIGH", "MODERATE", "LOW"], key="dashboard_risk")
        with f3:
            st.write("")
            if st.button("🔄 Refresh Live Data", use_container_width=True, type="primary"):
                refresh_live_sensor_values()
                st.rerun()

    # Filter village results
    dashboard_df = village_results_df.copy()
    if selected_state != "All Regions" and not dashboard_df.empty and "State" in dashboard_df.columns:
        dashboard_df = dashboard_df[dashboard_df["State"] == selected_state]
    if selected_risk != "All Risks" and not dashboard_df.empty and "Alert" in dashboard_df.columns:
        dashboard_df = dashboard_df[dashboard_df["Alert"] == selected_risk]

    def count_alert(level):
        if dashboard_df.empty or "Alert" not in dashboard_df.columns:
            return 0
        return int((dashboard_df["Alert"] == level).sum())

    # TOP RISK CARDS
    critical_count = count_alert("CRITICAL")
    high_count = count_alert("HIGH")
    moderate_count = count_alert("MODERATE")
    low_count = count_alert("LOW")
    villages_count = len(dashboard_df) if not dashboard_df.empty else len(village_df)

    cards = st.columns(6)
    card_data = [
        ("🚨", "Critical", critical_count, "red"),
        ("⚠️", "High", high_count, "orange"),
        ("🟡", "Moderate", moderate_count, "yellow"),
        ("🟢", "Low", low_count, "green"),
        ("🏘️", "Villages Monitored", villages_count, "cyan"),
        ("📡", "Sensors Online", 5, "purple"),
    ]
    for col, (icon, label, value, cls) in zip(cards, card_data):
        with col:
            st.markdown(
                f'<div class="risk-card {cls}"><div class="label">{icon} {label}</div><div class="value">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # AI + WEATHER + SENSOR STATUS
    a, w, s = st.columns([1.55, 1, 1])

    with a:
        level_icon = {"CRITICAL":"🚨", "HIGH":"⚠️", "MODERATE":"🟡", "LOW":"🟢"}.get(live_risk_level, "ℹ️")
        st.markdown(
            f"""
            <div class="ai-panel">
                <div class="section-title">🤖 Real-Time AI Risk Engine <span class="pill">● Live</span></div>
                <div class="small-muted">Current landslide probability from live prototype sensor inputs</div>
                <div style="display:flex;align-items:center;gap:28px;margin-top:20px;">
                    <div>
                        <div class="ai-number">{live_probability:.0f}%</div>
                        <div class="small-muted">Landslide Probability</div>
                    </div>
                    <div style="flex:1;">
                        <div style="font-size:1.25rem;font-weight:800;">{level_icon} {live_risk_level} RISK</div>
                        <div class="small-muted" style="margin:8px 0 12px;">{risk_message(live_risk_level).replace('🚨 ', '').replace('⚠️ ', '').replace('🟡 ', '').replace('🟢 ', '')}</div>
                        <div style="height:13px;border-radius:999px;background:linear-gradient(90deg,#27c977,#d8df43,#ffb52e,#ff3b4e);position:relative;">
                            <div style="position:absolute;left:{max(1,min(99,live_probability))}%;top:-5px;width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 0 18px rgba(255,255,255,.85);transform:translateX(-50%);"></div>
                        </div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:22px;">
                    <div class="small-muted">🌧️<br><b style="color:white">{live_values['rainfall_mm']:.1f} mm</b><br>Rainfall</div>
                    <div class="small-muted">💧<br><b style="color:white">{live_values['soil_moisture']:.1f}%</b><br>Moisture</div>
                    <div class="small-muted">📐<br><b style="color:white">{live_values['slope_deg']:.1f}°</b><br>Slope</div>
                    <div class="small-muted">🌍<br><b style="color:white">{live_values['ground_movement_mm']:.1f} mm</b><br>Movement</div>
                    <div class="small-muted">⛰️<br><b style="color:white">{live_values['elevation_m']:.0f} m</b><br>Elevation</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with w:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌧️ Live Weather</div>', unsafe_allow_html=True)
        try:
            from services.weather import get_weather
            weather = get_weather(27.586, 91.859)
        except Exception:
            weather = None
        if weather:
            temp = weather.get("temperature", "N/A")
            rain = weather.get("rain", "N/A")
            precip = weather.get("precipitation", "N/A")
        else:
            temp, rain, precip = "N/A", "N/A", "N/A"
        st.markdown(f"<div class='small-muted'>Tawang, Arunachal Pradesh</div><div style='font-size:2.7rem;font-weight:800;margin:8px 0;'>☁️ {temp}°C</div><div style='color:#b9d8f0;'>Rainfall: {rain} mm</div><hr style='border-color:rgba(255,255,255,.08)'><div class='small-muted'>Precipitation</div><div style='font-size:1.25rem;font-weight:700;'>{precip} mm</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with s:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📡 Sensor Status</div>', unsafe_allow_html=True)
        sensor_rows = [
            ("Rainfall", f"{live_values['rainfall_mm']:.1f} mm"),
            ("Soil Moisture", f"{live_values['soil_moisture']:.1f}%"),
            ("Ground Movement", f"{live_values['ground_movement_mm']:.1f} mm"),
            ("Slope Angle", f"{live_values['slope_deg']:.1f}°"),
            ("Elevation", f"{live_values['elevation_m']:.0f} m"),
        ]
        for name, value in sensor_rows:
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.07);'><span>{name}</span><span><b>{value}</b> <span style='color:#39dc8b'>● Online</span></span></div>", unsafe_allow_html=True)
        st.markdown("<div style='color:#50e49a;margin-top:12px;font-size:.84rem;'>● All systems operational</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ANALYTICS ROW
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.25])

    with c1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Risk Distribution</div>', unsafe_allow_html=True)
        dist = pd.DataFrame({"Risk": ["Critical", "High", "Moderate", "Low"], "Count": [critical_count, high_count, moderate_count, low_count]})
        if dist["Count"].sum() == 0:
            dist["Count"] = [0, 0, 0, 1]
        fig = px.pie(dist, names="Risk", values="Count", hole=.58)
        fig.update_layout(height=235, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f1f8", showlegend=True, legend=dict(orientation="v"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏘️ Highest Risk Communities</div>', unsafe_allow_html=True)
        top = dashboard_df.copy()
        if not top.empty and "AI Risk (%)" in top.columns:
            top = top.sort_values("AI Risk (%)", ascending=False).head(5)
            for _, row in top.iterrows():
                name = str(row.get("Village", "Unknown"))
                risk = safe_float(row.get("AI Risk (%)", 0))
                st.markdown(f"<div style='margin:12px 0;'><div style='display:flex;justify-content:space-between;'><span>{name}</span><b>{risk:.0f}%</b></div><div style='height:9px;background:rgba(255,255,255,.08);border-radius:99px;margin-top:5px;'><div style='width:{min(100,risk)}%;height:100%;border-radius:99px;background:linear-gradient(90deg,#36c978,#ffc52f,#ff4053);'></div></div></div>", unsafe_allow_html=True)
        else:
            st.info("No community risk data available for this filter.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🚨 Live Alerts <span style="float:right;font-size:.8rem;color:#5fc7ff;">View All →</span></div>', unsafe_allow_html=True)
        alerts = dashboard_df.copy()
        if not alerts.empty and "AI Risk (%)" in alerts.columns:
            alerts = alerts.sort_values("AI Risk (%)", ascending=False).head(4)
            for _, row in alerts.iterrows():
                lvl = str(row.get("Alert", row.get("Risk Level", "LOW")))
                icon = {"CRITICAL":"🔴", "HIGH":"🟠", "MODERATE":"🟡", "LOW":"🟢"}.get(lvl,"🔵")
                st.markdown(f"<div class='alert-item'><b>{icon} {lvl}</b> — {row.get('Village','Unknown')}<br><span class='small-muted'>AI landslide probability {safe_float(row.get('AI Risk (%)',0)):.0f}%</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert-item'>🟢 No active alerts for the selected filters.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # MAP PREVIEW
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗺️ Risk Map Preview</div>', unsafe_allow_html=True)
    center = [27.5, 92.0]
    if not dashboard_df.empty and "Latitude" in dashboard_df.columns and "Longitude" in dashboard_df.columns:
        center = [safe_float(dashboard_df["Latitude"].mean()), safe_float(dashboard_df["Longitude"].mean())]
    m = folium.Map(location=center, zoom_start=6, tiles="OpenStreetMap", control_scale=True)
    if not dashboard_df.empty:
        for _, row in dashboard_df.iterrows():
            lat = safe_float(row.get("Latitude")); lon = safe_float(row.get("Longitude")); risk = safe_float(row.get("AI Risk (%)",0)); level = str(row.get("Alert", "LOW"))
            color = {"CRITICAL":"red", "HIGH":"orange", "MODERATE":"beige", "LOW":"green"}.get(level,"blue")
            folium.CircleMarker([lat,lon], radius=8, color=color, fill=True, fill_opacity=.75, popup=f"{row.get('Village','Unknown')}<br>Risk: {risk:.1f}%<br>Alert: {level}").add_to(m)
    st_folium(m, width=None, height=360, returned_objects=[])
    st.markdown('</div>', unsafe_allow_html=True)

    st.caption("Prototype decision-support dashboard. AI probability is for demonstration and is not an official evacuation order.")


# RISK MAP
# ============================================================

elif page == "Risk Map":
    st.markdown('<div class="section-marker riskmap"></div><div class="section-accent riskmap"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)
    _map_region = st.session_state.get("selected_region", "All NER")
    _map_df = village_results_df.copy()
    if _map_region != "All NER" and "State" in _map_df.columns:
        _map_df = _map_df[_map_df["State"].astype(str).str.strip() == _map_region]
    render_live_summary(
        "Risk Map",
        "The GIS view is tracking where risk and exposure are concentrated.",
        f"The map is currently scoped to {_map_region} and is ready to show AI risk zones, communities, roads, infrastructure and field incidents. {_map_df.shape[0]} communities are in the current geographic scope.",
        [("Map scope", _map_region, "selected region"), ("Communities", len(_map_df), "in scope"), ("AI risk", f"{live_probability:.1f}%", "current sensor estimate"), ("Risk layer", "READY", "GIS visualization")],
    )
    st.title(f"🗺️ {t('Risk Map')}")

    st.markdown(
        """
        Live-style GIS visualization combining AI landslide risk,
        vulnerable communities, road risk, critical infrastructure,
        and geo-tagged field incidents. The global sidebar controls
        filter the map automatically.
        """
    )

    # --------------------------------------------------------
    # MAP CONTROLS — MAIN PAGE
    # --------------------------------------------------------
    # These controls intentionally live on the Risk Map page instead of the
    # global sidebar so users can configure the map while looking at it.
    st.markdown("""
    <div class="glass map-controls-panel">
        <div class="section-title">🗺️ Map Controls</div>
        <div class="map-controls-subtitle">Choose which live GIS layers and labels are visible on the map.</div>
    </div>
    """, unsafe_allow_html=True)

    control_cols = st.columns(4, gap="medium")

    with control_cols[0]:
        show_risk = st.checkbox("🔴 AI Risk Zones", True, key="map_show_risk")
        show_roads = st.checkbox("🛣️ Road Risk", True, key="map_show_roads")

    with control_cols[1]:
        show_infrastructure = st.checkbox(
            "🏥 Critical Infrastructure", True, key="map_show_infrastructure"
        )
        show_villages = st.checkbox("🏘️ Communities", True, key="map_show_villages")

    with control_cols[2]:
        show_incidents = st.checkbox("🚨 Field Incidents", True, key="map_show_incidents")
        show_labels = st.checkbox("🏷️ Village Labels", True, key="map_show_labels")

    with control_cols[3]:
        high_risk_only = st.checkbox("⚠️ High Risk Only", False, key="map_high_risk")
        active_layers = sum([
            bool(show_risk),
            bool(show_roads),
            bool(show_infrastructure),
            bool(show_villages),
            bool(show_incidents),
            bool(show_labels),
        ])
        st.markdown(
            f"<div class='map-control-status'><span>●</span> {active_layers}/6 layers active</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="map-help-card">
            <span class="map-help-icon">💡</span>
            <div>
                <b>Map layers</b><br>
                <span>Use the map's top-right <b>Layers</b> button to switch between OpenStreetMap, Satellite, Dark Map and Light Map. The controls above manage the risk overlays.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Base maps are added directly to the Folium map so they are available
    # inside the interactive map layer control.
    map_tiles = None

    # --------------------------------------------------------
    # APPLY GLOBAL REGION FILTER
    # --------------------------------------------------------
    selected_region = st.session_state.get("selected_region", "All NER")
    threshold = float(st.session_state.get("sidebar_risk_threshold", 60))

    def filter_by_region(df):
        if df.empty or selected_region == "All NER":
            return df.copy()

        result = df.copy()
        possible_columns = ["state", "State", "region", "Region"]
        for col in possible_columns:
            if col in result.columns:
                return result[
                    result[col].astype(str).str.strip().str.lower()
                    == selected_region.strip().lower()
                ].copy()
        return result

    map_villages = filter_by_region(village_results_df)
    map_risk = filter_by_region(risk_df)
    map_roads = filter_by_region(road_df)
    map_infra = filter_by_region(infra_df)
    map_incidents = load_incidents()

    if not map_incidents.empty and selected_region != "All NER":
        if "state" in map_incidents.columns:
            map_incidents = filter_by_region(map_incidents)
        elif "village" in map_incidents.columns and not map_villages.empty:
            allowed = set(map_villages["Village"].astype(str).str.lower())
            map_incidents = map_incidents[
                map_incidents["village"].astype(str).str.lower().isin(allowed)
            ].copy()

    # If the current dataset has no state field for a layer, keep it visible
    # rather than hiding valid prototype data.
    if map_risk.empty and not risk_df.empty and selected_region != "All NER":
        map_risk = risk_df.copy()
    if map_roads.empty and not road_df.empty and selected_region != "All NER":
        map_roads = road_df.copy()
    if map_infra.empty and not infra_df.empty and selected_region != "All NER":
        map_infra = infra_df.copy()

    # --------------------------------------------------------
    # MAP CENTER + BOUNDS
    # --------------------------------------------------------
    coordinate_points = []

    def add_point(lat_value, lon_value):
        try:
            lat = float(lat_value)
            lon = float(lon_value)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                coordinate_points.append([lat, lon])
        except (TypeError, ValueError):
            pass

    for df, lat_col, lon_col in [
        (map_villages, "Latitude", "Longitude"),
        (map_risk, "latitude", "longitude"),
        (map_roads, "latitude", "longitude"),
        (map_infra, "latitude", "longitude"),
    ]:
        if not df.empty and lat_col in df.columns and lon_col in df.columns:
            for _, r in df.iterrows():
                add_point(r.get(lat_col), r.get(lon_col))

    if not map_incidents.empty and "latitude" in map_incidents.columns:
        for _, r in map_incidents.iterrows():
            add_point(r.get("latitude"), r.get("longitude"))

    if coordinate_points:
        map_center = [
            sum(p[0] for p in coordinate_points) / len(coordinate_points),
            sum(p[1] for p in coordinate_points) / len(coordinate_points),
        ]
    else:
        map_center = [25.8, 92.0]

    m = folium.Map(
        location=map_center,
        zoom_start=6,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    # --------------------------------------------------------
    # INTERACTIVE BASE MAP SWITCHER
    # --------------------------------------------------------
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ OpenStreetMap",
        overlay=False,
        control=True,
        show=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="🛰️ Satellite",
        attr="Tiles © Esri",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        name="🌑 Dark Map",
        attr="© OpenStreetMap © CARTO",
        subdomains="abcd",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        name="☀️ Light Map",
        attr="© OpenStreetMap © CARTO",
        subdomains="abcd",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # --------------------------------------------------------
    # AI RISK ZONES — circles show spatial influence
    # --------------------------------------------------------
    if show_risk and not map_risk.empty:
        risk_layer = folium.FeatureGroup(name="🔴 AI Risk Zones", show=True)

        for _, row in map_risk.iterrows():
            try:
                probability = get_ai_probability(row)
                level = get_risk_level(probability)

                if high_risk_only and level not in ["HIGH", "CRITICAL"]:
                    continue
                if probability < threshold and high_risk_only:
                    continue

                lat = safe_float(row.get("latitude"))
                lon = safe_float(row.get("longitude"))
                radius = max(500, min(5000, probability * 45))
                popup = f"""
                <div style='min-width:260px'>
                <h4>🤖 AI Landslide Risk</h4>
                <b>Location:</b> {row.get('location', 'Unknown')}<br>
                <b>AI Probability:</b> {probability:.2f}%<br>
                <b>Risk Level:</b> {level}<br>
                <b>Rainfall:</b> {row.get('rainfall_mm', 'N/A')} mm<br>
                <b>Soil Moisture:</b> {row.get('soil_moisture', 'N/A')}%<br>
                <b>Slope:</b> {row.get('slope_deg', 'N/A')}°<br>
                <b>Ground Movement:</b> {row.get('ground_movement_mm', 'N/A')} mm
                </div>
                """

                folium.Circle(
                    location=[lat, lon],
                    radius=radius,
                    color=risk_color(level),
                    weight=2,
                    fill=True,
                    fill_color=risk_color(level),
                    fill_opacity=0.12,
                    popup=folium.Popup(popup, max_width=380),
                    tooltip=f"{row.get('location', 'Risk Zone')} • {probability:.1f}%",
                ).add_to(risk_layer)

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=9 if level in ["HIGH", "CRITICAL"] else 6,
                    color=risk_color(level),
                    fill=True,
                    fill_color=risk_color(level),
                    fill_opacity=0.85,
                    tooltip=f"AI Risk: {probability:.1f}% ({level})",
                    popup=folium.Popup(popup, max_width=380),
                ).add_to(risk_layer)
            except Exception:
                continue

        risk_layer.add_to(m)

    # --------------------------------------------------------
    # ROAD RISK — point markers or line geometry when available
    # --------------------------------------------------------
    if show_roads and not map_roads.empty:
        road_layer = folium.FeatureGroup(name="🛣️ Road Risk", show=True)

        for _, row in map_roads.iterrows():
            risk = str(row.get("risk_level", "Moderate"))
            risk_lower = risk.lower()
            if "critical" in risk_lower:
                road_color = "red"
            elif "high" in risk_lower:
                road_color = "orange"
            elif "moderate" in risk_lower:
                road_color = "beige"
            else:
                road_color = "blue"

            popup = f"""
            <b>🛣️ Road:</b> {row.get('road_name', 'Unknown')}<br>
            <b>Risk:</b> {risk}<br>
            <b>Connectivity:</b> {row.get('connectivity', 'Unknown')}
            """

            try:
                lat = safe_float(row.get("latitude"))
                lon = safe_float(row.get("longitude"))
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    color=road_color,
                    fill=True,
                    fill_color=road_color,
                    fill_opacity=0.75,
                    popup=folium.Popup(popup, max_width=320),
                    tooltip=f"Road: {row.get('road_name', 'Unknown')} • {risk}",
                ).add_to(road_layer)

                # Optional road line support if future CSV data contains endpoints.
                if all(c in row.index for c in ["start_lat", "start_lon", "end_lat", "end_lon"]):
                    folium.PolyLine(
                        locations=[
                            [safe_float(row["start_lat"]), safe_float(row["start_lon"])],
                            [safe_float(row["end_lat"]), safe_float(row["end_lon"])],
                        ],
                        color=road_color,
                        weight=6,
                        opacity=0.8,
                        popup=folium.Popup(popup, max_width=320),
                    ).add_to(road_layer)
            except Exception:
                continue

        road_layer.add_to(m)

    # --------------------------------------------------------
    # CRITICAL INFRASTRUCTURE
    # --------------------------------------------------------
    if show_infrastructure and not map_infra.empty:
        infrastructure_layer = folium.FeatureGroup(
            name="🏥 Critical Infrastructure", show=True
        )

        for _, row in map_infra.iterrows():
            popup = f"""
            <b>🏥 Infrastructure:</b> {row.get('name', 'Unknown')}<br>
            <b>Type:</b> {row.get('type', 'Unknown')}<br>
            <b>Importance:</b> {row.get('importance', 'Unknown')}
            """
            try:
                folium.Marker(
                    location=[safe_float(row.get("latitude")), safe_float(row.get("longitude"))],
                    popup=folium.Popup(popup, max_width=320),
                    tooltip=str(row.get("name", "Infrastructure")),
                    icon=folium.Icon(color="blue", icon="plus"),
                ).add_to(infrastructure_layer)
            except Exception:
                continue

        infrastructure_layer.add_to(m)

    # --------------------------------------------------------
    # COMMUNITY / VILLAGE MARKERS
    # --------------------------------------------------------
    if show_villages and not map_villages.empty:
        village_layer = folium.FeatureGroup(name="🏘️ Communities", show=True)

        for _, row in map_villages.iterrows():
            level = str(row.get("Alert", "LOW"))
            probability = safe_float(row.get("AI Risk (%)"))
            if high_risk_only and level not in ["HIGH", "CRITICAL"]:
                continue

            village = row.get("Village", "Unknown")
            popup = f"""
            <div style='min-width:280px'>
            <h4>🏘️ {village}</h4>
            <b>State:</b> {row.get('State', 'Unknown')}<br>
            <b>AI Risk:</b> {probability:.2f}%<br>
            <b>Alert:</b> {level}<br>
            <b>Response Priority:</b> {row.get('Priority', 'Unknown')}<br>
            <b>Priority Score:</b> {row.get('Priority Score', 'N/A')}/100<br>
            <b>Population:</b> {row.get('Population', 'N/A')}<br>
            <b>Road Connectivity:</b> {row.get('Road Connectivity', 'Unknown')}<br>
            <b>Nearest Hospital:</b> {row.get('Nearest Hospital', 'Unknown')}<br><br>
            <b>Recommended Action:</b><br>{row.get('Recommended Action', 'Continue monitoring.')}
            </div>
            """

            try:
                lat = safe_float(row.get("Latitude"))
                lon = safe_float(row.get("Longitude"))
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10 if level in ["HIGH", "CRITICAL"] else 7,
                    color=risk_color(level),
                    fill=True,
                    fill_color=risk_color(level),
                    fill_opacity=0.65,
                    popup=folium.Popup(popup, max_width=390),
                    tooltip=f"{village} • {probability:.1f}% • {level}",
                ).add_to(village_layer)

                if show_labels:
                    folium.Marker(
                        location=[lat, lon],
                        icon=folium.DivIcon(
                            html=f"<div style='font-size:10px;font-weight:700;color:white;text-shadow:0 1px 3px black'>{village}</div>"
                        ),
                    ).add_to(village_layer)
            except Exception:
                continue

        village_layer.add_to(m)

    # --------------------------------------------------------
    # GEO-TAGGED FIELD INCIDENTS
    # --------------------------------------------------------
    if show_incidents and not map_incidents.empty:
        incident_layer = folium.FeatureGroup(name="🚨 Field Incidents", show=True)

        for _, incident in map_incidents.iterrows():
            severity = str(incident.get("severity", "Low"))
            severity_lower = severity.lower()
            icon_color = (
                "red" if severity_lower == "critical"
                else "orange" if severity_lower == "high"
                else "beige" if severity_lower == "moderate"
                else "green"
            )
            popup = f"""
            <div style='min-width:270px'>
            <h4>🚨 Field Incident</h4>
            <b>Severity:</b> {severity}<br>
            <b>Village / Area:</b> {incident.get('village', 'Unknown')}<br>
            <b>Road Blocked:</b> {incident.get('road_blocked', 'Unknown')}<br>
            <b>Reported:</b> {incident.get('reported_at', 'Unknown')}<br><br>
            <b>Description:</b><br>{incident.get('description', 'No description')}
            </div>
            """
            try:
                folium.Marker(
                    location=[safe_float(incident.get("latitude")), safe_float(incident.get("longitude"))],
                    popup=folium.Popup(popup, max_width=380),
                    tooltip=f"Incident • {severity}",
                    icon=folium.Icon(color=icon_color, icon="exclamation-sign"),
                ).add_to(incident_layer)
            except Exception:
                continue

        incident_layer.add_to(m)

    folium.LayerControl(collapsed=True, position="topright").add_to(m)

    # --------------------------------------------------------
    # MAP HEADER METRICS
    # --------------------------------------------------------
    critical = int((map_villages["Alert"] == "CRITICAL").sum()) if "Alert" in map_villages.columns else 0
    high = int((map_villages["Alert"] == "HIGH").sum()) if "Alert" in map_villages.columns else 0
    moderate = int((map_villages["Alert"] == "MODERATE").sum()) if "Alert" in map_villages.columns else 0
    incidents_count = len(map_incidents)

    st.markdown("### 📡 Live GIS Situation")
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Communities", len(map_villages))
    mc2.metric("🔴 Critical", critical)
    mc3.metric("🟠 High", high)
    mc4.metric("🟡 Moderate", moderate)
    mc5.metric("🚨 Incidents", incidents_count)

    st.caption(
        f"Global region: {selected_region}  •  Alert threshold: {threshold:.0f}%  •  "
        f"Map points: {len(coordinate_points)}"
    )

    st.markdown(
        f"""<div class="glass" style="margin:10px 0 12px;padding:10px 14px;">
        <b>🧭 Map interaction:</b> zoom, pan, click markers for details, switch base maps, and use the <b>layers button</b> in the top-right to show or hide risk, roads, infrastructure, communities and field incidents.
        <span style="float:right;color:#76d7ff;">Interactive GIS • Base maps available in Layers</span>
        </div>""",
        unsafe_allow_html=True,
    )

    st_folium(
        m,
        use_container_width=True,
        height=720,
        returned_objects=["last_object_clicked", "bounds"],
        key="ner_live_risk_map",
    )

    st.info(
        "🟢 Low | 🟡 Moderate | 🟠 High | 🔴 Critical. "
        "Click any risk circle, village, road or incident marker for details. "
        "The map is a prototype decision-support view and is not an official evacuation order."
    )


# ============================================================
# SENSOR MONITORING
# ============================================================



elif page == "Alerts":
    st.markdown('<div class="section-marker alerts"></div><div class="section-accent alerts"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)
    _alert_critical = int((village_results_df["Alert"] == "CRITICAL").sum()) if not village_results_df.empty else 0
    _alert_high = int((village_results_df["Alert"] == "HIGH").sum()) if not village_results_df.empty else 0
    _alert_threshold = st.session_state.get("sidebar_risk_threshold", 60)
    render_live_summary(
        "Alerts",
        "Warnings are being converted into response priorities.",
        f"The alert center is watching {_alert_critical} critical and {_alert_high} high warning conditions. The active sidebar threshold is {_alert_threshold}%, so locations above the configured level should receive closer attention.",
        [("Critical", _alert_critical, "immediate attention"), ("High", _alert_high, "priority response"), ("Threshold", f"{_alert_threshold}%", "AI alert setting"), ("AI status", live_risk_level, f"{live_probability:.1f}% probability")],
    )

    st.markdown(
        """
        <div class="glass" style="padding:22px 24px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <div style="color:#67d5ff;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;">EARLY WARNING CENTER</div>
                    <div style="font-size:2rem;font-weight:850;margin-top:4px;">🚨 Alert Intelligence</div>
                    <div style="color:#9fb1c4;margin-top:5px;">Monitor → Predict → Prioritize → Alert → Respond</div>
                </div>
                <div style="padding:9px 13px;border-radius:999px;background:rgba(55,224,140,.10);border:1px solid rgba(55,224,140,.35);color:#70efad;font-weight:750;">● LIVE DECISION SUPPORT</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if village_results_df.empty:
        st.warning("No village data available.")
    else:
        # Global region filter from sidebar
        alerts_df = village_results_df.copy()
        selected_region_alerts = st.session_state.get("selected_region", "All NER")
        if selected_region_alerts != "All NER" and "State" in alerts_df.columns:
            alerts_df = alerts_df[alerts_df["State"].astype(str).str.strip() == selected_region_alerts].copy()

        # Controls
        af1, af2, af3 = st.columns([1, 1, 1])
        with af1:
            alert_level_filter = st.selectbox(
                "🔎 Alert level",
                ["All Levels", "CRITICAL", "HIGH", "MODERATE", "LOW"],
                key="alerts_level_filter",
            )
        with af2:
            alert_threshold = st.slider(
                "🎯 Minimum AI probability",
                0, 100, int(st.session_state.get("sidebar_risk_threshold", 60)), 5,
                key="alerts_probability_filter",
            )
        with af3:
            sort_mode = st.selectbox(
                "↕️ Sort alerts by",
                ["Priority Score", "AI Risk (%)", "Population"],
                key="alerts_sort_mode",
            )

        alerts_df = alerts_df[alerts_df["AI Risk (%)"] >= alert_threshold].copy()
        if alert_level_filter != "All Levels":
            alerts_df = alerts_df[alerts_df["Alert"] == alert_level_filter].copy()

        counts = {level: int((alerts_df["Alert"] == level).sum()) for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]}

        # Attractive alert cards
        st.markdown("### 📊 Current Alert Situation")
        c1, c2, c3, c4 = st.columns(4)
        cards = [
            (c1, "🚨", "CRITICAL", counts["CRITICAL"], "Immediate attention", "rgba(255,55,80,.20)", "#ff6374"),
            (c2, "🔴", "HIGH", counts["HIGH"], "Priority monitoring", "rgba(255,132,45,.18)", "#ffad61"),
            (c3, "🟠", "MODERATE", counts["MODERATE"], "Continue monitoring", "rgba(255,194,56,.15)", "#ffd166"),
            (c4, "🟢", "LOW", counts["LOW"], "Routine monitoring", "rgba(47,215,130,.14)", "#6de6a4"),
        ]
        for col, icon, label, value, subtitle, bg, accent in cards:
            with col:
                st.markdown(
                    f"""<div style="padding:17px;border-radius:16px;background:linear-gradient(135deg,{bg},rgba(7,24,41,.88));border:1px solid {accent}55;min-height:112px;box-shadow:0 10px 28px rgba(0,0,0,.16);">
                    <div style="font-size:1.15rem;">{icon} <span style="font-weight:800;color:{accent};">{label}</span></div>
                    <div style="font-size:2.2rem;font-weight:850;line-height:1;margin-top:8px;">{value}</div>
                    <div style="color:#9fb1c4;font-size:.78rem;margin-top:6px;">{subtitle}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.caption(f"Showing {len(alerts_df)} alert records • Region: {selected_region_alerts} • Minimum AI probability: {alert_threshold}%")

        # Highest priority alerts
        if not alerts_df.empty:
            sort_column = sort_mode
            priority_view = alerts_df.sort_values(sort_column, ascending=False).copy()

            st.markdown("### 🚨 Priority Alert Queue")

            for _, alert in priority_view.head(6).iterrows():
                level = str(alert.get("Alert", "LOW"))
                color = {"CRITICAL":"#ff5366", "HIGH":"#ff9f43", "MODERATE":"#ffd166", "LOW":"#54d98c"}.get(level, "#6ec8ff")
                icon = {"CRITICAL":"🚨", "HIGH":"⚠️", "MODERATE":"🟡", "LOW":"🟢"}.get(level, "ℹ️")
                village = alert.get("Village", "Unknown")
                risk = safe_float(alert.get("AI Risk (%)", 0))
                priority = safe_float(alert.get("Priority Score", 0))
                action = alert.get("Recommended Action", "Continue monitoring.")
                hospital = alert.get("Nearest Hospital", "Unknown")

                st.markdown(
                    f"""<div style="margin:9px 0;padding:15px 17px;border-radius:15px;background:linear-gradient(135deg,rgba(8,26,44,.94),rgba(5,18,31,.88));border:1px solid {color}66;border-left:5px solid {color};">
                    <div style="display:flex;justify-content:space-between;gap:15px;align-items:center;flex-wrap:wrap;">
                        <div><span style="font-size:1.05rem;font-weight:850;">{icon} {village}</span> <span style="margin-left:8px;padding:4px 9px;border-radius:999px;background:{color}22;color:{color};font-size:.72rem;font-weight:800;">{level}</span></div>
                        <div style="font-size:1.45rem;font-weight:850;">{risk:.1f}%</div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px;">
                        <div style="color:#9fb1c4;font-size:.78rem;">AI RISK<br><b style="color:#f2f7fb;font-size:.92rem;">{risk:.1f}%</b></div>
                        <div style="color:#9fb1c4;font-size:.78rem;">PRIORITY SCORE<br><b style="color:#f2f7fb;font-size:.92rem;">{priority:.1f}/100</b></div>
                        <div style="color:#9fb1c4;font-size:.78rem;">HOSPITAL ACCESS<br><b style="color:#f2f7fb;font-size:.92rem;">{hospital}</b></div>
                    </div>
                    <div style="margin-top:11px;padding:9px 11px;border-radius:10px;background:rgba(255,255,255,.035);color:#cbd8e4;font-size:.82rem;"><b>Recommended response:</b> {action}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.success("🟢 No alerts match the current region, level and probability filters.")

        st.markdown("### 📋 Alert Register")

        columns = [
            "Village", "State", "AI Risk (%)", "Risk Level",
            "Priority", "Priority Score", "Alert", "Recommended Action"
        ]
        all_alerts = alerts_df[[c for c in columns if c in alerts_df.columns]].copy()
        if "Priority Score" in all_alerts.columns:
            all_alerts = all_alerts.sort_values("Priority Score", ascending=False)

        st.dataframe(
            all_alerts,
            use_container_width=True,
            hide_index=True,
            column_config={
                "AI Risk (%)": st.column_config.ProgressColumn("AI Risk (%)", min_value=0, max_value=100, format="%.1f%%"),
                "Priority Score": st.column_config.ProgressColumn("Priority Score", min_value=0, max_value=100, format="%.1f"),
            },
        )

        st.download_button(
            "⬇️ Download Alert Register",
            data=all_alerts.to_csv(index=False),
            file_name="NER_alert_register.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.info(
            "Prototype decision-support warning system. AI probabilities and priority scores are indicators for monitoring and response planning; they are not official evacuation orders."
        )

# ============================================================
# PREDICTED LANDSLIDE RISK
# ============================================================

elif page == "Predicted Landslide Risk":
    st.markdown('<div class="section-marker predictions"></div><div class="section-accent predictions"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)

    # IMPORTANT: this view is read-only. The controls below only filter, sort
    # and inspect the existing model predictions; they never change risk values
    # or recalculate/override the prediction itself.
    prediction_df = village_results_df.copy()

    st.markdown(
        """<div class="prediction-hero glass">
            <div class="prediction-orbit">🔮</div>
            <div style="flex:1;min-width:260px;">
                <div class="prediction-kicker">AI FORECAST • READ-ONLY</div>
                <div class="prediction-title">Predicted Landslide Risk</div>
                <div class="prediction-subtitle">Explore the locations already ranked by the AI engine without changing the prediction.</div>
                <div class="prediction-pills">
                    <span>🔒 Prediction Locked</span>
                    <span>📍 Location Intelligence</span>
                    <span>⏱️ Estimated Warning Window</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True
    )

    if prediction_df.empty:
        st.info("No prediction locations are available.")
    else:
        # Read-only interactive controls. They affect display only.
        states = ["All Regions"]
        if "State" in prediction_df.columns:
            states += sorted(prediction_df["State"].dropna().astype(str).str.strip().unique().tolist())

        levels_present = [str(x).upper() for x in prediction_df.get("Alert", pd.Series(dtype=str)).dropna().tolist()]
        level_order = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
        available_levels = [x for x in level_order if x in set(levels_present)]

        st.markdown('<div class="prediction-control-panel">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
        with c1:
            prediction_region = st.selectbox(
                "📍 Explore region",
                states,
                key="prediction_region_filter",
            )
        with c2:
            prediction_level = st.selectbox(
                "🚨 Risk level",
                ["All Levels"] + available_levels,
                key="prediction_level_filter",
            )
        with c3:
            prediction_sort = st.selectbox(
                "↕️ Sort display",
                ["Highest risk first", "Lowest risk first", "Location A–Z"],
                key="prediction_sort_filter",
            )
        st.markdown('</div>', unsafe_allow_html=True)

        filtered = prediction_df.copy()
        if prediction_region != "All Regions" and "State" in filtered.columns:
            filtered = filtered[filtered["State"].astype(str).str.strip() == prediction_region]
        if prediction_level != "All Levels" and "Alert" in filtered.columns:
            filtered = filtered[filtered["Alert"].astype(str).str.upper() == prediction_level]

        if prediction_sort == "Highest risk first":
            filtered = filtered.sort_values(["AI Risk (%)", "Priority Score"], ascending=False)
        elif prediction_sort == "Lowest risk first":
            filtered = filtered.sort_values(["AI Risk (%)", "Priority Score"], ascending=True)
        else:
            filtered = filtered.sort_values(["Village", "State"], ascending=True)

        filtered = filtered.head(20)

        # Summary reflects the displayed records only; it does not modify the source prediction.
        critical_count = int((filtered.get("Alert", pd.Series(index=filtered.index, dtype=str)).astype(str).str.upper() == "CRITICAL").sum())
        high_count = int((filtered.get("Alert", pd.Series(index=filtered.index, dtype=str)).astype(str).str.upper() == "HIGH").sum())
        avg_risk = float(pd.to_numeric(filtered.get("AI Risk (%)", pd.Series(dtype=float)), errors="coerce").mean()) if not filtered.empty else 0.0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📌 Locations shown", len(filtered))
        k2.metric("🔴 Critical", critical_count)
        k3.metric("🟠 High", high_count)
        k4.metric("📊 Average AI risk", f"{avg_risk:.1f}%" if not filtered.empty else "—")

        st.markdown(
            '<div class="prediction-lock-note">🔒 <b>Prediction integrity:</b> these controls only change what is displayed. AI risk, location ranking data and prediction source values are not editable from this page.</div>',
            unsafe_allow_html=True,
        )

        if filtered.empty:
            st.warning("No predicted locations match the selected filters.")
        else:
            st.markdown("### 📍 Explore predicted locations")
            left, right = st.columns([1.55, 1.0])

            with left:
                for idx, (_, row) in enumerate(filtered.iterrows(), start=1):
                    risk = safe_float(row.get("AI Risk (%)"))
                    level = str(row.get("Alert", row.get("Risk Level", "LOW"))).upper()
                    accent = {"CRITICAL":"#ef4444", "HIGH":"#f97316", "MODERATE":"#eab308", "LOW":"#22c55e"}.get(level, "#60a5fa")
                    icon = {"CRITICAL":"🔴", "HIGH":"🟠", "MODERATE":"🟡", "LOW":"🟢"}.get(level, "🔵")
                    hours = {"CRITICAL":2, "HIGH":6, "MODERATE":12, "LOW":24}.get(level, 24)
                    predicted_time = (datetime.now() + timedelta(hours=hours)).strftime("%d %b %Y • %I:%M %p")
                    village = str(row.get("Village", "Unknown"))
                    state = str(row.get("State", "Unknown"))
                    population = safe_float(row.get("Population", 0))
                    priority = safe_float(row.get("Priority Score", 0))

                    st.markdown(
                        f"""<div class="prediction-card" style="--prediction-accent:{accent};">
                            <div class="prediction-card-top">
                                <div>
                                    <div class="prediction-location">{idx:02d} · 📍 {village}, {state}</div>
                                    <div class="prediction-meta">
                                        <span class="prediction-badge">{icon} {level}</span>
                                        <span>🕒 {predicted_time}</span>
                                    </div>
                                </div>
                                <div class="prediction-score">{risk:.1f}<small>%</small></div>
                            </div>
                            <div class="prediction-bar"><span style="width:{max(0,min(100,risk)):.1f}%;background:{accent};box-shadow:0 0 12px {accent}99;"></span></div>
                            <div class="prediction-mini-grid">
                                <div><span>AI risk</span><b>{risk:.1f}%</b></div>
                                <div><span>Priority</span><b>{priority:.1f}</b></div>
                                <div><span>Population</span><b>{population:,.0f}</b></div>
                            </div>
                        </div>""", unsafe_allow_html=True
                    )

            with right:
                st.markdown("#### 🧭 Inspect a prediction")
                labels = [f"{row.get('Village','Unknown')}, {row.get('State','Unknown')}" for _, row in filtered.iterrows()]
                selected_label = st.selectbox("Select a predicted location", labels, key="prediction_detail_location")
                selected_idx = labels.index(selected_label)
                selected_row = filtered.iloc[selected_idx]
                selected_risk = safe_float(selected_row.get("AI Risk (%)"))
                selected_level = str(selected_row.get("Alert", selected_row.get("Risk Level", "LOW"))).upper()
                selected_hours = {"CRITICAL":2, "HIGH":6, "MODERATE":12, "LOW":24}.get(selected_level, 24)
                selected_time = (datetime.now() + timedelta(hours=selected_hours)).strftime("%d %b %Y • %I:%M %p")
                selected_accent = {"CRITICAL":"#ef4444", "HIGH":"#f97316", "MODERATE":"#eab308", "LOW":"#22c55e"}.get(selected_level, "#60a5fa")

                st.markdown(
                    f"""<div class="prediction-detail glass" style="--prediction-accent:{selected_accent};">
                        <div class="detail-orb">{ {'CRITICAL':'🔴','HIGH':'🟠','MODERATE':'🟡','LOW':'🟢'}.get(selected_level,'🔵') }</div>
                        <div class="detail-level">{selected_level}</div>
                        <div class="detail-risk">{selected_risk:.1f}%</div>
                        <div class="detail-label">AI risk probability</div>
                        <div class="detail-row"><span>📍 Location</span><b>{selected_row.get('Village','Unknown')}, {selected_row.get('State','Unknown')}</b></div>
                        <div class="detail-row"><span>🕒 Estimated window</span><b>{selected_time}</b></div>
                        <div class="detail-row"><span>🎯 Priority score</span><b>{safe_float(selected_row.get('Priority Score',0)):.1f}</b></div>
                        <div class="detail-row"><span>👥 Population</span><b>{safe_float(selected_row.get('Population',0)):,.0f}</b></div>
                    </div>""", unsafe_allow_html=True
                )

                st.markdown("#### 📈 Risk profile")
                chart_df = filtered[[c for c in ["Village", "AI Risk (%)"] if c in filtered.columns]].copy()
                if not chart_df.empty and "AI Risk (%)" in chart_df.columns:
                    chart_df["AI Risk (%)"] = pd.to_numeric(chart_df["AI Risk (%)"], errors="coerce")
                    chart_df = chart_df.dropna(subset=["AI Risk (%)"]).head(10)
                    if not chart_df.empty:
                        fig = px.bar(chart_df, x="AI Risk (%)", y="Village", orientation="h", text="AI Risk (%)")
                        fig.update_layout(
                            height=390,
                            margin=dict(l=10,r=10,t=10,b=10),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#f5f8ff"),
                            xaxis=dict(range=[0,100], title="AI risk (%)", gridcolor="rgba(255,255,255,.08)"),
                            yaxis=dict(title="", categoryorder="total ascending"),
                            showlegend=False,
                        )
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown(
            """<div class="prediction-disclaimer">
                ⚠️ <b>Forecast interpretation:</b> the date/time shown is a prototype estimated warning window derived from the existing risk level. It is not a guaranteed landslide occurrence time or an official evacuation order. No control on this page changes the underlying prediction.
            </div>""",
            unsafe_allow_html=True,
        )


# ============================================================
# SENSOR MONITORING
# ============================================================
elif page == "Early Alert Systems":
    st.markdown('<div class="section-marker earlyalerts"></div><div class="section-accent earlyalerts"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)
    early_df = village_results_df.copy()

    st.markdown(
        """
        <div class="glass" style="padding:22px 24px;margin-bottom:16px;border:1px solid rgba(250,204,21,.28);background:linear-gradient(135deg,rgba(250,204,21,.12),rgba(20,12,5,.84));">
            <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <div style="color:#facc15;font-size:.72rem;font-weight:900;letter-spacing:.15em;text-transform:uppercase;">EARLY ALERT BROADCAST CENTER</div>
                    <div style="font-size:2rem;font-weight:900;margin-top:4px;">📢 Predicted Disaster Warnings</div>
                    <div style="color:#c8d3de;margin-top:6px;max-width:820px;">Warnings are generated from the existing AI prediction results. This page only presents, filters and prioritizes warnings — it does not alter the underlying prediction.</div>
                </div>
                <div style="padding:9px 13px;border-radius:999px;background:rgba(250,204,21,.10);border:1px solid rgba(250,204,21,.32);color:#ffe889;font-weight:850;">🔒 PREDICTION LOCKED</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if early_df.empty:
        st.warning("No predicted disaster conditions are currently available.")
    else:
        early_df = early_df.copy()
        if "AI Risk (%)" in early_df.columns:
            early_df["AI Risk (%)"] = pd.to_numeric(early_df["AI Risk (%)"], errors="coerce").fillna(0)

        selected_region_early = st.session_state.get("selected_region", "All NER")
        if selected_region_early != "All NER" and "State" in early_df.columns:
            early_df = early_df[early_df["State"].astype(str).str.strip() == selected_region_early].copy()

        e1, e2, e3 = st.columns([1.15, 1.15, 1.0])
        with e1:
            early_level = st.selectbox("🚨 Warning level", ["All Levels", "CRITICAL", "HIGH", "MODERATE", "LOW"], key="early_alert_level_filter")
        with e2:
            early_sort = st.selectbox("↕️ Sort warnings", ["Highest risk first", "Earliest warning first", "Location A–Z"], key="early_alert_sort")
        with e3:
            early_min = st.slider("🎯 Minimum risk", 0, 100, 60, 5, key="early_alert_min_risk")

        early_df = early_df[early_df["AI Risk (%)"] >= early_min].copy()
        if early_level != "All Levels" and "Alert" in early_df.columns:
            early_df = early_df[early_df["Alert"].astype(str).str.upper() == early_level].copy()
        if "Alert" not in early_df.columns:
            early_df["Alert"] = "LOW"

        def _early_hours(level):
            return {"CRITICAL": 2, "HIGH": 6, "MODERATE": 12, "LOW": 24}.get(str(level).upper(), 24)

        early_df["_warning_hours"] = early_df["Alert"].apply(_early_hours)
        early_df["_warning_time"] = early_df["_warning_hours"].apply(lambda h: datetime.now() + timedelta(hours=int(h)))

        if early_sort == "Highest risk first":
            sort_cols = ["AI Risk (%)"] + (["Priority Score"] if "Priority Score" in early_df.columns else [])
            early_df = early_df.sort_values(sort_cols, ascending=False)
        elif early_sort == "Earliest warning first":
            early_df = early_df.sort_values("_warning_time", ascending=True)
        else:
            early_df = early_df.sort_values([c for c in ["Village", "State"] if c in early_df.columns], ascending=True)

        early_df = early_df.head(20).copy()

        critical = int((early_df["Alert"].astype(str).str.upper() == "CRITICAL").sum())
        high = int((early_df["Alert"].astype(str).str.upper() == "HIGH").sum())
        imminent = int((early_df["_warning_hours"] <= 6).sum())

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("📢 Active warnings", len(early_df))
        s2.metric("🚨 Critical", critical)
        s3.metric("🟠 High", high)
        s4.metric("⏱️ ≤ 6 hr window", imminent)

        st.markdown(
            '<div style="margin:14px 0;padding:11px 14px;border-radius:13px;background:rgba(250,204,21,.07);border:1px solid rgba(250,204,21,.20);color:#f5e6ae;font-size:.82rem;">💡 <b>How this works:</b> the warning window is derived from the existing risk level for prototype display. No warning control changes the AI prediction itself.</div>',
            unsafe_allow_html=True,
        )

        if early_df.empty:
            st.success("🟢 No predicted disaster warnings match the current filters.")
        else:
            st.markdown("### 📡 Active Early Warnings")
            for idx, (_, warning) in enumerate(early_df.iterrows(), start=1):
                level = str(warning.get("Alert", "LOW")).upper()
                risk = safe_float(warning.get("AI Risk (%)", 0))
                village = str(warning.get("Village", "Unknown"))
                state = str(warning.get("State", "Unknown"))
                hours = int(warning.get("_warning_hours", 24))
                warning_time = warning.get("_warning_time", datetime.now() + timedelta(hours=hours))
                warning_time_text = warning_time.strftime("%d %b %Y • %I:%M %p")
                accent = {"CRITICAL":"#ef4444", "HIGH":"#f97316", "MODERATE":"#facc15", "LOW":"#22c55e"}.get(level, "#94a3b8")
                icon = {"CRITICAL":"🚨", "HIGH":"⚠️", "MODERATE":"🟡", "LOW":"🟢"}.get(level, "ℹ️")
                action = warning.get("Recommended Action", "Continue monitoring and verify field conditions.")
                priority = safe_float(warning.get("Priority Score", 0))
                st.markdown(
                    f"""
                    <div style="margin:10px 0;padding:17px 18px;border-radius:18px;background:linear-gradient(135deg,rgba(8,20,32,.94),rgba(38,24,7,.90));border:1px solid {accent}66;border-left:5px solid {accent};box-shadow:0 10px 30px rgba(0,0,0,.20);">
                        <div style="display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;">
                            <div>
                                <div style="font-size:1.08rem;font-weight:900;">{icon} {village}, {state}</div>
                                <div style="margin-top:6px;color:#b7c5d2;font-size:.78rem;">Warning #{idx:02d} • Predicted landslide condition</div>
                            </div>
                            <div style="font-size:1.75rem;font-weight:950;color:{accent};">{risk:.1f}%</div>
                        </div>
                        <div style="height:7px;border-radius:99px;background:rgba(255,255,255,.08);margin:13px 0;overflow:hidden;"><div style="height:100%;width:{max(0,min(100,risk)):.1f}%;background:{accent};box-shadow:0 0 14px {accent}88;border-radius:99px;"></div></div>
                        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:9px;">
                            <div style="padding:9px 10px;border-radius:11px;background:rgba(255,255,255,.035);"><span style="color:#8fa4b8;font-size:.66rem;text-transform:uppercase;">Level</span><br><b style="color:{accent};">{level}</b></div>
                            <div style="padding:9px 10px;border-radius:11px;background:rgba(255,255,255,.035);"><span style="color:#8fa4b8;font-size:.66rem;text-transform:uppercase;">Warning window</span><br><b>{hours} hours</b></div>
                            <div style="padding:9px 10px;border-radius:11px;background:rgba(255,255,255,.035);"><span style="color:#8fa4b8;font-size:.66rem;text-transform:uppercase;">Estimated time</span><br><b>{warning_time_text}</b></div>
                            <div style="padding:9px 10px;border-radius:11px;background:rgba(255,255,255,.035);"><span style="color:#8fa4b8;font-size:.66rem;text-transform:uppercase;">Priority</span><br><b>{priority:.1f}/100</b></div>
                        </div>
                        <div style="margin-top:11px;padding:10px 12px;border-radius:11px;background:rgba(250,204,21,.055);border:1px solid rgba(250,204,21,.10);color:#d8e1e8;font-size:.80rem;"><b>Recommended response:</b> {action}</div>
                        <div style="margin-top:9px;color:#91a6ba;font-size:.73rem;">📣 Alert channels: Medical • Police • Fire • Rescue teams • Local administration</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if not early_df.empty:
            st.markdown("### 🧭 Inspect a Warning")
            warning_labels = [f"{r.get('Village','Unknown')}, {r.get('State','Unknown')}" for _, r in early_df.iterrows()]
            selected_warning = st.selectbox("Select warning location", warning_labels, key="early_alert_detail_location")
            warning_idx = warning_labels.index(selected_warning)
            selected_warning_row = early_df.iloc[warning_idx]
            selected_level = str(selected_warning_row.get("Alert", "LOW")).upper()
            selected_risk = safe_float(selected_warning_row.get("AI Risk (%)", 0))
            selected_hours = int(selected_warning_row.get("_warning_hours", 24))
            selected_time = (datetime.now() + timedelta(hours=selected_hours)).strftime("%d %b %Y • %I:%M %p")
            d1, d2 = st.columns([1.05, 1.6])
            with d1:
                st.markdown(
                    f"""
                    <div class="glass" style="padding:18px;border:1px solid #facc1555;background:linear-gradient(145deg,rgba(250,204,21,.12),rgba(18,20,22,.88));">
                        <div style="color:#facc15;font-size:.72rem;font-weight:900;letter-spacing:.12em;">WARNING STATUS</div>
                        <div style="font-size:2.5rem;font-weight:950;color:#facc15;margin-top:5px;">{selected_risk:.1f}%</div>
                        <div style="font-weight:900;color:#facc15;">{selected_level}</div>
                        <div style="margin-top:12px;color:#c4d3e2;">📍 {selected_warning_row.get('Village','Unknown')}, {selected_warning_row.get('State','Unknown')}</div>
                        <div style="margin-top:6px;color:#c4d3e2;">🕒 {selected_time}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with d2:
                st.markdown("#### 📣 Response readiness")
                response_df = pd.DataFrame({
                    "Response team": ["🏥 Medical", "👮 Police", "🚒 Fire", "🛟 Rescue", "🏛️ Local administration"],
                    "Status": ["READY", "READY", "READY", "READY", "READY"],
                    "Trigger": ["Confirmed incident", "Confirmed incident", "Fire/access hazard", "Rescue requirement", "Public warning"],
                })
                st.dataframe(response_df, use_container_width=True, hide_index=True)

        st.markdown(
            '<div style="margin-top:16px;padding:14px 16px;border-radius:15px;background:rgba(255,193,7,.07);border:1px solid rgba(255,193,7,.20);color:#ead9ad;font-size:.78rem;line-height:1.5;">⚠️ <b>Prototype notice:</b> this page presents current AI risk outputs as warning messages. The displayed warning time is an estimated window, not a guaranteed disaster time or official evacuation order. Actual emergency dispatch requires authorized agency communication integrations.</div>',
            unsafe_allow_html=True,
        )


elif page == "Sensors":
    st.markdown('<div class="section-marker sensors"></div><div class="section-accent sensors"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)

    current = get_live_sensor_values()
    current_probability = get_ai_probability(pd.Series(current))
    current_level = get_risk_level(current_probability)

    level_colors = {
        "CRITICAL": "#ff5366",
        "HIGH": "#ff9f43",
        "MODERATE": "#ffd166",
        "LOW": "#54d98c",
    }
    level_color = level_colors.get(current_level, "#6ec8ff")

    render_live_summary(
        "Sensors",
        "Environmental signals are feeding the AI risk engine.",
        f"Current sensor conditions produce a {current_probability:.1f}% estimated landslide probability, classified as {current_level}. The readings below let you see which environmental signals are changing the risk picture.",
        [("AI probability", f"{current_probability:.1f}%", current_level), ("Rainfall", f"{current["rainfall_mm"]:.1f} mm", "current input"), ("Moisture", f"{current["soil_moisture"]:.1f}%", "current input"), ("Movement", f"{current["ground_movement_mm"]:.1f} mm", "ground movement")],
    )

    # ------------------------------------------------------------
    # SENSOR HEADER
    # ------------------------------------------------------------
    st.markdown(
        f"""
        <div class="sensor-hero">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap;">
                <div>
                    <div class="sensor-kicker">ENVIRONMENTAL INTELLIGENCE</div>
                    <div class="sensor-title">📡 Live Sensor Command Center</div>
                    <div class="sensor-subtitle">Monitor field signals, inspect sensor health and test how changing conditions affect AI landslide risk.</div>
                </div>
                <div class="sensor-live"><span class="sensor-dot"></span> LIVE MONITORING</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------
    # TOP STATUS CARDS
    # ------------------------------------------------------------
    sensor_data = pd.DataFrame({
        "Sensor": ["Soil Sensor 01", "Rain Gauge 01", "Movement Sensor 01", "Soil Sensor 02", "Rain Gauge 02"],
        "Location": ["Tawang", "Sela", "Dirang", "Bomdila", "Tawang"],
        "Value": [89, 164, 12, 71, 145],
        "Unit": ["%", "mm", "mm", "%", "mm"],
        "Status": ["Warning", "Critical", "Warning", "Normal", "Warning"],
    })

    critical_sensors = int((sensor_data["Status"] == "Critical").sum())
    warning_sensors = int((sensor_data["Status"] == "Warning").sum())

    t1, t2, t3, t4 = st.columns(4)
    top_cards = [
        (t1, "📡", "Sensor Channels", "05", "All prototype channels active", "#67d5ff"),
        (t2, "🚨", "Critical Signals", f"{critical_sensors:02d}", "Needs immediate attention", "#ff6374"),
        (t3, "⚠️", "Warning Signals", f"{warning_sensors:02d}", "Increased monitoring", "#ffad61"),
        (t4, "🤖", "AI Risk", f"{current_probability:.1f}%", current_level, level_color),
    ]
    for col, icon, label, value, note, accent in top_cards:
        with col:
            st.markdown(
                f"""<div class="sensor-stat" style="border-top:2px solid {accent};">
                    <div class="sensor-stat-label">{icon} {label}</div>
                    <div class="sensor-stat-value">{value}</div>
                    <div class="sensor-stat-note" style="color:{accent};">● {note}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ------------------------------------------------------------
    # SENSOR HEALTH
    # ------------------------------------------------------------
    st.markdown('<div class="sensor-section-label">🟢 Field Sensor Health</div>', unsafe_allow_html=True)

    health_cols = st.columns(5)
    health_rows = [
        ("🌧️", "Rain Gauge 01", "Sela", "164 mm", "CRITICAL", 92, "#ff5366"),
        ("💧", "Soil Sensor 01", "Tawang", "89 %", "WARNING", 76, "#ff9f43"),
        ("🌍", "Movement 01", "Dirang", "12 mm", "WARNING", 61, "#ff9f43"),
        ("💧", "Soil Sensor 02", "Bomdila", "71 %", "NORMAL", 44, "#54d98c"),
        ("🌧️", "Rain Gauge 02", "Tawang", "145 mm", "WARNING", 80, "#ff9f43"),
    ]
    for col, (icon, name, location, reading, status, pct, accent) in zip(health_cols, health_rows):
        with col:
            st.markdown(
                f"""<div class="sensor-tile">
                    <div class="sensor-tile-head">
                        <div style="font-size:1.35rem;">{icon}</div>
                        <span class="sensor-status" style="background:{accent}22;color:{accent};border:1px solid {accent}55;">{status}</span>
                    </div>
                    <div class="sensor-name" style="margin-top:9px;">{name}</div>
                    <div class="sensor-location">📍 {location}</div>
                    <div class="sensor-reading">{reading}</div>
                    <div class="sensor-progress"><div class="sensor-progress-fill" style="width:{pct}%;background:{accent};box-shadow:0 0 10px {accent}66;"></div></div>
                </div>""",
                unsafe_allow_html=True,
            )

    with st.expander("📋 View detailed sensor register", expanded=False):
        st.dataframe(
            sensor_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Value": st.column_config.NumberColumn("Current Value", format="%.1f"),
            },
        )

    # ------------------------------------------------------------
    # LIVE AI SCENARIO
    # ------------------------------------------------------------
    st.markdown('<div class="sensor-section-label">🧠 Interactive AI Sensor Simulator</div>', unsafe_allow_html=True)
    st.info("Adjust the environmental inputs below to simulate an IoT gateway update. The AI probability changes immediately. These are prototype/simulated values, not certified field measurements.")

    sc1, sc2, sc3 = st.columns([1, 1, 1])
    with sc1:
        new_rain = st.slider("🌧️ Rainfall (mm)", 0.0, 300.0, float(current["rainfall_mm"]), 1.0, key="sensor_rain")
        new_moisture = st.slider("💧 Soil moisture (%)", 0.0, 100.0, float(current["soil_moisture"]), 1.0, key="sensor_moisture")
    with sc2:
        new_slope = st.slider("📐 Slope (°)", 0.0, 60.0, float(current["slope_deg"]), 0.5, key="sensor_slope")
        new_movement = st.slider("🌍 Ground movement (mm)", 0.0, 30.0, float(current["ground_movement_mm"]), 0.5, key="sensor_movement")
    with sc3:
        new_elevation = st.slider("⛰️ Elevation (m)", 0.0, 4000.0, float(current["elevation_m"]), 50.0, key="sensor_elevation")
        if st.button("💾 Apply Scenario", use_container_width=True, type="primary"):
            st.session_state.live_sensors.update({
                "rainfall_mm": new_rain,
                "soil_moisture": new_moisture,
                "slope_deg": new_slope,
                "ground_movement_mm": new_movement,
                "elevation_m": new_elevation,
            })
            st.rerun()
        if st.button("🔄 Simulate Sensor Refresh", use_container_width=True):
            refresh_live_sensor_values()
            st.rerun()

    scenario_values = {
        "rainfall_mm": new_rain,
        "soil_moisture": new_moisture,
        "slope_deg": new_slope,
        "ground_movement_mm": new_movement,
        "elevation_m": new_elevation,
    }
    scenario_probability = get_ai_probability(pd.Series(scenario_values))
    scenario_level = get_risk_level(scenario_probability)
    scenario_color = level_colors.get(scenario_level, "#6ec8ff")

    ai1, ai2 = st.columns([1, 2])
    with ai1:
        st.markdown(
            f"""<div class="sensor-ai-card">
                <div class="sensor-kicker">AI PREDICTION</div>
                <div class="sensor-ai-value" style="color:{scenario_color};">{scenario_probability:.1f}%</div>
                <div class="sensor-ai-label">Estimated landslide probability from the current scenario</div>
                <div class="sensor-badge" style="background:{scenario_color}22;color:{scenario_color};border:1px solid {scenario_color}66;">{scenario_level} RISK</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with ai2:
        scenario_chart = pd.DataFrame({
            "Parameter": ["Rainfall", "Soil Moisture", "Slope", "Ground Movement", "Elevation"],
            "Value": [new_rain, new_moisture, new_slope, new_movement, new_elevation],
        })
        fig_sensor = px.bar(
            scenario_chart,
            x="Parameter",
            y="Value",
            title="Live Environmental Inputs",
        )
        fig_sensor.update_layout(
            margin=dict(l=10, r=10, t=45, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#dce8f3"),
        )
        st.plotly_chart(fig_sensor, use_container_width=True, config={"displayModeBar": False})

    # ------------------------------------------------------------
    # CURRENT READINGS + RESPONSE
    # ------------------------------------------------------------
    st.markdown('<div class="sensor-section-label">📊 Current AI Input Readings</div>', unsafe_allow_html=True)
    reading_cols = st.columns(5)
    readings = [
        (reading_cols[0], "🌧️", "Rainfall", new_rain, "mm", 200),
        (reading_cols[1], "💧", "Soil Moisture", new_moisture, "%", 100),
        (reading_cols[2], "📐", "Slope", new_slope, "°", 45),
        (reading_cols[3], "🌍", "Ground Movement", new_movement, "mm", 20),
        (reading_cols[4], "⛰️", "Elevation", new_elevation, "m", 3000),
    ]
    for col, icon, label, value, unit, maximum in readings:
        with col:
            ratio = min(max(float(value) / float(maximum), 0), 1) * 100
            st.markdown(
                f"""<div class="sensor-tile">
                    <div style="font-size:1.15rem;">{icon}</div>
                    <div class="sensor-location" style="margin-top:7px;">{label}</div>
                    <div class="sensor-reading">{value:.1f} <span style="font-size:.8rem;color:#8fa4b8;">{unit}</span></div>
                    <div class="sensor-progress"><div class="sensor-progress-fill" style="width:{ratio:.0f}%;background:{scenario_color};"></div></div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown(
        f"<div class=\"glass\" style=\"margin-top:14px;padding:15px 18px;\"><b>🎯 Alert threshold:</b> {st.session_state.sidebar_risk_threshold}% &nbsp; • &nbsp; <b>Current scenario:</b> {scenario_level} &nbsp; • &nbsp; <b>Suggested action:</b> {get_recommended_action(scenario_level)}</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# ANALYTICS
# ============================================================

elif page == "Analytics":
    st.markdown('<div class="section-marker analytics"></div><div class="section-accent analytics"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)

    # ------------------------------------------------------------
    # LIVE ANALYTICS SUMMARY
    # ------------------------------------------------------------
    if village_results_df.empty:
        _analytics_avg = 0.0
        _analytics_top = "—"
        _analytics_max = 0.0
        _analytics_critical = 0
        _analytics_high = 0
    else:
        _analytics_avg = float(village_results_df["AI Risk (%)"].mean())
        _analytics_top_row = village_results_df.sort_values("AI Risk (%)", ascending=False).iloc[0]
        _analytics_top = str(_analytics_top_row["Village"])
        _analytics_max = float(_analytics_top_row["AI Risk (%)"])
        _analytics_critical = int((village_results_df["Alert"] == "CRITICAL").sum())
        _analytics_high = int((village_results_df["Alert"] == "HIGH").sum())

    render_live_summary(
        "Analytics",
        "The analytics engine is continuously converting village-level AI predictions into patterns, comparisons and response priorities.",
        f"Currently analysing {len(village_results_df)} monitored communities. Average AI risk is {_analytics_avg:.1f}%, while {_analytics_top} has the highest observed risk at {_analytics_max:.1f}%. The dashboard below lets you change the region, metric and risk focus to understand where attention is needed most.",
        [
            ("Communities", len(village_results_df), "currently analysed"),
            ("Average risk", f"{_analytics_avg:.1f}%", "AI probability"),
            ("Critical", _analytics_critical, "communities"),
            ("High", _analytics_high, "communities"),
        ],
    )

    st.title(f"📊 {t('Analytics')}")
    st.caption("Explore risk patterns, compare communities and identify where response resources should be focused.")

    if village_results_df.empty:
        st.warning("No village data available for analytics.")
    else:
        # --------------------------------------------------------
        # ANALYTICS CONTROL CENTER
        # --------------------------------------------------------
        st.markdown(
            """
            <div class="glass" style="padding:18px 20px;margin:8px 0 18px 0;">
                <div style="font-size:.74rem;color:#63c8ff;font-weight:800;letter-spacing:.14em;text-transform:uppercase;">ANALYTICS CONTROL CENTER</div>
                <div style="font-size:1.25rem;font-weight:850;margin-top:4px;">🎛️ Tune the analysis</div>
                <div style="color:#9fb1c4;font-size:.9rem;margin-top:5px;">Change the filters below and the charts, KPIs and priority table update with the selected scope.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns([1.05, 1.05, 1.05, 1.2])

        with c1:
            analytics_state = st.selectbox(
                "📍 Region",
                ["All Regions"] + sorted(village_results_df["State"].dropna().astype(str).unique().tolist()),
                key="analytics_state",
            )

        with c2:
            analytics_metric = st.selectbox(
                "📊 Primary metric",
                ["AI Risk (%)", "Priority Score", "Population"],
                key="analytics_metric",
            )

        with c3:
            analytics_alert = st.selectbox(
                "🚦 Alert focus",
                ["All Alerts", "CRITICAL", "HIGH", "MODERATE", "LOW"],
                key="analytics_alert",
            )

        with c4:
            analytics_min_risk = st.slider(
                "🎯 Minimum AI risk",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
                format="%d%%",
                key="analytics_min_risk",
            )

        analytics_df = village_results_df.copy()

        if analytics_state != "All Regions":
            analytics_df = analytics_df[analytics_df["State"].astype(str) == analytics_state]

        if analytics_alert != "All Alerts":
            analytics_df = analytics_df[analytics_df["Alert"] == analytics_alert]

        analytics_df = analytics_df[analytics_df["AI Risk (%)"] >= analytics_min_risk]

        # --------------------------------------------------------
        # LIVE FILTER STATUS
        # --------------------------------------------------------
        scope_text = analytics_state if analytics_state != "All Regions" else "All regions"
        alert_text = analytics_alert if analytics_alert != "All Alerts" else "All alert levels"

        if analytics_df.empty:
            st.error("No communities match the current filters. Try lowering the minimum risk or changing the alert/region filter.")
        else:
            filtered_avg = float(analytics_df["AI Risk (%)"].mean())
            filtered_max_row = analytics_df.sort_values("AI Risk (%)", ascending=False).iloc[0]
            filtered_priority = float(analytics_df["Priority Score"].mean())
            filtered_population = int(analytics_df["Population"].sum())
            filtered_critical = int((analytics_df["Alert"] == "CRITICAL").sum())
            filtered_high = int((analytics_df["Alert"] == "HIGH").sum())

            st.markdown(
                f"""
                <div class="glass" style="padding:13px 17px;margin:12px 0 16px 0;border-left:4px solid #63c8ff;">
                    <b>🔎 Current analysis scope:</b> {scope_text}
                    &nbsp; • &nbsp; <b>Alert:</b> {alert_text}
                    &nbsp; • &nbsp; <b>Risk ≥:</b> {analytics_min_risk}%
                    &nbsp; • &nbsp; <b>Communities:</b> {len(analytics_df)}
                    <div style="color:#9fb1c4;margin-top:5px;font-size:.84rem;">
                        Highest-risk community in this view: <b style="color:#ffffff;">{filtered_max_row['Village']}</b>
                        ({float(filtered_max_row['AI Risk (%)']):.1f}% AI risk). Analysis is based on the currently loaded prototype data.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ----------------------------------------------------
            # LIVE KPI CARDS
            # ----------------------------------------------------
            k1, k2, k3, k4, k5 = st.columns(5)

            with k1:
                st.metric("🏘️ In scope", len(analytics_df))
            with k2:
                st.metric("🧠 Avg AI risk", f"{filtered_avg:.1f}%")
            with k3:
                st.metric("🎯 Avg priority", f"{filtered_priority:.1f}")
            with k4:
                st.metric("🚨 Critical / High", f"{filtered_critical} / {filtered_high}")
            with k5:
                st.metric("👥 Population", f"{filtered_population:,}")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # TABBED ANALYSIS WORKSPACE
            # ----------------------------------------------------
            overview_tab, comparison_tab, alerts_tab, data_tab = st.tabs(
                ["📈 Overview", "🏘️ Community Comparison", "🚨 Alert Intelligence", "📋 Data Explorer"]
            )

            with overview_tab:
                left_chart, right_chart = st.columns(2)

                with left_chart:
                    metric_chart = analytics_df[["Village", analytics_metric]].sort_values(
                        analytics_metric, ascending=False
                    ).head(12)

                    fig = px.bar(
                        metric_chart,
                        x="Village",
                        y=analytics_metric,
                        title=f"Top Communities by {analytics_metric}",
                        labels={analytics_metric: analytics_metric, "Village": "Community"},
                    )
                    fig.update_layout(height=430, margin=dict(l=10, r=10, t=55, b=80), xaxis_tickangle=-40)
                    st.plotly_chart(fig, use_container_width=True)

                with right_chart:
                    alert_distribution = analytics_df["Alert"].value_counts().reset_index()
                    alert_distribution.columns = ["Alert Level", "Villages"]

                    fig3 = px.pie(
                        alert_distribution,
                        names="Alert Level",
                        values="Villages",
                        hole=0.48,
                        title="Current Alert Distribution",
                    )
                    fig3.update_layout(height=430, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig3, use_container_width=True)

                st.subheader("📊 Risk vs Response Priority")
                scatter = analytics_df.copy()
                scatter["Hover"] = (
                    "Community: " + scatter["Village"].astype(str)
                    + "<br>AI Risk: " + scatter["AI Risk (%)"].round(1).astype(str) + "%"
                    + "<br>Priority Score: " + scatter["Priority Score"].round(1).astype(str)
                )

                fig_scatter = px.scatter(
                    scatter,
                    x="AI Risk (%)",
                    y="Priority Score",
                    size="Population",
                    color="Alert",
                    hover_name="Village",
                    hover_data={"AI Risk (%)": True, "Priority Score": True, "Population": True, "Alert": True},
                    title="AI Risk and Response Priority Relationship",
                )
                fig_scatter.update_layout(height=480, margin=dict(l=10, r=10, t=55, b=10))
                st.plotly_chart(fig_scatter, use_container_width=True)

                st.info(
                    "💡 How to read this view: communities toward the upper-right have both higher predicted risk and higher response priority. Larger markers represent larger populations."
                )

            with comparison_tab:
                st.subheader("🏘️ Community Comparison")

                compare_cols = [
                    "Village", "State", "AI Risk (%)", "Priority Score", "Population",
                    "Alert", "Priority", "Road Connectivity", "Importance",
                ]
                compare_cols = [c for c in compare_cols if c in analytics_df.columns]

                compare_df = analytics_df[compare_cols].sort_values(
                    "AI Risk (%)", ascending=False
                ).copy()

                # Streamlit requires min_value < max_value.
                # When only 1–4 communities remain after filtering, the old
                # slider could receive min_value=5 and max_value=1/4.
                # Keep the control valid for every dataset/filter combination.
                available_communities = len(compare_df)

                if available_communities <= 0:
                    st.info("No communities match the current Analytics filters.")
                    top_compare = compare_df.copy()
                else:
                    max_top_n = max(1, min(25, available_communities))

                    if max_top_n == 1:
                        top_n = 1
                        st.caption("Showing the only community that matches the current filters.")
                    else:
                        top_n = st.slider(
                            "Show top communities",
                            min_value=1,
                            max_value=max_top_n,
                            value=min(10, max_top_n),
                            step=1,
                            key="analytics_top_n",
                        )

                    top_compare = compare_df.head(top_n)

                left, right = st.columns(2)
                with left:
                    fig_risk = px.bar(
                        top_compare.sort_values("AI Risk (%)"),
                        x="AI Risk (%)",
                        y="Village",
                        orientation="h",
                        title="AI Risk Ranking",
                    )
                    fig_risk.update_layout(height=500, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig_risk, use_container_width=True)

                with right:
                    fig_priority = px.bar(
                        top_compare.sort_values("Priority Score"),
                        x="Priority Score",
                        y="Village",
                        orientation="h",
                        title="Response Priority Ranking",
                    )
                    fig_priority.update_layout(height=500, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig_priority, use_container_width=True)

                st.markdown("#### 🏆 Highest-priority communities")
                st.dataframe(
                    top_compare,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "AI Risk (%)": st.column_config.ProgressColumn(
                            "AI Risk (%)", min_value=0, max_value=100, format="%.1f%%"
                        ),
                        "Priority Score": st.column_config.ProgressColumn(
                            "Priority Score", min_value=0, max_value=100, format="%.1f"
                        ),
                    },
                )

            with alerts_tab:
                st.subheader("🚨 Alert Intelligence")

                a1, a2, a3, a4 = st.columns(4)
                with a1:
                    st.metric("🚨 Critical", filtered_critical)
                with a2:
                    st.metric("⚠️ High", filtered_high)
                with a3:
                    moderate_count = int((analytics_df["Alert"] == "MODERATE").sum())
                    st.metric("🟠 Moderate", moderate_count)
                with a4:
                    low_count = int((analytics_df["Alert"] == "LOW").sum())
                    st.metric("🟢 Low", low_count)

                alert_table = (
                    analytics_df.groupby("Alert", dropna=False)
                    .agg(
                        Communities=("Village", "count"),
                        Avg_Risk=("AI Risk (%)", "mean"),
                        Avg_Priority=("Priority Score", "mean"),
                        Population=("Population", "sum"),
                    )
                    .reset_index()
                    .rename(columns={"Avg_Risk": "Average AI Risk", "Avg_Priority": "Average Priority"})
                    .sort_values("Average AI Risk", ascending=False)
                )

                alert_left, alert_right = st.columns(2)
                with alert_left:
                    fig_alert_risk = px.bar(
                        alert_table,
                        x="Alert",
                        y="Average AI Risk",
                        title="Average AI Risk by Alert Level",
                    )
                    fig_alert_risk.update_layout(height=400, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig_alert_risk, use_container_width=True)

                with alert_right:
                    fig_alert_pop = px.bar(
                        alert_table,
                        x="Alert",
                        y="Population",
                        title="Population Exposure by Alert Level",
                    )
                    fig_alert_pop.update_layout(height=400, margin=dict(l=10, r=10, t=55, b=10))
                    st.plotly_chart(fig_alert_pop, use_container_width=True)

                st.markdown("#### 🧭 Communities requiring the most attention")
                response_cols = [
                    "Village", "State", "AI Risk (%)", "Alert", "Priority",
                    "Priority Score", "Population", "Recommended Action", "Nearest Hospital",
                ]
                response_cols = [c for c in response_cols if c in analytics_df.columns]
                response_df = analytics_df.sort_values(
                    ["Priority Score", "AI Risk (%)"], ascending=False
                )[response_cols].head(15)
                st.dataframe(response_df, use_container_width=True, hide_index=True)

            with data_tab:
                st.subheader("📋 Data Explorer")
                st.caption("Use this view to inspect the filtered records behind the visualisations.")

                search_term = st.text_input(
                    "🔎 Search community or state",
                    placeholder="Type a village or state name...",
                    key="analytics_search",
                )

                explorer_df = analytics_df.copy()
                if search_term.strip():
                    mask = (
                        explorer_df["Village"].astype(str).str.contains(search_term, case=False, na=False)
                        | explorer_df["State"].astype(str).str.contains(search_term, case=False, na=False)
                    )
                    explorer_df = explorer_df[mask]

                st.markdown(
                    f"**{len(explorer_df)}** record(s) match the current analysis filters and search."
                )

                st.dataframe(
                    explorer_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "AI Risk (%)": st.column_config.ProgressColumn(
                            "AI Risk (%)", min_value=0, max_value=100, format="%.1f%%"
                        ),
                        "Priority Score": st.column_config.ProgressColumn(
                            "Priority Score", min_value=0, max_value=100, format="%.1f"
                        ),
                    },
                )

                csv_data = explorer_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Export filtered analytics CSV",
                    data=csv_data,
                    file_name="ner_landslide_analytics.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            # ----------------------------------------------------
            # ANALYTICS FOOTER / REFRESH STATUS
            # ----------------------------------------------------
            st.markdown(
                f"""
                <div class="glass" style="margin-top:18px;padding:14px 18px;text-align:center;">
                    <span style="color:#63c8ff;font-weight:800;">📡 ANALYTICS STATUS: LIVE</span>
                    &nbsp; • &nbsp; {len(analytics_df)} communities in current scope
                    &nbsp; • &nbsp; Minimum risk {analytics_min_risk}%
                    &nbsp; • &nbsp; Primary metric: {analytics_metric}
                    &nbsp; • &nbsp; Updated on app refresh
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# INCIDENT REPORTING
# ============================================================

elif page == "Incident Reporting":
    st.markdown('<div class="section-marker incidents"></div><div class="section-accent incidents"></div>', unsafe_allow_html=True)
    render_module_info(page, compact=st.session_state.compact_mode)
    _incident_df_summary = load_incidents(include_photo=False)
    _incident_count = len(_incident_df_summary)
    _latest_incident = "No reports yet"
    if not _incident_df_summary.empty and "reported_at" in _incident_df_summary.columns:
        _latest_incident = str(_incident_df_summary.iloc[0]["reported_at"])
    render_live_summary(
        "Incident Reporting",
        "Verify field alarms before emergency dispatch.",
        "Incident reports are checked against camera evidence and nearby AI risk. Verified high-priority incidents are placed into a response queue for medical, police, fire and rescue teams.",
        [("Stored reports", _incident_count, "field incidents"), ("Latest report", _latest_incident, "recorded time"), ("AI risk", f"{live_probability:.1f}%", live_risk_level), ("Camera check", "READY", "evidence workflow")],
    )
    st.title(f"📸 {t('Incident Reporting')}")
    st.markdown(
        """<div class="glass" style="padding:16px 18px;border-left:4px solid #f59e0b;">
            <b>🚨 Automated incident-response workflow</b><br>
            <span style="color:#ffd9b0;">Report → Camera evidence → AI-assisted verification → Emergency notification queue → Response teams</span>
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption("Prototype note: the camera verifier is evidence-assisted triage. Production deployment should connect authenticated CCTV/IP cameras and a trained landslide-vision model.")

    left, right = st.columns([1.05, 0.95])
    with left:
        st.subheader("📝 New Incident Report")
        uploaded_photo = st.file_uploader("📷 Upload landslide photo (optional)", type=["jpg", "jpeg", "png", "webp"])
        st.markdown("**📹 Live Camera Verification**")
        camera_photo = st.camera_input("Capture camera evidence", help="Use a connected webcam/phone camera to capture evidence for incident verification.")
        if camera_photo is not None:
            st.image(camera_photo, caption="Live camera evidence", use_container_width=True)
        elif uploaded_photo is not None:
            st.image(uploaded_photo, caption="Uploaded incident evidence", use_container_width=True)

        r1, r2 = st.columns(2)
        with r1:
            latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=27.58600, format="%.6f")
        with r2:
            longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=91.85900, format="%.6f")
        r3, r4 = st.columns(2)
        with r3:
            severity = st.selectbox("⚠️ Severity", ["Low", "Moderate", "High", "Critical"], index=2)
        with r4:
            road_blocked = st.selectbox("🛣️ Road blocked?", ["No", "Yes"])
        village_options = ["Not specified"]
        if not village_df.empty and "village" in village_df.columns:
            village_options += village_df["village"].dropna().astype(str).tolist()
        village = st.selectbox("🏘️ Affected village / area", village_options)
        description = st.text_area("📝 Incident description", placeholder="Describe visible cracks, debris flow, damaged houses, road condition, etc.", height=120)

        submit = st.button("🚨 Verify & Submit Incident", type="primary", use_container_width=True)
        if submit:
            if not description.strip():
                st.warning("Please add a short incident description.")
            else:
                evidence = camera_photo if camera_photo is not None else uploaded_photo
                camera_present = camera_photo is not None
                verification_status, verification_confidence, nearby_risk = verify_incident_evidence(description, severity, latitude, longitude, evidence is not None)
                high_priority = severity in ["High", "Critical"] or nearby_risk >= st.session_state.sidebar_risk_threshold
                verified_for_dispatch = evidence is not None and verification_confidence >= 70 and high_priority
                notification_status = "QUEUED — MEDICAL / POLICE / FIRE / RESCUE" if verified_for_dispatch else "NOT SENT — HUMAN REVIEW REQUIRED"
                photo_name = evidence.name if evidence is not None else ""
                photo_data = evidence.getvalue() if evidence is not None else None
                save_incident(
                    latitude, longitude, severity, road_blocked, village, description.strip(),
                    photo_name, photo_data, verification_status, verification_confidence,
                    "LIVE CAMERA" if camera_present else ("UPLOAD" if evidence is not None else "NONE"),
                    notification_status,
                )
                if verified_for_dispatch:
                    st.session_state.last_incident_dispatch = {"status": verification_status, "confidence": verification_confidence, "risk": nearby_risk, "location": f"{latitude:.5f}, {longitude:.5f}"}
                    st.success("🚨 Incident verified for response. Medical, police, fire and rescue notification queue has been activated.")
                elif evidence is None:
                    st.warning("⚠️ Report stored, but it is UNVERIFIED. Capture camera evidence before dispatching emergency teams.")
                else:
                    st.info(f"🔎 Report stored for human review. Verification confidence: {verification_confidence:.1f}%. Nearby AI risk: {nearby_risk:.1f}%.")
                st.rerun()

    with right:
        st.subheader("📡 Camera & Response Center")
        st.markdown(
            """<div class="glass" style="padding:15px;">
                <b>Camera status</b><br>
                🟢 Browser camera: <b>AVAILABLE</b><br>
                🟡 Remote CCTV/IP camera: <b>INTEGRATION READY</b><br>
                <span style="font-size:.78rem;color:#b9c9d8;">For production, connect an authenticated RTSP/IP camera feed to a vision model. This demo uses camera evidence captured in the browser.</span>
            </div>""",
            unsafe_allow_html=True,
        )
        if "last_incident_dispatch" in st.session_state:
            dispatch = st.session_state.last_incident_dispatch
            st.subheader("🚨 Emergency Notification Queue")
            st.success("Response queue ACTIVE")
            st.write(f"**Verification:** {dispatch['status']}")
            st.write(f"**Confidence:** {dispatch['confidence']:.1f}%")
            st.write(f"**Nearby AI risk:** {dispatch['risk']:.1f}%")
            st.write(f"**Location:** {dispatch['location']}")
            for service in ["🏥 Medical / Ambulance", "👮 Police", "🚒 Fire Department", "🛟 Rescue / SDRF Team"]:
                st.markdown(f"✅ **{service}** — notification queued")
            st.caption("Actual SMS/call/radio dispatch requires the relevant emergency-service API or control-room integration.")
        else:
            st.info("Submit an incident with camera evidence to start the verification and emergency-response workflow.")

        st.subheader("📊 Incident Summary")
        incidents = load_incidents()
        if incidents.empty:
            st.info("No field incidents have been reported yet.")
        else:
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                st.metric("Total Reports", len(incidents))
            with ic2:
                st.metric("High / Critical", len(incidents[incidents["severity"].isin(["High", "Critical"])]))
            with ic3:
                verified_count = int(incidents["verification_status"].fillna("").astype(str).str.contains("LIKELY TRUE").sum()) if "verification_status" in incidents.columns else 0
                st.metric("Verified", verified_count)
            urgent = incidents[incidents["severity"].isin(["Critical", "High"])]
            if urgent.empty:
                st.success("No High or Critical field reports.")
            else:
                st.subheader("🚨 Recent Critical / High Reports")
                for _, incident in urgent.head(5).iterrows():
                    box = st.error if incident["severity"] == "Critical" else st.warning
                    verification = incident.get("verification_status", "UNVERIFIED")
                    box(f"**{incident['severity']} — {incident.get('village') or 'Unknown area'}**\n\n{incident.get('description') or 'No description'}\n\n📍 {float(incident['latitude']):.5f}, {float(incident['longitude']):.5f}\n\n🛣️ Road blocked: {incident['road_blocked']}\n\n🔎 {verification}")

    st.markdown("---")
    st.subheader("📋 Incident Register")
    incidents = load_incidents()
    if incidents.empty:
        st.caption("Submitted reports will appear here.")
    else:
        display_incidents = incidents.rename(columns={
            "id": "ID", "reported_at": "Reported At", "latitude": "Latitude", "longitude": "Longitude",
            "severity": "Severity", "road_blocked": "Road Blocked", "village": "Village / Area", "description": "Description", "photo_name": "Photo",
            "verification_status": "Verification", "verification_confidence": "Confidence %", "camera_source": "Camera Source", "notification_status": "Notification Status",
        })
        st.dataframe(display_incidents, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download Incident Register", data=display_incidents.to_csv(index=False), file_name="NER_landslide_incident_register.csv", mime="text/csv")


# ============================================================
# REPORTS
# ============================================================

elif page == "Reports":
    st.markdown('<div class="section-marker reports"></div><div class="section-accent reports"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)
    _report_avg = float(village_results_df["AI Risk (%)"].mean()) if not village_results_df.empty else 0
    _report_critical = int((village_results_df["Alert"] == "CRITICAL").sum()) if not village_results_df.empty else 0
    _report_high = int((village_results_df["Alert"] == "HIGH").sum()) if not village_results_df.empty else 0
    render_live_summary(
        "Reports",
        "Report data is ready to be filtered, reviewed and exported.",
        f"The reporting engine currently has {len(village_results_df)} community records. Average AI risk is {_report_avg:.1f}%, with {_report_critical} critical and {_report_high} high alerts. Report filters below will update the displayed evidence and export files.",
        [("Records", len(village_results_df), "community records"), ("Critical", _report_critical, "alerts"), ("High", _report_high, "alerts"), ("Average risk", f"{_report_avg:.1f}%", "AI probability")],
    )

    st.markdown(
        """
        <div class="reports-hero">
            <div class="reports-kicker">INTELLIGENCE & EXPORT CENTER • SIH PROTOTYPE</div>
            <div class="reports-title">📄 Monitoring Reports</div>
            <div class="reports-subtitle">
                Turn live village-risk data into focused operational summaries, response priorities
                and presentation-ready monitoring reports.
            </div>
            <div class="reports-live"><span class="reports-dot"></span> Report engine ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if village_results_df.empty:
        st.warning("No village data available to generate a report.")
    else:
        # --------------------------------------------------------
        # REPORT FILTERS
        # --------------------------------------------------------
        st.markdown('<div class="reports-section">🎛️ Report Builder</div>', unsafe_allow_html=True)
        st.caption("Use the controls below to build a focused monitoring report. Results update instantly.")

        states = sorted(
            village_results_df["State"].dropna().astype(str).unique().tolist()
        )
        alert_options = ["All Alerts", "CRITICAL", "HIGH", "MODERATE", "LOW"]
        priority_options = ["All Priorities", "PRIORITY 1", "PRIORITY 2", "PRIORITY 3"]

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            report_state = st.selectbox(
                "📍 Region",
                ["All Regions"] + states,
                key="report_state",
            )
        with f2:
            report_alert = st.selectbox(
                "🚨 Alert level",
                alert_options,
                key="report_alert",
            )
        with f3:
            report_priority = st.selectbox(
                "🎯 Response priority",
                priority_options,
                key="report_priority",
            )
        with f4:
            report_min_risk = st.slider(
                "📈 Minimum AI risk",
                0,
                100,
                0,
                5,
                key="report_min_risk",
            )

        report_source = village_results_df.copy()
        if report_state != "All Regions":
            report_source = report_source[report_source["State"].astype(str) == report_state]
        if report_alert != "All Alerts":
            report_source = report_source[report_source["Alert"] == report_alert]
        if report_priority != "All Priorities":
            report_source = report_source[report_source["Priority"] == report_priority]
        report_source = report_source[report_source["AI Risk (%)"] >= report_min_risk]

        report = report_source[
            [
                "Village",
                "State",
                "Population",
                "AI Risk (%)",
                "Risk Level",
                "Priority",
                "Priority Score",
                "Alert",
                "Recommended Action",
            ]
        ].sort_values("Priority Score", ascending=False).reset_index(drop=True)

        # --------------------------------------------------------
        # LIVE REPORT SUMMARY
        # --------------------------------------------------------
        total = len(report)
        critical = int((report["Alert"] == "CRITICAL").sum()) if total else 0
        high = int((report["Alert"] == "HIGH").sum()) if total else 0
        moderate = int((report["Alert"] == "MODERATE").sum()) if total else 0
        low = int((report["Alert"] == "LOW").sum()) if total else 0
        exposed_population = int(report["Population"].sum()) if total else 0
        avg_risk = float(report["AI Risk (%)"].mean()) if total else 0.0
        avg_priority = float(report["Priority Score"].mean()) if total else 0.0

        st.markdown(
            f'<div class="report-scope"><b>ACTIVE SCOPE</b> &nbsp; {report_state} &nbsp;•&nbsp; '
            f'{report_alert} &nbsp;•&nbsp; {report_priority} &nbsp;•&nbsp; AI risk ≥ {report_min_risk}% '
            f'<span class="report-scope-count">{total} communities</span></div>',
            unsafe_allow_html=True,
        )

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f'<div class="report-kpi red"><div class="report-kpi-label">Critical</div><div class="report-kpi-value">{critical}</div><div class="report-kpi-note">Immediate attention</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="report-kpi orange"><div class="report-kpi-label">High</div><div class="report-kpi-value">{high}</div><div class="report-kpi-note">Priority response</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="report-kpi cyan"><div class="report-kpi-label">Avg AI Risk</div><div class="report-kpi-value">{avg_risk:.1f}%</div><div class="report-kpi-note">Filtered communities</div></div>', unsafe_allow_html=True)
        with k4:
            st.markdown(f'<div class="report-kpi purple"><div class="report-kpi-label">Avg Priority</div><div class="report-kpi-value">{avg_priority:.1f}</div><div class="report-kpi-note">Response score</div></div>', unsafe_allow_html=True)
        with k5:
            st.markdown(f'<div class="report-kpi green"><div class="report-kpi-label">Population Exposed</div><div class="report-kpi-value">{exposed_population:,}</div><div class="report-kpi-note">Across report scope</div></div>', unsafe_allow_html=True)

        if report.empty:
            st.info("No communities match the selected report filters. Try lowering the minimum AI risk or widening the alert/priority filters.")
        else:
            # ----------------------------------------------------
            # TABS: OVERVIEW / TABLE / RESPONSE
            # ----------------------------------------------------
            tab_overview, tab_table, tab_response = st.tabs([
                "📊 Overview",
                "📋 Detailed Report",
                "🚨 Response Priorities",
            ])

            with tab_overview:
                c1, c2 = st.columns(2, gap="large")

                with c1:
                    alert_counts = pd.DataFrame({
                        "Alert": ["CRITICAL", "HIGH", "MODERATE", "LOW"],
                        "Communities": [critical, high, moderate, low],
                    })
                    fig_alert = px.bar(
                        alert_counts,
                        x="Alert",
                        y="Communities",
                        text="Communities",
                        title="Warning Distribution",
                    )
                    fig_alert.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=10, r=10, t=55, b=10),
                        showlegend=False,
                        height=330,
                    )
                    st.plotly_chart(fig_alert, use_container_width=True)

                with c2:
                    risk_chart = report[["Village", "AI Risk (%)"]].copy()
                    risk_chart = risk_chart.sort_values("AI Risk (%)", ascending=False).head(10)
                    fig_risk = px.bar(
                        risk_chart.sort_values("AI Risk (%)"),
                        x="AI Risk (%)",
                        y="Village",
                        orientation="h",
                        text="AI Risk (%)",
                        title="Top 10 AI Risk Communities",
                    )
                    fig_risk.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=10, r=10, t=55, b=10),
                        height=330,
                    )
                    fig_risk.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                    st.plotly_chart(fig_risk, use_container_width=True)

                st.markdown('<div class="reports-section">📡 Monitoring Snapshot</div>', unsafe_allow_html=True)
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown(
                        f'<div class="report-insight"><div class="report-insight-icon">🚨</div><b>Warning concentration</b><p>{critical + high} communities are currently in Critical/High alert within this report scope.</p></div>',
                        unsafe_allow_html=True,
                    )
                with s2:
                    top_village = str(report.iloc[0]["Village"])
                    top_score = float(report.iloc[0]["Priority Score"])
                    st.markdown(
                        f'<div class="report-insight"><div class="report-insight-icon">🎯</div><b>Highest response priority</b><p><strong>{top_village}</strong> leads the filtered report with a priority score of <strong>{top_score:.1f}</strong>.</p></div>',
                        unsafe_allow_html=True,
                    )
                with s3:
                    st.markdown(
                        f'<div class="report-insight"><div class="report-insight-icon">🏘️</div><b>Population exposure</b><p>The filtered communities represent an estimated monitored population of <strong>{exposed_population:,}</strong>.</p></div>',
                        unsafe_allow_html=True,
                    )

            with tab_table:
                st.markdown('<div class="reports-section">📋 Decision-Ready Community Report</div>', unsafe_allow_html=True)
                st.dataframe(
                    report,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "AI Risk (%)": st.column_config.ProgressColumn(
                            "AI Risk (%)",
                            min_value=0,
                            max_value=100,
                            format="%.1f%%",
                        ),
                        "Priority Score": st.column_config.ProgressColumn(
                            "Priority Score",
                            min_value=0,
                            max_value=100,
                            format="%.1f",
                        ),
                    },
                    height=430,
                )

                st.markdown('<div class="reports-section">⬇️ Export Center</div>', unsafe_allow_html=True)
                e1, e2, e3 = st.columns(3)
                report_csv = report.to_csv(index=False)
                report_txt = (
                    "NER LANDSLIDE EARLY WARNING REPORT\n"
                    "=================================\n"
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Region: {report_state}\n"
                    f"Alert filter: {report_alert}\n"
                    f"Priority filter: {report_priority}\n"
                    f"Minimum AI risk: {report_min_risk}%\n\n"
                    f"Communities: {total}\n"
                    f"Critical: {critical}\n"
                    f"High: {high}\n"
                    f"Moderate: {moderate}\n"
                    f"Low: {low}\n"
                    f"Average AI risk: {avg_risk:.1f}%\n"
                    f"Average priority score: {avg_priority:.1f}\n"
                    f"Population exposed: {exposed_population:,}\n"
                )
                with e1:
                    st.download_button(
                        "⬇️ Download CSV",
                        data=report_csv,
                        file_name="NER_landslide_early_warning_report.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with e2:
                    st.download_button(
                        "📄 Download Summary",
                        data=report_txt,
                        file_name="NER_landslide_report_summary.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with e3:
                    st.download_button(
                        "📊 Download Full Data",
                        data=village_results_df.to_csv(index=False),
                        file_name="NER_complete_village_monitoring_data.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            with tab_response:
                st.markdown('<div class="reports-section">🚨 Recommended Response Queue</div>', unsafe_allow_html=True)
                response = report[
                    ["Village", "State", "AI Risk (%)", "Priority", "Priority Score", "Alert", "Recommended Action"]
                ].copy()
                response["Rank"] = range(1, len(response) + 1)
                response = response[["Rank", "Village", "State", "AI Risk (%)", "Priority", "Priority Score", "Alert", "Recommended Action"]]
                st.dataframe(
                    response,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("#", width="small"),
                        "AI Risk (%)": st.column_config.ProgressColumn("AI Risk (%)", min_value=0, max_value=100, format="%.1f%%"),
                        "Priority Score": st.column_config.ProgressColumn("Priority Score", min_value=0, max_value=100, format="%.1f"),
                    },
                    height=430,
                )

                st.markdown('<div class="report-action-banner"><b>⚡ Operational focus</b><br><span>Start with Priority 1 communities, then review Critical/High alerts and recommended actions before field deployment.</span></div>', unsafe_allow_html=True)

            # ----------------------------------------------------
            # EXECUTIVE SUMMARY
            # ----------------------------------------------------
            st.markdown('<div class="reports-section">📌 Executive Summary</div>', unsafe_allow_html=True)
            summary_left, summary_right = st.columns([1.7, 1], gap="large")
            with summary_left:
                st.markdown(
                    f"""
                    <div class="executive-card">
                        <div class="executive-label">AUTOMATED REPORT NARRATIVE</div>
                        <div class="executive-title">Current monitoring situation</div>
                        <p>
                            The current filtered monitoring scope contains <strong>{total}</strong> communities,
                            including <strong>{critical} critical</strong> and <strong>{high} high</strong> alerts.
                            The average AI risk is <strong>{avg_risk:.1f}%</strong>, while the average response-priority
                            score is <strong>{avg_priority:.1f}</strong>.
                        </p>
                        <p>
                            Recommended actions shown in this report are decision-support outputs for the SIH prototype
                            and should be validated against authoritative field observations before operational use.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with summary_right:
                st.markdown('<div class="executive-card compact">', unsafe_allow_html=True)
                st.markdown('<div class="executive-label">REPORT METADATA</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metadata-row"><span>Generated</span><b>{datetime.now().strftime("%d %b %Y, %H:%M")}</b></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metadata-row"><span>Communities</span><b>{total}</b></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metadata-row"><span>Region</span><b>{report_state}</b></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metadata-row"><span>Risk threshold</span><b>{report_min_risk}%</b></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":
    st.markdown('<div class="section-marker settings"></div><div class="section-accent settings"></div>', unsafe_allow_html=True)

    render_module_info(page, compact=st.session_state.compact_mode)

    defaults = {
        "sms_alerts": True,
        "mobile_alerts": True,
        "dashboard_alerts": True,
        "priority_ai_weight": 40,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown('<div class="settings-section">🌐 {}</div>'.format(t("Language")), unsafe_allow_html=True)
    st.caption(t("Select interface language"))
    current_language_name = next((name for name, code in LANGUAGE_OPTIONS.items() if code == st.session_state.language), "English")
    selected_language_name = st.selectbox(
        t("Language"),
        list(LANGUAGE_OPTIONS.keys()),
        index=list(LANGUAGE_OPTIONS.keys()).index(current_language_name),
        key="settings_language",
        label_visibility="collapsed",
    )
    selected_language_code = LANGUAGE_OPTIONS[selected_language_name]

    # Keep an explicit "Add Language" option for future expansion.
    # It opens a small interactive panel without breaking the current language.
    if selected_language_code == "add":
        st.info(
            "🌐 Choose an additional supported language below. "
            "Your current interface language will remain active until you select one."
        )
        extra_language_options = {
            "Kokborok (Tripura)": "trp",
            "Karbi (Assam)": "mjw",
            "Ao (Nagaland)": "njo",
            "Angami (Nagaland)": "nag",
            "Hmar (Mizoram/Manipur)": "hmr",
            "Adi (Arunachal Pradesh)": "adi",
        }
        add_language_name = st.selectbox(
            "Additional language",
            list(extra_language_options.keys()),
            key="additional_language_choice",
        )
        if st.button("➕ Add selected language", key="add_selected_language_btn"):
            LANGUAGE_OPTIONS[add_language_name] = extra_language_options[add_language_name]
            st.session_state.language = extra_language_options[add_language_name]
            st.session_state.settings_language = add_language_name
            st.rerun()
    elif selected_language_code != st.session_state.language:
        st.session_state.language = selected_language_code
        st.rerun()

    active_channels = sum([
        bool(st.session_state.sms_alerts),
        bool(st.session_state.mobile_alerts),
        bool(st.session_state.dashboard_alerts),
    ])
    system_state = "Monitoring configuration active" if active_channels else "All notification channels disabled"

    render_live_summary(
        "Settings",
        "The control center is keeping alert and prioritization behavior visible.",
        f"{active_channels} of 3 notification channels are enabled. The AI priority contribution is set to {st.session_state.priority_ai_weight}%. Changes in this section affect the current prototype session and are reflected immediately in the interface.",
        [("Channels", f"{active_channels}/3", "notifications enabled"), (t("AI weight"), f"{st.session_state.priority_ai_weight}%", "priority contribution"), ("Monitoring", "ON" if st.session_state.live_monitoring else "OFF", "live mode"), ("Model", "ONLINE" if model is not None else "FALLBACK", "risk engine")],
        "CONFIGURATION • ACTIVE" if active_channels else "CONFIGURATION • REVIEW",
    )

    st.markdown(
        f"""
        <div class="settings-hero">
            <div class="settings-kicker">CONTROL CENTER • SIH PROTOTYPE</div>
            <div class="settings-title">⚙️ {t("System Settings")}</div>
            <div class="settings-subtitle">
                Configure how the NER early-warning prototype presents alerts and prioritizes
                communities. Changes are applied instantly to this session.
            </div>
            <div class="settings-status"><span class="settings-status-dot"></span>{system_state}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown(f'<div class="settings-mini"><div class="settings-mini-label">{t("Alert channels")}</div><div class="settings-mini-value">{active_channels}/3</div></div>', unsafe_allow_html=True)
    with q2:
        st.markdown(f'<div class="settings-mini"><div class="settings-mini-label">{t("AI weight")}</div><div class="settings-mini-value">{st.session_state.priority_ai_weight}%</div></div>', unsafe_allow_html=True)
    with q3:
        st.markdown(f'<div class="settings-mini"><div class="settings-mini-label">{t("Villages")}</div><div class="settings-mini-value">{len(village_df):,}</div></div>', unsafe_allow_html=True)
    with q4:
        model_label = "Loaded" if model is not None else "Fallback"
        st.markdown(f'<div class="settings-mini"><div class="settings-mini-label">{t("AI engine")}</div><div class="settings-mini-value">{model_label}</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="settings-section">🔔 {t("Notification Control")}</div>', unsafe_allow_html=True)
    st.caption("Choose where prototype warning notifications should appear. These controls do not send real messages in prototype mode.")

    n1, n2, n3 = st.columns(3)
    with n1:
        st.markdown('<div class="settings-card"><div class="settings-card-icon">📱</div><div class="settings-card-title">SMS Alerts</div><div class="settings-card-desc">Prepare high-priority warning notifications for field response teams.</div></div>', unsafe_allow_html=True)
        st.session_state.sms_alerts = st.toggle(t("Enable SMS channel"), value=st.session_state.sms_alerts, key="settings_sms")
    with n2:
        st.markdown('<div class="settings-card"><div class="settings-card-icon">🔔</div><div class="settings-card-title">Mobile Notifications</div><div class="settings-card-desc">Keep app users informed when risk levels or priorities change.</div></div>', unsafe_allow_html=True)
        st.session_state.mobile_alerts = st.toggle(t("Enable mobile channel"), value=st.session_state.mobile_alerts, key="settings_mobile")
    with n3:
        st.markdown('<div class="settings-card"><div class="settings-card-icon">🖥️</div><div class="settings-card-title">Dashboard Alerts</div><div class="settings-card-desc">Show warning states directly inside the command-center dashboard.</div></div>', unsafe_allow_html=True)
        st.session_state.dashboard_alerts = st.toggle(t("Enable dashboard channel"), value=st.session_state.dashboard_alerts, key="settings_dashboard")

    active_channels = sum([
        bool(st.session_state.sms_alerts),
        bool(st.session_state.mobile_alerts),
        bool(st.session_state.dashboard_alerts),
    ])
    if active_channels == 3:
        st.success("All notification channels are active for this prototype session.")
    elif active_channels == 0:
        st.warning("All notification channels are disabled. No prototype warning channel is currently selected.")
    else:
        st.info(f"{active_channels} of 3 notification channels are active.")

    st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="settings-section">🧠 {t("AI-Assisted Priority Weights")}</div>', unsafe_allow_html=True)
    st.caption("Adjust how strongly the AI landslide-risk score influences community response priority.")

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown('<div class="weight-panel">', unsafe_allow_html=True)
        st.markdown('<span class="weight-badge">LIVE WEIGHT CONFIGURATION</span>', unsafe_allow_html=True)
        st.session_state.priority_ai_weight = st.slider(
            t("AI Landslide Risk Weight"),
            min_value=20,
            max_value=70,
            value=int(st.session_state.priority_ai_weight),
            step=5,
            key="settings_ai_weight",
        )
        remaining = 100 - st.session_state.priority_ai_weight
        st.markdown(f'<div class="settings-card-desc">AI contributes <b>{st.session_state.priority_ai_weight}%</b> of the priority score. The remaining <b>{remaining}%</b> is distributed across population exposure, road connectivity and community importance.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    ai_weight = st.session_state.priority_ai_weight
    secondary_weight = round((100 - ai_weight) / 3, 1)
    weight_df = pd.DataFrame({
        "Factor": ["AI Landslide Risk", "Population Exposure", "Road Connectivity", "Community Importance"],
        "Weight": [f"{ai_weight}%", f"{secondary_weight}%", f"{secondary_weight}%", f"{secondary_weight}%"],
    })

    with right:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        st.markdown('<div class="preview-label">Current configuration</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="preview-value">{ai_weight}% AI</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="settings-card-desc">{secondary_weight}% each for the three supporting factors.</div>', unsafe_allow_html=True)
        st.progress(ai_weight / 100, text=f"AI influence: {ai_weight}%")
        st.markdown('</div>', unsafe_allow_html=True)

    st.dataframe(weight_df, use_container_width=True, hide_index=True)

    if ai_weight >= 55:
        st.warning("AI-heavy configuration: predictions have a stronger influence on response priority.")
    elif ai_weight <= 30:
        st.info("Balanced community-first configuration: contextual factors have more influence than the AI score.")
    else:
        st.success("Balanced AI-assisted prioritization is active.")

    st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="settings-section">🛰️ System Information</div>', unsafe_allow_html=True)
    i1, i2 = st.columns(2, gap="large")
    with i1:
        info = {
            "Application": "NER Landslide Early Warning System",
            "Mode": "SIH Prototype",
            "AI Model": "Loaded" if model is not None else "Fallback risk engine",
            "Risk Locations": len(risk_df),
            "Villages": len(village_df),
            "Roads": len(road_df),
            "Infrastructure Points": len(infra_df),
        }
        st.json(info)
    with i2:
        st.markdown(f"""
        <div class="preview-card">
            <div class="preview-label">Prototype readiness</div>
            <h3 style="margin:6px 0 12px;">🟢 Configuration online</h3>
            <p style="color:#9fb1c4;font-size:.84rem;line-height:1.55;">
                Notification preferences and AI priority settings are stored in the current
                Streamlit session. The system can be connected to authorized messaging,
                sensor and weather services for production deployment.
            </p>
            <div class="settings-mini" style="margin-top:12px;">
                <div class="settings-mini-label">Current mode</div>
                <div style="font-weight:850;margin-top:4px;">{t("SIH Demonstration Prototype")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)
    if st.button(t("Reset settings to default"), use_container_width=False):
        st.session_state.sms_alerts = defaults["sms_alerts"]
        st.session_state.mobile_alerts = defaults["mobile_alerts"]
        st.session_state.dashboard_alerts = defaults["dashboard_alerts"]
        st.session_state.priority_ai_weight = defaults["priority_ai_weight"]
        st.rerun()

    st.warning(
        "Prototype notice: this is a decision-support demonstration. Production deployment requires validated models, "
        "authoritative sensor/weather data, secure notification services, security controls and approval from relevant "
        "disaster-management authorities."
    )
