# 短片《第三天》

成片：`第三天_short_film.mp4`（1280×720、24fps、約 1 分 59 秒、中文字幕燒錄）

## 製作流程
1. `shots.json`：16 個分鏡的影格提示（`img`）與動態/音效提示（`vid`）。
2. `gen_image.py` / `gen_all_images.py`：以 `character_sheet_07.png` 為角色參考，用 Gemini 影像模型產生每顆鏡頭的關鍵影格（`keyframes/`）。
3. `gen_video.py`：Veo 3.1 Fast 以關鍵影格生成 s02–s11（含原生環境音與對白）。
4. `fallback_shots.py`：s12–s16 因 Gemini 專案月度花費上限用盡，改以關鍵影格做鏡頭推移、晃動、槍火閃光，並以程式合成雨聲、無線電雜訊、槍響與耳鳴。
5. `gen_audio.py`：心電圖嗶聲（合成）、OS「這是……誰的手？」（Gemini TTS）；`audio/score.mp3` 為 Lyria 生成的原創配樂。
6. `assemble.py` + `subs.json`：調色、顆粒、字卡（三天前／《第三天》）、字幕、混音、輸出。

## 可再提升
- 額度恢復後重跑 `python3 gen_video.py s12 s13 s14 s15 s16`（先刪除 `clips/` 下對應檔），再 `python3 assemble.py`，即可把後五顆換成 Veo 實拍動態。
- Veo 生成的對白為模型自行配音，台詞內容以字幕為準。
