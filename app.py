import streamlit as st
import json
import time
import urllib.parse
import google.generativeai as genai
from pydantic import BaseModel

# ==========================================
# ページ設定とUIの初期化
# ==========================================
st.set_page_config(page_title="1-Click AI Manga Maker (Gemini版)", page_icon="📖", layout="centered")

st.title("📖 1-Click AI Manga Maker")
st.markdown("テーマを入力するだけで、Geminiが全自動でマンガを作成します。（完全無料版）")

# ==========================================
# データ構造の定義
# ==========================================
class Panel(BaseModel):
    panel_number: int
    image_prompt: str
    dialogue: str
    narration: str

class MangaScript(BaseModel):
    title: str
    character_design_prompt: str
    panels: list[Panel]

# ==========================================
# メインのUIと処理ロジック
# ==========================================
theme = st.text_input("マンガのテーマを入力してください", placeholder="例：サイバーパンク都市でハッキングを行う天才ハッカーの少女")
page_count = st.slider("コマ数", min_value=1, max_value=4, value=4)

if st.button("🚀 マンガを生成する (1-Click)", use_container_width=True):
    if not theme:
        st.warning("テーマを入力してください。")
        st.stop()

    # ★金庫（Secrets）からGemini APIキーを読み込む
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    except KeyError:
        st.error("システムエラー：StreamlitのSecretsにGEMINI_API_KEYが設定されていません。")
        st.stop()
    
    with st.status("マンガを生成中... (約1分かかります)", expanded=True) as status:
        try:
            # --- Step 1: 脚本生成 ---
            st.write("📝 Step 1: Gemini 1.5 Flashで構成とプロットを作成中...")
            
            # 正式に公開されている安定版モデルを指定
            text_model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            あなたは世界トップクラスの漫画編集者です。
            テーマ「{theme}」で{page_count}コマのマンガを構成してください。
            各コマの image_prompt には同じキャラクターの容姿設定（character_design_prompt）を英語で必ず含め、その後にアクションや背景を記述してください。
            """
            
            response = text_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=MangaScript,
                    temperature=0.7,
                ),
            )
            script_data = json.loads(response.text)
            st.write(f"✅ タイトル決定: **{script_data['title']}**")
            
            # --- Step 2: 画像生成と表示 ---
            st.write("🎨 Step 2: フリー画像APIで作画中...")
            
            for panel in script_data['panels']:
                st.write(f"🖌️ コマ {panel['panel_number']} を描画中...")
                
                # 完全無料でAPIキー不要の画像生成サービス (Pollinations AI) を使用
                safe_prompt = urllib.parse.quote(panel['image_prompt'])
                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1792&nologo=true"
                
                # Streamlit上で画像とセリフを表示
                st.image(image_url, use_container_width=True)
                st.markdown(f"**ナレーション:** {panel['narration']}")
                st.info(f"**セリフ:** 「{panel['dialogue']}」")
                st.divider()
                
                time.sleep(1) 
                
            status.update(label="✨ マンガが完成しました！", state="complete", expanded=False)
            st.balloons()
            
        except Exception as e:
            status.update(label="❌ エラーが発生しました", state="error")
            st.error(f"詳細: {e}")
