import streamlit as st
import json
import time
import google.generativeai as genai
from pydantic import BaseModel

# ==========================================
# ページ設定とUIの初期化
# ==========================================
st.set_page_config(page_title="1-Click AI Manga Maker", page_icon="📖", layout="centered")

st.title("📖 1-Click AI Manga Maker")
st.markdown("テーマを入力するだけで、AIがストーリーと作画を全自動で行います。")

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
with st.sidebar:
    st.header("⚙️ 設定")
    api_key_input = st.text_input("Gemini API Keyを入力してください", type="password")
    st.markdown("[APIキーの取得はこちら(Google AI Studio)](https://aistudio.google.com/)")

theme = st.text_input("マンガのテーマを入力してください", placeholder="例：サイバーパンク都市でハッキングを行う天才ハッカーの少女")
page_count = st.slider("コマ数", min_value=1, max_value=4, value=4)

if st.button("🚀 マンガを生成する (1-Click)", use_container_width=True):
    if not api_key_input:
        st.error("左のサイドバーからGemini API Keyを設定してください。")
        st.stop()
    if not theme:
        st.warning("テーマを入力してください。")
        st.stop()

    genai.configure(api_key=api_key_input)
    
    with st.status("マンガを生成中... (約1〜2分かかります)", expanded=True) as status:
        try:
            # --- Step 1: 脚本生成 ---
            st.write("📝 Step 1: 構成とプロットを作成中...")
            text_model = genai.GenerativeModel('gemini-3.1-pro')
            
            prompt = f"""
            あなたは世界トップクラスの漫画編集者です。
            テーマ「{theme}」で{page_count}コマのマンガを構成してください。
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
            st.write("🎨 Step 2: コマ画像の作画中...")
            
            for panel in script_data['panels']:
                st.write(f"🖌️ コマ {panel['panel_number']} を描画中...")
                
                image_result = genai.generate_image(
                    model="models/gemini-3-flash-image",
                    prompt=panel['image_prompt'],
                    number_of_images=1,
                    aspect_ratio="3:4",
                    output_mime_type="image/jpeg"
                )
                
                st.image(image_result.images[0].image, use_column_width=True)
                st.markdown(f"**ナレーション:** {panel['narration']}")
                st.info(f"**セリフ:** 「{panel['dialogue']}」")
                st.divider()
                
                time.sleep(2) 
                
            status.update(label="✨ マンガが完成しました！", state="complete", expanded=False)
            st.balloons()
            
        except Exception as e:
            status.update(label="❌ エラーが発生しました", state="error")
            st.error(f"詳細: {e}")
