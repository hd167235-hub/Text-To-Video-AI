# Đường về với mẹ chữ — video thuyết trình (Nhóm 1)

Video dựng từ `kich-ban.md` (kịch bản gốc) và `cot-truyen-bo-sung.md` (phần cốt truyện mở rộng do người dùng cung cấp).

**Thành phẩm:** [`../duong-ve-voi-me-chu.mp4`](../duong-ve-voi-me-chu.mp4)

| Thông số | Giá trị |
|---|---|
| Thời lượng | **4:30.6** (nằm trong khoảng 4:00 – 4:40 theo yêu cầu) |
| Định dạng | MP4 · H.264 + AAC · 1280×720 (16:9) · 24 fps · ~55 MB |
| Giọng đọc | **Duy nhất 1 giọng AI nam** (`voice-00`) cho toàn bộ 14 đoạn |
| Hình ảnh | 16 nền minh họa (9 + 7 ảnh mới) + bản đồ tự vẽ + ảnh bìa/chân dung lấy trên mạng |
| Cấu trúc | 14 đoạn lời đọc · **18 cảnh** · 60 thẻ phụ đề chạy theo giọng |
| Phụ đề | Chữ chạy ngay trong video + file `phu_de.srt` (60 dòng, có mốc thời gian) |
| Nhạc nền | Pad âm thanh nhẹ tự tổng hợp, không lấn lời đọc |

## Các yêu cầu đã xử lý

- Toàn bộ lời thoại (kể cả đoạn tự giới thiệu 6 thành viên và 6 đoạn cốt truyện mới) đều do **một giọng nam AI** đọc.
- **Không dùng ảnh chân dung các thành viên**: phần giới thiệu nhóm chỉ hiện tên + phần phụ trách dưới dạng chữ chạy trên nền. Video không quay người đọc, đúng định dạng "chữ chạy trên nền".
- Phần cốt truyện được **thay và mở rộng** theo đúng 5 ý người dùng gửi, chia thành 6 đoạn: (1) Quyết tâm đi tìm mẹ chữ, (2) Chín ngày đêm / hoãn thi, (3) Đối mặt hổ dữ, (4) Rết hổ ở đèo Giàng, (5) Vượt đói rét, (6) Không bỏ dở việc học. Các chi tiết mới đều có slide riêng: Phan Soong, Hỏn, bạn Lư, Bế Tâm, chõng tre, chăn thủng, lều quán…
- Đoạn **Nghệ thuật** được thu lại để đổi chi tiết thành "hổ dữ / rết hổ đèo Giàng / chõng tre", tránh mâu thuẫn với cốt truyện mới.
- **Thêm 7 ảnh minh họa mới** (`10_` … `16_`) cho riêng phần cốt truyện: làng bản lúc chia tay, lều quán đêm, cổng trường sương mù, cuộc đối mặt hổ, xe đạp + rết hổ đèo Giàng, gian bếp rét, học dưới đèn dầu.
- Để nhét đủ nội dung mà vẫn ≤ 4:40: `atempo=1.12` (tăng nhịp đọc nhẹ, không đổi cao độ), khoảng nghỉ giữa đoạn 0,3 s, mở đầu 1,2 s, kết 2 s → **4:30.6**.

## Cấu trúc 18 cảnh

| STT | Nội dung | Nền |
|---|---|---|
| 1 | Tiêu đề + bìa tác phẩm | núi rừng Việt Bắc bình minh |
| 2 | Nhóm 1 & phân công (chữ, không ảnh người) | núi rừng tông lạnh |
| 3 | Nhà văn Vi Hồng + chân dung thật | bàn viết bản thảo |
| 4–5 | Bối cảnh hang đá / lộ trình Cao Bằng → Thái Nguyên | hang đá / bản đồ tự vẽ |
| 6–7 | Nhân vật, hình ảnh "mẹ chữ" | học sinh đi rừng / ánh sáng mẹ chữ |
| 8 | **Quyết tâm đi tìm mẹ chữ** | làng bản Tày lúc chia tay |
| 9–10 | **Chín ngày đêm, 250–300 km** | lều quán đêm / đèo dốc |
| 11 | **Hoãn thi, lại trở về** | cổng trường sương mù |
| 12 | **Đối mặt với hổ dữ** | dân bản + học sinh chống trả hổ |
| 13 | **Rết hổ ở đèo Giàng** | xe đạp, rết hổ, đèo chiều tà |
| 14–15 | **Vượt đói rét / không bỏ dở việc học** | gian bếp chõng tre / học dưới đèn dầu |
| 16 | Nghệ thuật (4 ý, đã cập nhật) | sách, vải thổ cẩm Tày |
| 17 | Giá trị & ý nghĩa | bình minh thung lũng |
| 18 | Lời cảm ơn + credits | núi rừng Việt Bắc |

## Cấu trúc thư mục

```
video_project/
├── README.md                   # tài liệu này
├── kich-ban.md                 # kịch bản gốc
├── cot-truyen-bo-sung.md       # phần cốt truyện mở rộng (có nguồn)
├── phu_de.srt                  # phụ đề rời
├── build_video.py              # toàn bộ pipeline dựng video
├── audio/
│   ├── clip01..05, clip09, clip10.mp3   # 7 đoạn giữ nguyên
│   ├── plot01..06.mp3                   # 6 đoạn cốt truyện mới
│   └── art_new.mp3                      # đoạn nghệ thuật cập nhật
├── assets/
│   ├── 01..09_*.jpg            # 9 minh họa ban đầu
│   ├── 10..16_*.jpg            # 7 minh họa mới cho cốt truyện
│   ├── web/bia_sach.jpg, chan_dung_vi_hong.jpg
│   └── fonts/*.ttf             # Be Vietnam Pro (đầy đủ dấu tiếng Việt)
└── build/                      # file trung gian (git bỏ qua)
```

## Dựng lại video

```bash
python3 -m pip install pillow numpy imageio-ffmpeg
python3 video_project/build_video.py
```

`build_video.py` tự ghép các mp3 (có `atempo`), tạo nhạc nền, vẽ lớp chữ bằng Pillow, dùng FFmpeg (Ken Burns, fade, caption theo thời gian) render từng cảnh rồi ghép và mix âm thanh. `python3 video_project/build_video.py --test` chỉ render 1 cảnh để kiểm tra bố cục. Sau khi chạy, file `build/video_info.json` cấp thông tin thời lượng/dung lượng cho trang tải.

## Nguồn ảnh & ghi công

- Ảnh bìa *Đường về với mẹ chữ* (NXB Kim Đồng): [Báo Văn hóa Nghệ thuật](https://vanhoanghethuat.vn/tac-gia/la-nguyet-anh-016D51.html).
- Chân dung nhà văn Vi Hồng: [nguoinoitieng.tv](https://nguoinoitieng.tv/nghe-nghiep/nha-van/vi-hong/a9s9) (đã cắt watermark, chỉnh tông màu).
- **Tư liệu cốt truyện mở rộng**: [Xung quanh hành trình "Đường về với mẹ chữ" của Vi Hồng](https://vanhoanghethuat.vn/xung-quanh-hanh-trinh-duong-ve-voi-me-chu-cua-vi-hong-77749313.html).
- Tiểu sử đối chiếu: [Báo Cao Bằng](https://baocaobang.vn/-35024.html).
- 16 ảnh minh họa còn lại, bản đồ parchment và nhạc nền: tự tạo bằng AI / code trong dự án này.
- Phông chữ: **Be Vietnam Pro** (Google Fonts, SIL Open Font License).

> Ảnh bìa và chân dung chỉ dùng cho mục đích thuyết trình học tập; vui lòng giữ ghi công nếu phát hành rộng rãi.
