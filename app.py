import streamlit as st
import json
import time
import urllib.parse
import google.generativeai as genai

# ==========================================
# ページ設定とUIの初期化
# ==========================================
st.set_page_config(page_title="1-Click AI Manga Maker (Gemini版)", page_icon="📖", layout="centered")

st.title("📖 1-Click AI Manga Maker")
st.markdown("テーマを入力するだけで、Geminiが全自動でマンガを作成します。（完全無料版）")

# ==========================================
# メインのUIと処理ロジック
# ==========================================
theme = st.text_input("マンガのテーマを入力してください", placeholder="例：サイバーパンク都市でハッキングを行う天才ハッカーの少女")
page_count = st.slider("コマ数", min_value=1, max_value=4, value=4)

if st.button("🚀 マンガを生成する (1-Click)", use_container_width=True):
    if not theme:
        st.warning("テーマを入力してください。")
        st.stop()

    # ★金庫（Secrets）からAPIキーを読み込む
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    except KeyError:
        st.error("システムエラー：StreamlitのSecretsにGEMINI_API_KEYが設定されていません。")
        st.stop()
    
    with st.status("マンガを生成中... (約1〜2分かかります)", expanded=True) as status:
        try:
            # --- Step 1: 脚本生成 (フォールバック・システム) ---
            st.write("📝 Step 1: 利用可能なGeminiモデルを検索し、構成を作成中...")
            
            # あなたのアカウントで使えるモデルを上から順に探すリスト
            available_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            script_data = None
            last_error = None
            
            prompt = f"""
            あなたは世界トップクラスの漫画編集者です。
            テーマ「{theme}」で{page_count}コマのマンガを構成してください。
            各コマの image_prompt には同じキャラクターの容姿設定（character_design_prompt）を英語で必ず含め、その後にアクションや背景を記述してください。
            
            【重要】必ず以下のJSONフォーマットのみを出力してください（マークダウンや```jsonなどの記号は一切不要です。純粋なJSONテキストのみを返してください）：
            {{
                "title": "マンガのタイトル",
                "character_design_prompt": "主人公の英語の容姿設定",
                "panels": [
                    {{
                        "panel_number": 1,
                        "image_prompt": "1コマ目の英語の画像生成プロンプト",
                        "dialogue": "1コマ目のセリフ",
                        "narration": "1コマ目のナレーション"
                    }}
                ]
            }}
            """
            
            for model_name in available_models:
                try:
                    st.write(f"🔄 モデル `{model_name}` で接続テスト中...")
                    text_model = genai.GenerativeModel(model_name)
                    response = text_model.generate_content(prompt)
                    
                    # JSON文字列のクレンジング（不要なマークダウンを取り除く）
                    json_str = response.text.strip().replace('```json', '').replace('```', '')
                    script_data = json.loads(json_str)
                    
                    st.write(f"✅ `{model_name}` での生成に成功しました！")
                    break # 成功したらループを抜ける
                except Exception as e:
                    last_error = e
                    st.warning(f"⚠️ `{model_name}` は利用不可でした。次のモデルを試します...")
                    continue
            
            if not script_data:
                raise Exception(f"利用可能なGeminiモデルが見つかりませんでした。最後のエラー: {last_error}")
                
            st.write(f"✅ タイトル決定: **{script_data['title']}**")
            
            # --- Step 2: 画像生成と表示 ---
            st.write("🎨 Step 2: フリー画像APIで作画中...")
            
            for panel in script_data['panels']:
                st.write(f"🖌️ コマ {panel['panel_number']} を描画中...")
                
                safe_prompt = urllib.parse.quote(panel['image_prompt'])
                image_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){safe_prompt}?width=1024&height=1792&nologo=true"
                
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
