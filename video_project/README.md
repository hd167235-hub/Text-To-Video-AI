# Đường về với mẹ chữ — video thuyết trình (Nhóm 1)

Video dựng từ kịch bản `kich-ban-video-duong-ve-voi-me-chu.md`.

**Thành phẩm:** [`../duong-ve-voi-me-chu.mp4`](../duong-ve-voi-me-chu.mp4)

| Thông số | Giá trị |
|---|---|
| Thời lượng | 3:40 (dưới 5 phút theo yêu cầu) |
| Định dạng | MP4 · H.264 + AAC · 1280×720 (16:9) · 24 fps |
| Giọng đọc | **Duy nhất 1 giọng AI nam** cho toàn bộ 10 đoạn (`voice-00`) |
| Hình ảnh | Minh họa AI + ảnh lấy trên mạng (bìa sách, chân dung tác giả) + bản đồ tự vẽ |
| Phụ đề | Chữ chạy ngay trong video + file `phu_de.srt` (40 dòng, có mốc thời gian) |
| Nhạc nền | Pad âm thanh nhẹ, tự tổng hợp, chỉ làm nền không lấn lời đọc |

## Các yêu cầu của kịch bản đã xử lý

- Toàn bộ lời thoại (kể cả phần tự giới thiệu 6 thành viên) đều do **một giọng nam AI** đọc.
- **Không dùng ảnh chân dung các thành viên**: phần giới thiệu nhóm chỉ hiện tên và phần phụ trách dưới dạng chữ chạy trên nền minh họa. Video cũng không quay người đọc, đúng định dạng "chữ chạy trên nền".
- Ảnh tác giả, ảnh bìa lấy trên mạng; các cảnh rừng núi, hang đá, học sinh, đèo dốc, "mẹ chữ"… là minh họa tự tạo.
- Chữ chạy theo từng phần: tác phẩm – tác giả – nhân vật – tóm tắt – nghệ thuật – giá trị – cảm ơn.

## Cấu trúc 13 cảnh

| Cảnh | Nội dung | Nền |
|---|---|---|
| 1 | Tiêu đề, bìa tác phẩm | núi rừng Việt Bắc lúc bình minh |
| 2 | Nhóm 1 và phân công (chữ, không ảnh người) | núi rừng (tông lạnh) |
| 3 | Nhà văn Vi Hồng + chân dung thật | bàn viết bản thảo |
| 4–5 | Bối cảnh hang đá / lộ trình Cao Bằng → Thái Nguyên | lớp học hang đá / bản đồ tự vẽ |
| 6–7 | Nhân vật, hình ảnh "mẹ chữ" | học sinh đi đường rừng / ánh sáng mẹ chữ |
| 8 | Cốt truyện 250–300 km | đèo dốc, suối lũ |
| 9–10 | Thử thách, nghị lực, trích dẫn | rừng đêm / bình minh |
| 11 | Nghệ thuật (4 ý) | sách, vải thổ cẩm Tày |
| 12 | Giá trị & ý nghĩa | bình minh thung lũng |
| 13 | Lời cảm ơn + credits | núi rừng Việt Bắc |

## Cấu trúc thư mục

```
video_project/
├── README.md                  # tài liệu này
├── kich-ban.md                # kịch bản gốc do người dùng cung cấp
├── phu_de.srt                 # phụ đề rời (nếu cần dùng riêng)
├── build_video.py             # toàn bộ pipeline dựng video
├── audio/clip01..10.mp3       # 10 đoạn giọng AI nam
├── assets/
│   ├── 01..09_*.jpg           # 9 minh họa AI (phong cách màu nước Việt Bắc)
│   ├── web/bia_sach.jpg       # ảnh bìa tác phẩm
│   ├── web/chan_dung_vi_hong.jpg
│   └── fonts/*.ttf            # Be Vietnam Pro (hỗ trợ đầy đủ tiếng Việt)
└── build/                     # file trung gian (bị git bỏ qua)
```

## Dựng lại video

```bash
python3 -m pip install pillow numpy imageio-ffmpeg fonttools brotli
python3 video_project/build_video.py
```

`build_video.py` tự ghép 10 file mp3, tạo nhạc nền, vẽ các lớp chữ bằng Pillow,
dùng FFmpeg (Ken Burns, fade, caption theo thời gian) để render từng cảnh rồi ghép
và mix âm thanh. Chạy `python3 video_project/build_video.py --test` để render thử 1 cảnh.

## Nguồn ảnh & ghi công

- Ảnh bìa *Đường về với mẹ chữ* (NXB Kim Đồng): [Báo Văn hóa Nghệ thuật](https://vanhoanghethuat.vn/tac-gia/la-nguyet-anh-016D51.html).
- Chân dung nhà văn Vi Hồng: [nguoinoitieng.tv](https://nguoinoitieng.tv/nghe-nghiep/nha-van/vi-hong/a9s9) (đã cắt bỏ watermark, chỉnh tông màu).
- Thông tin tiểu sử đối chiếu thêm: [Báo Cao Bằng](https://baocaobang.vn/-35024.html).
- 9 ảnh minh họa còn lại, bản đồ parchment và nhạc nền: tự tạo bằng AI / code trong dự án này.
- Phông chữ: **Be Vietnam Pro** (Google Fonts, giấy phép SIL Open Font License).

> Lưu ý: ảnh bìa và chân dung chỉ dùng cho mục đích thuyết trình học tập, vui lòng giữ
> ghi công nếu phát hành video rộng rãi.
