import streamlit as st
import json
import time
from openai import OpenAI
from pydantic import BaseModel

# ==========================================
# ページ設定とUIの初期化
# ==========================================
st.set_page_config(page_title="1-Click AI Manga Maker", page_icon="📖", layout="centered")

st.title("📖 1-Click AI Manga Maker")
st.markdown("テーマを入力するだけで、AIが全自動でマンガを作成します。")

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

    # ★変更点：Streamlitの金庫（Secrets）からAPIキーを自動で読み込む
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
    except KeyError:
        st.error("システムエラー：StreamlitのSecretsにAPIキーが設定されていません。")
        st.stop()
    
    with st.status("マンガを生成中... (約1〜2分かかります)", expanded=True) as status:
        try:
            # --- Step 1: 脚本生成 ---
            st.write("📝 Step 1: GPT-4oで構成とプロットを作成中...")
            
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "あなたは世界トップクラスの漫画編集者です。キャラクターの一貫性を保つため、各コマの image_prompt には同じキャラクターの容姿設定（character_design_prompt）を英語で必ず含め、その後にアクションや背景を記述してください。"},
                    {"role": "user", "content": f"テーマ「{theme}」で{page_count}コマのマンガを構成してください。"}
                ],
                response_format=MangaScript,
            )
            
            script_data = completion.choices[0].message.parsed
            st.write(f"✅ タイトル決定: **{script_data.title}**")
            
            # --- Step 2: 画像生成 ---
            st.write("🎨 Step 2: DALL-E 3でコマ画像の作画中...")
            
            for panel in script_data.panels:
                st.write(f"🖌️ コマ {panel.panel_number} を描画中...")
                
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=panel.image_prompt,
                    size="1024x1792",
                    quality="standard",
                    n=1,
                )
                
                image_url = response.data[0].url
                st.image(image_url, use_container_width=True)
                st.markdown(f"**ナレーション:** {panel.narration}")
                st.info(f"**セリフ:** 「{panel.dialogue}」")
                st.divider()
                
            status.update(label="✨ マンガが完成しました！", state="complete", expanded=False)
            st.balloons()
            
        except Exception as e:
            status.update(label="❌ エラーが発生しました", state="error")
            st.error(f"詳細: {e}")
