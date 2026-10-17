import os, json, tempfile, subprocess, pickle
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

load_dotenv()
st.set_page_config(page_title="YouTube Shorts Agent", page_icon="🎬")
st.title("🎬 YouTube Shorts Automation Agent")
st.caption("OpenRouter AI → original script → voice-over → MP4 → YouTube upload")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def ai_client():
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key: raise ValueError("OPENROUTER_API_KEY missing. Add it to your .env file.")
    return OpenAI(
        api_key=key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "YouTube Shorts Automation Agent"),
        },
    )

def ask_json(prompt, model=None):
    c = ai_client()
    response = c.chat.completions.create(
        model=model or os.getenv("OPENROUTER_MODEL", "openrouter/free"),
        messages=[
            {"role":"system","content":"You create original, factual YouTube Shorts content. Never claim you checked live trends unless given current sources. Return valid JSON only."},
            {"role":"user","content":prompt}],
        response_format={"type":"json_object"}, temperature=0.65)
    return json.loads(response.choices[0].message.content)

def get_youtube():
    creds=None
    if os.path.exists("token.pickle"):
        with open("token.pickle","rb") as f: creds=pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            if not os.path.exists("client_secret.json"):
                raise FileNotFoundError("client_secret.json is missing. Follow README setup.")
            flow=InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds=flow.run_local_server(port=0)
        with open("token.pickle","wb") as f: pickle.dump(creds,f)
    return build("youtube","v3",credentials=creds)

def create_video(pkg, language):
    out=os.path.abspath("output_shorts.mp4")
    with tempfile.TemporaryDirectory() as td:
        audio=os.path.join(td,"voice.mp3"); frame=os.path.join(td,"frame.png")
        lang={"English":"en","Urdu":"ur","Hindi":"hi"}[language]
        gTTS(text=pkg["script"],lang=lang).save(audio)
        im=Image.new("RGB",(1080,1920),(15,28,55)); d=ImageDraw.Draw(im)
        try: font=ImageFont.truetype("arial.ttf",76)
        except: font=ImageFont.load_default()
        words=pkg["title"].split(); lines=[]; line=""
        for word in words:
            if len((line+" "+word).strip())>18 and line: lines.append(line); line=word
            else: line=(line+" "+word).strip()
        if line: lines.append(line)
        y=620
        for ln in lines[:8]:
            box=d.textbbox((0,0),ln,font=font,stroke_width=2)
            d.text(((1080-(box[2]-box[0]))//2,y),ln,font=font,fill="white",stroke_width=2,stroke_fill="#111827"); y+=100
        d.text((45,1780),"QUICK FACTS • SHORTS",fill="#facc15")
        im.save(frame)
        subprocess.run(["ffmpeg","-y","-loop","1","-i",frame,"-i",audio,"-c:v","libx264","-tune","stillimage","-c:a","aac","-b:a","128k","-pix_fmt","yuv420p","-shortest","-vf","scale=1080:1920","-r","30","-movflags","+faststart",out],check=True,capture_output=True)
    return out

def upload(path,pkg,privacy):
    yt=get_youtube()
    body={"snippet":{"title":pkg["title"][:100],"description":pkg["description"][:5000],"tags":[x.lstrip("#") for x in pkg.get("hashtags",[])][:15],"categoryId":"27"},
          "status":{"privacyStatus":privacy,"selfDeclaredMadeForKids":False}}
    req=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(path,chunksize=-1,resumable=True))
    result=None
    while result is None: _,result=req.next_chunk()
    return "https://www.youtube.com/watch?v="+result["id"]

with st.sidebar:
    niche=st.text_input("Content niche","Trending topics — mixed niche")
    region=st.selectbox("Region",["Pakistan","Worldwide","United States","United Kingdom","India"])
    language=st.selectbox("Language",["English","Urdu","Hindi"])
    duration=st.slider("Length (seconds)",15,58,35)
    privacy=st.selectbox("Upload visibility",["private","unlisted","public"],index=0)

if st.button("1. Find content ideas",type="primary"):
    try:
        with st.spinner("Asking OpenRouter for ideas…"):
            result=ask_json(f"""Suggest 5 potentially timely YouTube Shorts ideas for niche {niche}, region {region}.
Do not pretend to have live trend access. Output JSON object with key ideas, an array of objects with topic, why_it_may_interest_viewers, angle, search_terms. Avoid rumors and unverified claims.""")
            st.session_state.ideas=result.get("ideas",[])
    except Exception as e: st.error(str(e))

ideas=st.session_state.get("ideas",[])
if ideas:
    options=[f"{i+1}. {x.get('topic','Idea')}" for i,x in enumerate(ideas)]
    selected=st.selectbox("Choose idea",options)
    idea=ideas[options.index(selected)]
    st.json(idea)
    if st.button("2. Generate script and video"):
        try:
            with st.spinner("Creating script, voice-over and MP4…"):
                pkg=ask_json(f"""Create an original YouTube Shorts package about {idea.get('topic')}.
Language: {language}. Duration about {duration} seconds. JSON keys: title, description, script (spoken narration), visuals (array), hashtags (array).
No copied scripts, no unsupported claims. Description should disclose realistic AI-generated visuals/voice if applicable.""")
                path=create_video(pkg,language)
                st.session_state.pkg=pkg; st.session_state.path=path
            st.success("Video created.")
        except Exception as e: st.error("Video creation failed: "+str(e)+" Check FFmpeg and API limits.")

pkg=st.session_state.get("pkg"); path=st.session_state.get("path")
if pkg:
    st.subheader("Generated video package")
    st.write("**Title:**",pkg.get("title"))
    st.write("**Description:**",pkg.get("description"))
    st.write("**Narration:**",pkg.get("script"))
    st.write("**Visual plan:**",pkg.get("visuals"))
    if path and os.path.exists(path):
        st.video(path)
        with open(path,"rb") as f: st.download_button("Download MP4",f,file_name="youtube_short.mp4",mime="video/mp4")
        if st.button("3. Upload to YouTube now"):
            try: st.success("Uploaded: "+upload(path,pkg,privacy))
            except Exception as e: st.error("Upload failed: "+str(e))

st.divider()
st.caption("Starter limitation: it makes a narrated title-card video, not a full stock-footage montage. Ideas are AI suggestions, not verified live trends. Uploads default to private. YouTube Data API is still required for publishing.")
