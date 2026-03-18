import os
import json
import google.generativeai as genai
from pydantic import BaseModel
import time

# ==========================================
# 1. APIの初期設定
# ==========================================
# 環境変数からAPIキーを読み込む
api_key = os.environ.get("AIzaSyDtQzVifZddGgiZrSddRdtSm0QJ7yyI81Q")
if not api_key:
    raise ValueError("GEMINI_API_KEYが設定されていません。")

genai.configure(api_key=api_key)

# ==========================================
# 2. データ構造の定義 (Pydanticによる構造化出力)
# ==========================================
class Panel(BaseModel):
    panel_number: int
    image_prompt: str
    dialogue: str

class MangaScript(BaseModel):
    title: str
    character_design_prompt: str
    panels: list[Panel]

# ==========================================
# 3. メイン処理：自動生成パイプライン
# ==========================================
def generate_manga_pipeline(theme: str, page_count: int = 4):
    print(f"[{theme}] のマンガ生成パイプラインを起動します...")
    
    # --- Step 1: 脚本とプロンプトの自動生成 (Text Generation) ---
    print(">> Step 1: Gemini 3 Proによる脚本と画像プロンプトの設計中...")
    text_model = genai.GenerativeModel('gemini-1.5-pro-latest') # または最新のテキストモデル
    
    prompt = f"""
    あなたは世界トップクラスの漫画編集者兼プロンプトエンジニアです。
    テーマ「{theme}」で{page_count}コマのマンガを構成してください。
    キャラクターの一貫性を保つため、各コマの image_prompt には同じキャラクターの容姿設定（character_design_prompt）を英語で必ず含め、その後にアクションや背景を記述してください。
    """
    
    # 構造化データ（JSON）として出力を強制
    response = text_model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=MangaScript,
            temperature=0.7,
        ),
    )
    
    script_data = json.loads(response.text)
    print(f"タイトル: {script_data['title']}")
    
    # --- Step 2: コマ画像の連続生成 (Image Generation) ---
    print("\n>> Step 2: Gemini 3 Flash Imageによる画像の一括生成中...")
    
    # 画像保存用ディレクトリの作成
    os.makedirs(script_data['title'], exist_ok=True)
    
    # ※注意: 以下の画像生成メソッドは2026年現在の最新SDKの仕様に基づきます
    for panel in script_data['panels']:
        print(f"  - コマ {panel['panel_number']} を生成中... (セリフ: {panel['dialogue']})")
        
        try:
            # 画像生成APIの呼び出し
            image_result = genai.generate_image(
                model="models/gemini-3-flash-image", # Nano Banana 2ベースの最新モデル
                prompt=panel['image_prompt'],
                number_of_images=1,
                aspect_ratio="3:4", # マンガのコマに適した縦長
                output_mime_type="image/jpeg"
            )
            
            # 画像の保存
            image_bytes = image_result.images[0].image
            file_path = f"{script_data['title']}/panel_{panel['panel_number']}.jpg"
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            print(f"    -> {file_path} に保存しました。")
            
            # レートリミット対策のウェイト
            time.sleep(2) 
            
        except Exception as e:
            print(f"    [Error] コマ {panel['panel_number']} の生成に失敗しました: {e}")

    print("\n>> すべての処理が完了しました！")

# ==========================================
# 実行エントリーポイント
# ==========================================
if __name__ == "__main__":
    # 好きなテーマを入力して実行します
    target_theme = "サイバーパンク都市でハッキングを行う天才ハッカーの少女"
    generate_manga_pipeline(theme=target_theme, page_count=4)