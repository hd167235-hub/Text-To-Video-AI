#!/usr/bin/env python3
"""Build the presentation video for "Duong ve voi me chu" (Nhom 1).

Pipeline:
  1. Concatenate the male-AI-voice MP3 clips, add a soft ambient bed.
  2. Generate graded backgrounds, on-screen text cards and timed caption cards.
  3. Render each shot with ffmpeg (Ken Burns + fades + timed captions).
  4. Concatenate shots and mux the final audio.

Usage:  python3 build_video.py [--test]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import unicodedata
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
ASSETS = ROOT / "assets"
WEB = ASSETS / "web"
FONTS = ASSETS / "fonts"
AUDIO = ROOT / "audio"
OUT = ROOT.parent / "duong-ve-voi-me-chu.mp4"

W, H = 1280, 720
FPS = 24
SR = 48000
LEAD = 1.2
GAP = 0.30
TAIL = 2.0
ATEMPO = 1.12  # gentle speed-up so the full expanded plot fits in 4:00-4:40

FF = imageio_ffmpeg.get_ffmpeg_exe()
GOLD = (242, 198, 112, 255)
CREAM = (245, 238, 220, 255)
WHITE = (248, 250, 247, 255)

_FONT_FILES = {
    "reg": "BeVietnamPro_400Regular.ttf",
    "italic": "BeVietnamPro_400Regular_Italic.ttf",
    "med": "BeVietnamPro_500Medium.ttf",
    "semi": "BeVietnamPro_600SemiBold.ttf",
    "bold": "BeVietnamPro_700Bold.ttf",
    "black": "BeVietnamPro_800ExtraBold.ttf",
}
_FONT_CACHE: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}


def font(size: int, weight: str = "reg") -> ImageFont.FreeTypeFont:
    key = (size, weight)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(str(FONTS / _FONT_FILES[weight]), size)
    return _FONT_CACHE[key]


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = nfc(text).split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def spaced(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, spacing: int = 2):
    x, y = xy
    for ch in nfc(text):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + spacing


def text(draw, xy, value, fnt, fill, anchor="la", stroke=0, stroke_fill=(0, 0, 0, 170)):
    draw.text(xy, nfc(value), font=fnt, fill=fill, anchor=anchor,
              stroke_width=stroke, stroke_fill=stroke_fill)


# --------------------------------------------------------------------------- script

T_OPEN = "Kính chào thầy cô và các bạn! Hôm nay, Nhóm 1 chúng em xin thuyết trình về tác phẩm Đường về với mẹ chữ của nhà văn Vi Hồng."
T_GROUP = "Em là Trần Tiến Minh, phụ trách mở đầu và kết bài. Em là Nguyễn Thị Hiền, giới thiệu tác phẩm. Em là Vũ Tiến Đạt, phần nhân vật. Em là Trần Văn Phúc, phần tóm tắt truyện. Em là Vũ Ngọc Linh, phần nghệ thuật. Em là Vi Đức Hiệp, phần giá trị tác phẩm. Mời thầy cô và các bạn cùng theo dõi!"
T_AUTHOR = "Đường về với mẹ chữ là truyện ngắn ký của nhà văn Vi Hồng, tên thật là Vi Văn Hồng, người dân tộc Tày, quê ở Cao Bằng, mất năm 1997 tại Thái Nguyên, quê hương của nhóm em. Ông sinh năm 1936 và gắn bó suốt đời với văn hóa Tày, Nùng."
T_BG = "Tác phẩm ghi lại hành trình đi học thời kháng chiến. Trước năm 1949, miền núi Đông Bắc chỉ có một trường cấp II duy nhất, nay là trường Lương Ngọc Quyến ở Thái Nguyên, khi ấy phải học trong hang đá. Học xong mẹ chữ ở Cao Bằng, muốn học cao hơn, các học sinh quyết tìm đường về với mẹ chữ ở xứ Thái."
T_CHAR = "Nhân vật chính là tác giả, tôi, một trong bảy học sinh người Tày, kể lại bằng ngôi thứ nhất. Đi cùng là sáu người bạn trên chặng đường dài hơn hai trăm năm mươi ki lô mét. Còn có cha mẹ và các già làng qua lời kể. Hình ảnh mẹ chữ được nhân cách hóa: người Tày gọi cái gì quý giá là mẻ, nghĩa là mẹ, như mẹ đá, mẹ nước. Nên trường học, người thầy được gọi là mẹ chữ, đích đến thiêng liêng của hành trình."

T_PLOT1 = "Thời kháng chiến chống Pháp, trường lớp thường phải di chuyển, có khi phải học trong hang đá. Học hết lớp bảy ở Cao Bằng, bảy học sinh quyết định đến trường Lương Ngọc Quyến ở Thái Nguyên để học tiếp. Với họ, trường học là nơi sinh ra chữ nghĩa, được gọi trìu mến là mẹ chữ. Cho con đi học xa là quyết định rất khó khăn với các gia đình nghèo, vì chi phí quá lớn."
T_PLOT2 = "Từ nhà đến trường dài hơn hai trăm năm mươi cây số, có bạn phải đi gần ba trăm. Cả nhóm đi bộ suốt chín ngày đêm, vượt núi, băng rừng, lội suối. Ban đêm gặp bản thì xin ngủ nhờ; không gặp nhà dân thì ngủ rừng hoặc nghỉ ở lều quán ven đường. Chân sưng tấy, giày dép mang theo cũng rách hết."
T_PLOT3 = "Đến trường ôn thi, họ lại nhận tin hoãn thi một tháng. Không có đủ tiền ở lại, cả nhóm phải đi bộ chín ngày trở về nhà. Nghỉ ở nhà chừng mười ngày, họ lại chuẩn bị lên đường. Những chuyến đi vất vả ấy lặp lại nhiều lần trên con đường học tập."
T_PLOT4 = "Đáng nhớ là cuộc chạm trán với hổ trên đường đi học. Dù cha mẹ đã căn dặn cách đề phòng, khi đối diện con vật, một số người vẫn tái mặt vì sợ. Vi Hồng và bạn Phan Soong cố giữ bình tĩnh. Thấy hổ sắp tấn công, Vi Hồng hô hào mọi người cùng chống trả. Cả nhóm cùng dân bản reo hò, cầm dao, vác gậy tiến lên; Hỏn cũng xông lên hàng đầu. Trước sự chống trả ấy, con hổ bỏ chạy vào rừng."
T_PLOT5 = "Một lần đi xe đạp về quê cùng bạn Lư, Vi Hồng gặp rết hổ ở đèo Giàng. Qua lời kể của tác giả và chuyện truyền lại trong dân gian, đây là loài vật có nọc độc nguy hiểm. Cuộc gặp khiến ông vô cùng hoảng hốt; qua khỏi chỗ nguy hiểm, ông vẫn chưa hết sợ trong suốt đoạn xuống đèo. Đó là kỉ niệm khó quên về hiểm nguy trên đường đi học."
T_PLOT6 = "Đến được trường chưa có nghĩa là hết gian nan. Học trò xa quê thiếu ăn, thiếu áo ấm, ở trọ trong gian bếp thấp, vách thưa, gió lùa bốn phía. Chiếc chõng tre vừa là giường ngủ vừa là bàn học; mùa đông đắp chăn cũ thủng, nằm sát nhau cho đỡ rét. Có lần Bế Tâm bị cảm nặng, phải nằm viện gần nửa tháng. Dù vậy các bạn vẫn chăm chỉ học hành, và nhắc nhau: cần cố gắng, cần gan dạ mới về được với mẹ chữ. Học thêm một chữ là một phân vàng cho đời."

T_ART = "Về nghệ thuật, tác phẩm nổi bật ở bốn điểm. Một, thể loại ký truyện ngắn, ngôi kể thứ nhất tôi, người trong cuộc, nên câu chuyện chân thực, giàu cảm xúc. Hai, ngôn ngữ mộc mạc, đậm chất dân gian Tày, như mẹ đá, mẹ nước, lời các già làng, mỗi chữ một phân vàng. Ba, chi tiết giàu sức gợi: cuộc đối mặt với hổ dữ, rết hổ ở đèo Giàng, chiếc chõng tre vừa là giường vừa là bàn học. Bốn, vừa kể vừa suy ngẫm, xen những triết lý sâu sắc về giá trị chữ nghĩa."
T_VALUE = "Về giá trị, tác phẩm ca ngợi tinh thần hiếu học, gan dạ, kiên trì của thanh niên dân tộc thiểu số thời chiến. Đồng thời nhắc nhở thế hệ trẻ hôm nay: cha ông xưa vất vả đến thế nào mới có một ít chữ trong bụng, nên ta phải trân trọng và chăm học. Tác phẩm còn thể hiện tình yêu quê hương, niềm tự hào về văn hóa dân tộc Việt Bắc, và giá trị nhân văn sâu sắc: tri thức là tài sản quý giá nhất để con người trưởng thành."
T_END = "Kính chào thầy cô và các bạn! Bài thuyết trình của Nhóm 1 chúng em đến đây là kết thúc. Nhóm 1 xin chân thành cảm ơn thầy cô giáo đã xem bài thuyết trình của chúng em. Kính chúc thầy cô luôn mạnh khỏe, hạnh phúc và công tác tốt. Xin cảm ơn!"

CREDITS = ("Ảnh bìa: NXB Kim Đồng / Báo Văn hóa Nghệ thuật · Chân dung: nguoinoitieng.tv · "
           "Tư liệu cốt truyện: vanhoanghethuat.vn · Minh họa: AI · Giọng đọc: AI nam")


def spec(**kw):
    return kw


CLIPS: list[dict] = [
    dict(audio="clip01.mp3", text=T_OPEN, fracs=[1.0], shots=[
        spec(bg="01_hero_mountains.jpg", section="PHẦN 1  ·  MỞ ĐẦU",
             title="ĐƯỜNG VỀ\nVỚI MẸ CHỮ", title_size=62,
             subtitle="Nhà văn Vi Hồng  ·  Bài thuyết trình của Nhóm 1",
             bullets=["Truyện ngắn – ký", "Hành trình đi học thời kháng chiến", "Việt Bắc, trước năm 1949"],
             inset="bia_sach.jpg", inset_label="BÌA TÁC PHẨM · NXB KIM ĐỒNG")]),
    dict(audio="clip02.mp3", text=T_GROUP, fracs=[1.0], shots=[
        spec(bg="01_hero_mountains.jpg", variant="cool", section="PHẦN 1  ·  NHÓM 1",
             title="Sáu thành viên, một hành trình", title_size=54,
             subtitle="Phân công phần trình bày", two_cols=True, bullet_size=26,
             bullets=[["Trần Tiến Minh — Mở đầu & Kết bài", "Nguyễn Thị Hiền — Giới thiệu tác phẩm", "Vũ Tiến Đạt — Nhân vật"],
                      ["Trần Văn Phúc — Tóm tắt truyện", "Vũ Ngọc Linh — Nghệ thuật", "Vi Đức Hiệp — Giá trị & ý nghĩa"]])]),
    dict(audio="clip03.mp3", text=T_AUTHOR, fracs=[1.0], shots=[
        spec(bg="02_author_desk.jpg", section="2.1  ·  GIỚI THIỆU CHUNG", title="Nhà văn Vi Hồng",
             subtitle="Vi Văn Hồng  ·  Dân tộc Tày  ·  Quê Cao Bằng",
             bullets=["1936 – 1997: mất tại Thái Nguyên", "Giảng viên Đại học Sư phạm Việt Bắc",
                      "Gắn bó suốt đời với văn hóa Tày, Nùng", "Giải thưởng Nhà nước truy tặng năm 2012"],
             bullet_size=26, inset="chan_dung_vi_hong.jpg", inset_label="CHÂN DUNG NHÀ VĂN VI HỒNG",
             inset_box=(906, 150, 1164, 408))]),
    dict(audio="clip04.mp3", text=T_BG, fracs=[0.52, 0.48], shots=[
        spec(bg="03_cave_classroom.jpg", section="2.1  ·  BỐI CẢNH", title="Học chữ trong hang đá",
             subtitle="Trước năm 1949 · Miền núi Đông Bắc",
             bullets=["Chỉ có một trường cấp II duy nhất", "Nay là trường Lương Ngọc Quyến, Thái Nguyên",
                      "Lớp học sơ tán trong hang đá thời kháng chiến"], bullet_size=27),
        spec(bg="map", section="2.1  ·  HÀNH TRÌNH", title="Từ Cao Bằng đến xứ Thái",
             subtitle="Khát khao được học cao hơn",
             bullets=["Học xong 'mẹ chữ' ở Cao Bằng", "Bảy học sinh quyết lên đường", "Tìm 'đường về với mẹ chữ'"], bullet_size=27)]),
    dict(audio="clip05.mp3", text=T_CHAR, fracs=[0.48, 0.52], shots=[
        spec(bg="04_students_road.jpg", section="2.2  ·  NHÂN VẬT", title="Bảy học sinh người Tày",
             subtitle="Ngôi kể thứ nhất: 'tôi' – người trong cuộc",
             bullets=["Tác giả cùng sáu người bạn", "Chặng đường dài hơn 250 km", "Cha mẹ, các già làng qua lời kể"], bullet_size=27),
        spec(bg="05_mother_word.jpg", section="2.2  ·  HÌNH ẢNH", title="Mẹ chữ",
             subtitle="Người Tày gọi cái quý giá là 'mẻ' – nghĩa là mẹ",
             bullets=["Mẹ đá  ·  Mẹ nước", "Trường học và người thầy được gọi là 'mẹ chữ'",
                      "Đích đến thiêng liêng của hành trình"], bullet_size=27)]),
    # ---- expanded plot (user-supplied summary) ----
    dict(audio="plot01.mp3", text=T_PLOT1, fracs=[1.0], shots=[
        spec(bg="10_village_farewell.jpg", section="2.3  ·  CỐT TRUYỆN (1/6)",
             title="Quyết tâm đi tìm mẹ chữ", title_size=52,
             subtitle="Kháng chiến chống Pháp · Trường lớp sơ tán trong hang đá",
             bullets=["Học hết lớp 7 ở Cao Bằng", "Bảy học sinh đến trường Lương Ngọc Quyến, Thái Nguyên",
                      "Trường học = nơi sinh ra chữ nghĩa = 'mẹ chữ'",
                      "Gia đình nghèo: cho con đi học xa là quyết định khó khăn"], bullet_size=26)]),
    dict(audio="plot02.mp3", text=T_PLOT2, fracs=[0.50, 0.50], shots=[
        spec(bg="11_night_camp.jpg", section="2.3  ·  CỐT TRUYỆN (2/6)",
             title="Chín ngày đêm đi bộ", title_size=52,
             subtitle="Hơn 250 km, có bạn gần 300 km",
             bullets=["Vượt núi, băng rừng, lội suối", "Gặp bản xin ngủ nhờ; không thì ngủ rừng, lều quán",
                      "Chân sưng tấy, giày dép rách hết"], bullet_size=27),
        spec(bg="06_mountain_pass.jpg", section="2.3  ·  CỐT TRUYỆN (2/6)",
             title="Đường dài 250 – 300 km", title_size=48, big_number="9 ngày đêm",
             bullets=["Đi bộ suốt chín ngày đêm", "Ban ngày đi, ban đêm nghỉ nhờ bản",
                      "Chân sưng tấy, giày dép mang theo rách hết"], bullet_size=27)]),
    dict(audio="plot03.mp3", text=T_PLOT3, fracs=[1.0], shots=[
        spec(bg="12_school_gate.jpg", section="2.3  ·  CỐT TRUYỆN (3/6)",
             title="Hoãn thi, lại trở về", title_size=54,
             subtitle="Không đủ tiền ở lại Thái Nguyên",
             bullets=["Nhận tin hoãn thi một tháng", "Đi bộ chín ngày về nhà, nghỉ chừng mười ngày",
                      "Rồi lại chuẩn bị lên đường", "Những chuyến đi ấy lặp lại nhiều lần"], bullet_size=27)]),
    dict(audio="plot04.mp3", text=T_PLOT4, fracs=[1.0], shots=[
        spec(bg="13_tiger_confront.jpg", section="2.3  ·  CỐT TRUYỆN (4/6)",
             title="Đối mặt với hổ dữ", title_size=54,
             subtitle="Cuộc chạm trán trên đường đi học",
             bullets=["Cha mẹ căn dặn, nhưng nhiều người vẫn tái mặt", "Vi Hồng và Phan Soong giữ bình tĩnh, hô hào chống trả",
                      "Dân bản cùng reo hò, cầm dao, vác gậy", "Hỏn xông lên hàng đầu · Hổ bỏ chạy vào rừng"], bullet_size=26)]),
    dict(audio="plot05.mp3", text=T_PLOT5, fracs=[1.0], shots=[
        spec(bg="14_bicycle_centipede.jpg", section="2.3  ·  CỐT TRUYỆN (5/6)",
             title="Rết hổ ở đèo Giàng", title_size=54,
             subtitle="Đi xe đạp về quê cùng bạn Lư",
             bullets=["Loài vật có nọc độc nguy hiểm trong lời kể dân gian", "Vi Hồng vô cùng hoảng hốt",
                      "Qua khỏi nơi nguy hiểm vẫn chưa hết sợ", "Kỉ niệm khó quên về hiểm nguy trên đường học"], bullet_size=26)]),
    dict(audio="plot06.mp3", text=T_PLOT6, fracs=[0.52, 0.48], shots=[
        spec(bg="15_cold_kitchen.jpg", section="2.3  ·  CỐT TRUYỆN (6/6)",
             title="Vượt đói rét để tiếp tục học", title_size=48,
             subtitle="Gian bếp thấp, vách thưa, gió lùa bốn phía",
             bullets=["Thiếu ăn, thiếu áo ấm", "Chõng tre: vừa giường ngủ, vừa bàn học",
                      "Mùa đông đắp chăn cũ thủng, nằm sát nhau", "Bế Tâm cảm nặng, nằm viện gần nửa tháng"], bullet_size=25),
        spec(bg="16_study_by_lamp.jpg", section="2.3  ·  CỐT TRUYỆN (6/6)",
             title="Không bỏ dở việc học", title_size=52,
             quote="'Cần cố gắng, cần gan dạ mới về được với mẹ chữ'",
             bullets=["Học thêm một chữ là một phân vàng cho đời", "Cùng nhau đến với Mẹ chữ Lương Ngọc Quyến"], bullet_size=27)]),
    dict(audio="art_new.mp3", text=T_ART, fracs=[1.0], shots=[
        spec(bg="08_art_book.jpg", section="2.4  ·  NGHỆ THUẬT", title="Bốn nét đặc sắc",
             numbered=True, bullet_size=27,
             bullets=["Ký – truyện ngắn, ngôi kể thứ nhất 'tôi' nên chân thực, giàu cảm xúc",
                      "Ngôn ngữ mộc mạc, đậm chất dân gian Tày: 'mẹ đá', 'mỗi chữ một phân vàng'",
                      "Chi tiết giàu sức gợi: hổ dữ, rết hổ đèo Giàng, chõng tre làm bàn học",
                      "Vừa kể vừa suy ngẫm, xen triết lý về giá trị chữ nghĩa"])]),
    dict(audio="clip09.mp3", text=T_VALUE, fracs=[1.0], shots=[
        spec(bg="09_value_sunrise.jpg", variant="cool", section="2.4  ·  GIÁ TRỊ & Ý NGHĨA",
             title="Tri thức là tài sản quý giá nhất", title_size=50,
             bullets=["Ca ngợi tinh thần hiếu học, gan dạ, kiên trì", "Nhắc nhở thế hệ trẻ: trân trọng và chăm học",
                      "Tình yêu quê hương, tự hào văn hóa Việt Bắc", "Giá trị nhân văn sâu sắc"], bullet_size=27)]),
    dict(audio="clip10.mp3", text=T_END, fracs=[1.0], shots=[
        spec(bg="01_hero_mountains.jpg", variant="warm", center=True, section="PHẦN 3  ·  KẾT BÀI",
             title="Xin chân thành cảm ơn", title_size=66,
             subtitle="Kính chúc thầy cô luôn mạnh khỏe, hạnh phúc và công tác tốt",
             quote="'Bài thuyết trình của Nhóm 1 đến đây là kết thúc'",
             credits=CREDITS)]),
]


# --------------------------------------------------------------------------- audio

def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    if capture:
        return subprocess.run(cmd, capture_output=True, check=True)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)


def decode_mp3(path: Path) -> np.ndarray:
    r = run([FF, "-v", "error", "-i", str(path), "-af", f"atempo={ATEMPO}",
             "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture=True)
    pcm = np.frombuffer(r.stdout, dtype="<i2").astype(np.float32) / 32768.0
    peak = float(np.max(np.abs(pcm))) or 1.0
    return pcm * (0.84 / peak)


def make_music(duration: float) -> np.ndarray:
    n = int(duration * SR)
    t = np.arange(n, dtype=np.float32) / SR
    freqs = [146.83, 220.0, 293.66, 349.23, 440.0]
    out = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(freqs):
        env = 0.55 + 0.45 * np.sin(2 * np.pi * (0.031 + i * 0.006) * t + i * 0.7)
        out += (0.55 / (i + 1)) * env * np.sin(2 * np.pi * f * t + 0.12 * np.sin(2 * np.pi * 0.07 * t))
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, n + 512).astype(np.float32)
    cs = np.cumsum(noise)
    smooth = (cs[512:] - cs[:-512]) / 512.0
    out += 0.35 * smooth * (0.5 + 0.5 * np.sin(2 * np.pi * 0.021 * t))
    out *= 0.075
    fade = int(3.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return out


def build_audio() -> tuple[list[dict], float, Path]:
    clips = [decode_mp3(AUDIO / c["audio"]) for c in CLIPS]
    durations = [len(c) / SR for c in clips]
    timeline = 0.0
    parts: list[np.ndarray] = []
    meta: list[dict] = []
    parts.append(np.zeros(int(LEAD * SR), dtype=np.float32))
    timeline += LEAD
    for i, (pcm, dur, conf) in enumerate(zip(clips, durations, CLIPS), start=1):
        meta.append({"index": i, "start": timeline, "dur": dur, "end": timeline + dur, "text": conf["text"]})
        parts.append(pcm)
        timeline += dur
        gap = TAIL if i == len(CLIPS) else GAP
        parts.append(np.zeros(int(gap * SR), dtype=np.float32))
        timeline += gap
    narration = np.concatenate(parts)
    total = len(narration) / SR
    music = make_music(total)
    mixed = np.tanh((narration + music[: len(narration)]) * 1.05) * 0.94
    pcm16 = (np.clip(mixed, -1, 1) * 32767).astype("<i2")
    path = BUILD / "final_audio.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16.tobytes())
    print(f"[audio] {total:.2f}s = {int(total//60)}:{total%60:04.1f} -> {path.name}")
    return meta, total, path


# --------------------------------------------------------------------------- artwork

def graded_bg(src: Path, dst: Path, warmth: float = 1.0, dim: float = 0.80) -> Path:
    im = Image.open(src).convert("RGB")
    im = ImageOps.fit(im, (1920, 1080), Image.LANCZOS, centering=(0.5, 0.48))
    arr = np.asarray(im).astype(np.float32)
    arr = arr * dim * np.array([1.04 * warmth, 1.0, 0.96 / warmth], dtype=np.float32)
    yy, xx = np.mgrid[0:1080, 0:1920]
    r = np.sqrt(((xx - 960) / 960) ** 2 + ((yy - 540) / 540) ** 2) / 1.414
    arr *= np.clip(1 - 0.30 * r ** 1.7, 0.65, 1.0)[..., None]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(dst, quality=92)
    return dst


def make_map_bg(dst: Path) -> Path:
    """Self-drawn stylised parchment map: Cao Bang -> Thai Nguyen."""
    rng = np.random.default_rng(21)
    base = np.zeros((1080, 1920, 3), dtype=np.float32)
    base[:] = np.array([226, 208, 172], dtype=np.float32)
    base += rng.normal(0, 5, base.shape).astype(np.float32)
    yy, xx = np.mgrid[0:1080, 0:1920]
    r = np.sqrt(((xx - 960) / 960) ** 2 + ((yy - 540) / 540) ** 2) / 1.414
    base *= np.clip(1 - 0.42 * r ** 1.8, 0.55, 1.0)[..., None]
    Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(dst, quality=94)
    im = Image.open(dst).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    for k in range(16):
        pts = [(x, 115 + k * 58 + 46 * math.sin(x / 220 + k * 0.55) + 24 * math.sin(x / 95 + k))
               for x in range(0, 1921, 12)]
        d.line(pts, fill=(120, 104, 78, 48), width=2)
    for cx, cy, scale in [(260, 700, 1.0), (560, 830, 1.3), (1420, 700, 1.1), (1660, 850, 0.9)]:
        s = 90 * scale
        d.line([(cx - s, cy), (cx, cy - s * 1.25), (cx + s, cy)], fill=(104, 88, 66, 150), width=5)
        d.line([(cx - s * 0.45, cy - s * 0.45), (cx, cy - s * 1.25)], fill=(104, 88, 66, 90), width=3)
    A = np.array([430.0, 330.0])
    B = np.array([1420.0, 760.0])
    C1 = np.array([720.0, 250.0])
    C2 = np.array([1030.0, 900.0])
    curve = []
    for i in range(501):
        t = i / 500
        p = (1 - t) ** 3 * A + 3 * (1 - t) ** 2 * t * C1 + 3 * (1 - t) * t ** 2 * C2 + t ** 3 * B
        curve.append(tuple(p))
    for i in range(0, len(curve) - 8, 14):
        d.line(curve[i: i + 9], fill=(176, 62, 48, 235), width=8)
    for p in [tuple(A), tuple(B)]:
        x, y = p
        d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=(176, 62, 48, 255), outline=(255, 246, 224, 255), width=4)
    x, y = tuple(B)
    d.text((x, y - 74), "THÁI NGUYÊN", font=font(40, "bold"), fill=(74, 58, 42, 255), anchor="mm")
    d.text((x, y + 52), "Mẹ chữ Lương Ngọc Quyến", font=font(26, "reg"), fill=(96, 78, 58, 255), anchor="mm")
    d.text((960, 100), "VIỆT BẮC", font=font(66, "bold"), fill=(104, 88, 66, 70), anchor="mm")
    cx, cy = 1740, 200
    d.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), outline=(104, 88, 66, 150), width=3)
    d.line([(cx, cy - 78), (cx, cy + 78)], fill=(104, 88, 66, 150), width=3)
    d.line([(cx - 78, cy), (cx + 78, cy)], fill=(104, 88, 66, 150), width=3)
    d.text((cx, cy - 100), "B", font=font(30, "bold"), fill=(104, 88, 66, 190), anchor="mm")
    im.convert("RGB").save(dst, quality=94)
    return dst


def prepare_backgrounds():
    for p in sorted(ASSETS.glob("[0-9][0-9]_*.jpg")):
        graded_bg(p, BUILD / f"bg_{p.stem}.jpg")
    hero = ASSETS / "01_hero_mountains.jpg"
    value = ASSETS / "09_value_sunrise.jpg"
    graded_bg(hero, BUILD / "bg_01_hero_mountains_cool.jpg", warmth=0.90, dim=0.72)
    graded_bg(hero, BUILD / "bg_01_hero_mountains_warm.jpg", warmth=1.10, dim=0.70)
    graded_bg(value, BUILD / "bg_09_value_sunrise_cool.jpg", warmth=0.92, dim=0.74)
    make_map_bg(BUILD / "bg_map.jpg")


def bg_path(spec: dict) -> Path:
    name = spec["bg"]
    if name == "map":
        return BUILD / "bg_map.jpg"
    suffix = {"cool": "_cool", "warm": "_warm"}.get(spec.get("variant", ""), "")
    return BUILD / f"bg_{Path(name).stem}{suffix}.jpg"


def base_panel() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W]
    left = np.clip(1 - xx / 900.0, 0, 1) ** 1.25 * 196
    bottom = np.clip((yy - 400) / 300.0, 0, 1) ** 1.15 * 178
    a = np.maximum(np.maximum(left, bottom), 14)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 7, 19, 23
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def paste_inset(ov: Image.Image, path: Path, box, label=None):
    d = ImageDraw.Draw(ov, "RGBA")
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 - 2, y0 + 6, x1 + 10, y1 + 16), 18, fill=(0, 0, 0, 90))
    d.rounded_rectangle((x0 - 10, y0 - 10, x1 + 10, y1 + 10), 18, fill=(243, 231, 205, 238))
    im = Image.open(path).convert("RGB")
    im = ImageOps.fit(im, (x1 - x0, y1 - y0), Image.LANCZOS, centering=(0.5, 0.42))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), 10, fill=255)
    ov.paste(im, (x0, y0), mask)
    d.rounded_rectangle((x0, y0, x1, y1), 10, outline=(255, 255, 255, 120), width=2)
    if label:
        d.rounded_rectangle((x0 - 10, y1 + 16, x1 + 10, y1 + 58), 8, fill=(7, 19, 23, 210))
        text(d, ((x0 + x1) / 2, y1 + 37), label, font(20, "semi"), GOLD, anchor="mm")


def make_overlay(spec: dict, dst: Path, progress: float):
    ov = base_panel().copy()
    d = ImageDraw.Draw(ov, "RGBA")
    d.rectangle((0, 0, W, 5), fill=(255, 255, 255, 28))
    d.rectangle((0, 0, int(W * progress), 5), fill=GOLD)
    text(d, (W - 52, 34), "NHÓM 1  ·  THUYẾT TRÌNH VĂN HỌC", font(19, "semi"), (225, 232, 225, 190), anchor="ra")

    center = spec.get("center", False)
    left = 84 if not center else W / 2
    max_w = 760 if spec.get("inset") else 1080
    if center:
        max_w = 1050

    label = spec.get("section", "")
    if not center:
        d.rounded_rectangle((84, 72, 128, 78), 3, fill=GOLD)
        spaced(d, (146, 62), label, font(22, "semi"), GOLD, 2)
    else:
        spaced(d, (W / 2 - font(23, "semi").getlength(label) / 2, 92), label, font(23, "semi"), GOLD, 2)

    y = 128 if not center else 158
    if spec.get("big_number"):
        text(d, (left if not center else W / 2, y), spec["big_number"], font(76, "black"), GOLD,
             anchor="la" if not center else "ma")
        y += 96

    tf = font(spec.get("title_size", 60), "bold")
    title_lines: list[str] = []
    for block in spec.get("title", "").split("\n"):
        title_lines.extend(wrap(block, tf, max_w))
    for line in title_lines:
        text(d, (left if not center else W / 2, y), line, tf, WHITE,
             anchor="la" if not center else "ma", stroke=1)
        y += tf.size * 1.16
    y += 14

    if spec.get("subtitle"):
        sf = font(28, "med")
        for line in wrap(spec["subtitle"], sf, max_w):
            text(d, (left if not center else W / 2, y), line, sf, (222, 232, 224, 255),
                 anchor="la" if not center else "ma")
            y += sf.size * 1.35
        y += 26

    if spec.get("quote"):
        qf = font(41, "italic")
        for line in wrap(spec["quote"], qf, max_w):
            text(d, (left if not center else W / 2, y), line, qf, GOLD,
                 anchor="la" if not center else "ma", stroke=1)
            y += qf.size * 1.3
        y += 30

    bullets = spec.get("bullets", [])
    if bullets:
        bf = font(spec.get("bullet_size", 27), "reg")
        numbered = spec.get("numbered", False)
        if spec.get("two_cols"):
            for ci, col in enumerate(bullets):
                bx, by = 84 + ci * 600, y
                for item in col:
                    d.ellipse((bx, by + 11, bx + 12, by + 23), fill=GOLD)
                    lines = wrap(item, bf, 510)
                    for j, line in enumerate(lines):
                        text(d, (bx + 30, by + j * bf.size * 1.3), line, bf, WHITE)
                    by += max(52, len(lines) * bf.size * 1.3 + 18)
        else:
            by = y
            for idx, item in enumerate(bullets):
                if numbered:
                    d.rounded_rectangle((left, by + 2, left + 36, by + 38), 10, fill=(242, 198, 112, 55))
                    text(d, (left + 18, by + 20), str(idx + 1), font(22, "bold"), GOLD, anchor="mm")
                    tx = left + 52
                else:
                    d.ellipse((left, by + 12, left + 13, by + 25), fill=GOLD)
                    tx = left + 32
                lines = wrap(item, bf, max_w - (tx - left))
                for j, line in enumerate(lines):
                    text(d, (tx, by + j * bf.size * 1.3), line, bf, WHITE)
                by += max(50, len(lines) * bf.size * 1.3 + 14)

    if spec.get("inset"):
        paste_inset(ov, WEB / spec["inset"], spec.get("inset_box", (892, 176, 1176, 458)), spec.get("inset_label"))
    if spec.get("credits"):
        text(d, (W / 2, 566), spec["credits"], font(17, "reg"), (220, 226, 218, 175), anchor="ma")
    ov.save(dst)


def chunk_text(value: str, max_chars: int = 96) -> list[str]:
    parts = re.split(r"(?<=[.!?;:,])\s+", nfc(value))
    chunks: list[str] = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            if len(p) <= max_chars:
                cur = p
            else:
                acc = ""
                for w in p.split():
                    if len(acc) + len(w) + 1 <= max_chars:
                        acc = (acc + " " + w).strip()
                    else:
                        chunks.append(acc)
                        acc = w
                cur = acc
    if cur:
        chunks.append(cur)
    return chunks


def caption_schedule(clip: dict) -> list[tuple[float, float, str]]:
    chunks = chunk_text(clip["text"])
    weights = [max(8, len(c)) for c in chunks]
    total = sum(weights)
    out, acc = [], 0
    for c, wgt in zip(chunks, weights):
        s = clip["start"] + acc / total * clip["dur"]
        acc += wgt
        e = clip["start"] + acc / total * clip["dur"]
        out.append((s, e, c))
    return out


def caption_schedule_all(clip_meta: list[dict]):
    out = []
    for c in clip_meta:
        out.extend(caption_schedule(c))
    return out


def make_caption(value: str, dst: Path):
    value = nfc(value).strip().rstrip(" ,;:")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    d.rounded_rectangle((86, 594, 1194, 704), 18, fill=(6, 17, 21, 224))
    d.rounded_rectangle((86, 608, 92, 690), 3, fill=GOLD)
    f = font(31, "reg")
    lines = wrap(value, f, 1040)
    if len(lines) > 2:
        f = font(27, "reg")
        lines = wrap(value, f, 1040)
    if len(lines) > 2:
        lines = lines[:2]
    lh = f.size * 1.34
    for i, line in enumerate(lines):
        cy = 649 + (i - (len(lines) - 1) / 2) * lh
        text(d, (640, cy), line, f, WHITE, anchor="mm", stroke=1, stroke_fill=(0, 0, 0, 150))
    ov.save(dst)


# --------------------------------------------------------------------------- shots

def build_shots(clip_meta: list[dict], total: float) -> list[dict]:
    shots: list[dict] = []
    cursor = 0.0
    for ci, (clip, conf) in enumerate(zip(clip_meta, CLIPS)):
        seg_start = 0.0 if ci == 0 else cursor
        seg_end = clip["end"] + (TAIL if ci == len(CLIPS) - 1 else GAP)
        seg_dur = seg_end - seg_start
        fracs, specs = conf["fracs"], conf["shots"]
        t = seg_start
        for k, (frac, sp) in enumerate(zip(fracs, specs)):
            dur = seg_dur * frac if k < len(fracs) - 1 else seg_end - t
            shots.append({"index": len(shots) + 1, "clip": clip, "spec": sp,
                          "start": t, "end": t + dur, "dur": dur, "progress": t / total})
            t += dur
        cursor = seg_end
    assert abs(sum(s["dur"] for s in shots) - total) < 0.05
    return shots


def render_shot(shot: dict, captions: list[tuple[float, float, str]]) -> Path:
    idx, dur = shot["index"], shot["dur"]
    ov_path = BUILD / f"ov_{idx:02d}.png"
    make_overlay(shot["spec"], ov_path, shot["progress"])
    bgp = bg_path(shot["spec"])

    local_caps = []
    for ci, (s, e, value) in enumerate(captions):
        ls = max(s, shot["start"]) - shot["start"]
        le = min(e, shot["end"]) - shot["start"]
        if le - ls < 0.25:
            continue
        cap_path = BUILD / f"cap_{idx:02d}_{ci:02d}.png"
        make_caption(value, cap_path)
        local_caps.append((ls, le, cap_path))

    cmd = [FF, "-y", "-v", "error"]
    for p in [bgp, ov_path] + [c[2] for c in local_caps]:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(p)]
    f = [
        "[0:v]zoompan=z='min(1.0+0.00032*on,1.09)':x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24,format=rgba[base]",
        f"[1:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1,"
        f"fade=t=out:st={max(0, dur-0.5):.3f}:d=0.5:alpha=1[ov0]",
        "[base][ov0]overlay=0:0:format=auto[v0]",
    ]
    for i, (s, e, _) in enumerate(local_caps):
        fd = min(0.28, (e - s) / 3)
        f.append(f"[{i+2}:v]format=rgba,fade=t=in:st={s:.3f}:d={fd:.3f}:alpha=1,"
                 f"fade=t=out:st={max(s, e-fd):.3f}:d={fd:.3f}:alpha=1[c{i}]")
        f.append(f"[v{i}][c{i}]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})':format=auto[v{i+1}]")
    last = f"v{len(local_caps)}"
    f.append(f"[{last}]fade=t=in:st=0:d=0.32,fade=t=out:st={max(0, dur-0.32):.3f}:d=0.32,"
             "format=yuv420p[v]")
    out = BUILD / f"seg_{idx:02d}.mp4"
    cmd += ["-filter_complex", ";".join(f), "-map", "[v]", "-an", "-t", f"{dur:.3f}",
            "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-g", "48", "-threads", "2", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"shot {idx} failed:\n{r.stderr.decode(errors='replace')[-3500:]}")
    print(f"[shot {idx:02d}] {dur:6.2f}s  {len(local_caps)} captions", flush=True)
    return out


def main(test_only: bool = False):
    BUILD.mkdir(exist_ok=True)
    clip_meta, total, audio_path = build_audio()
    all_captions = caption_schedule_all(clip_meta)
    shots = build_shots(clip_meta, total)
    prepare_backgrounds()
    print(f"[plan] {len(shots)} shots, {len(all_captions)} caption cards, {total:.2f}s "
          f"= {int(total//60)}:{total%60:04.1f}")

    todo = shots[:1] if test_only else shots
    results: list[Path] = []
    with ThreadPoolExecutor(max_workers=1 if test_only else 3) as ex:
        futures = [ex.submit(render_shot, s, all_captions) for s in todo]
        for fut in as_completed(futures):
            results.append(fut.result())
    if test_only:
        print("[test] rendered only shot 1:", results[0])
        return

    results.sort(key=lambda p: int(p.stem.split("_")[1]))
    seg_list = BUILD / "segments.txt"
    seg_list.write_text("".join(f"file '{p.resolve()}'\n" for p in results), encoding="utf-8")
    silent = BUILD / "silent_video.mp4"
    run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(seg_list),
         "-c", "copy", "-movflags", "+faststart", str(silent)])
    run([FF, "-y", "-v", "error", "-i", str(silent), "-i", str(audio_path),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(SR), "-shortest", "-movflags", "+faststart", str(OUT)])
    (BUILD / "video_info.json").write_text(
        json.dumps({"duration": total, "size": OUT.stat().st_size}, indent=2), encoding="utf-8")
    print(f"[done] {OUT} ({OUT.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    main(ap.parse_args().test)
