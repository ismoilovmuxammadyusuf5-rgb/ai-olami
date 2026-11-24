# AI Olami

O‘zbekcha AI katalogi. GitHub Pages va public GitHub Actions bilan ishlaydi; API kaliti, pullik xizmat, obuna, alohida domen yoki kredit karta kerak emas. Katalogdagi tashqi mahsulotlarning o‘z tariflari bo‘lishi mumkin; sayt va uning yangilanishi bepul.

## Yangilanish

`.github/workflows/update-ai.yml` har soatning 17-daqiqasida, `main`ga o‘zgarish yuborilganda va **Actions → Run workflow** orqali ishlaydi. GitHub rejalashtirilgan ishlarni kechiktirishi yoki tashlab ketishi mumkin; public repoda 60 kun faollik bo‘lmasa schedule o‘chirilishi mumkin. Bu uzluksiz real vaqt monitoringi emas.

1. Bepul RSS manbalar alohida tekshiriladi. Bir manba xatosi qolganlarini to‘xtatmaydi.
2. Manzil va mahsulot nomlari bir xillashtirilib, takrorlar birlashtiriladi. Faqat nomi bor eski yozuvlar dalilsiz tasdiqlanmaydi.
3. Aniq AI vazifasi bor mahsulotlar mavjud sakkiz yo‘nalishdan biriga ajratiladi. Aniq AI bo‘lmagan yozuvlar rad qilinadi, noaniqlari `pending` qoladi. Bu qoidaviy saralash; mahsulotni amalda sinash yoki inson tekshiruvi emas.
4. Tasdiqlangan topilmalar `data/approved-ai.json`ga yoziladi va sahifadagi asosiy katalog, qidiruv va filtrlarga qo‘shiladi. Manba uzilganda oldingi katalog saqlanadi. Narx yoki foydalanuvchi soni taxmin qilinmaydi.
5. Takliflar faqat sozlangan rasmiy domenning o‘zidan qayta tekshiriladi. Narx/valyuta, shartlar va qatnashish mezonlari, vaqt zonali boshlanish/tugash sanalari hamda amaldagi holat bir taklifga tegishli aniq strukturali dalilda bo‘lishi kerak. Yetishmayotgan sana yoki shart taxmin qilinmaydi. Qo‘llanmaydigan sahifa formatlari ham `pending` qoladi.
6. Avval tasdiqlangan taklif ham har safar qayta tekshiriladi; tekshirib bo‘lmasa yashiriladi. Brauzer qo‘shimcha ravishda vaqt oralig‘i va 24 soatlik tekshiruv yangiligini tekshiradi. Tasdiqlangan aksiya bo‘lmasa bo‘sh holat ko‘rsatiladi.
7. Testlar va ma’lumot tekshiruvi o‘tgach ma’lumotlar commit qilinadi, ayni ish ichida Pagesga joylanadi. Bot commiti boshqa workflow’ni ishga tushirishiga tayanilmaydi.

## Fayllar

- `index.html`, `assets/`: mavjud dizayn va xavfsiz brauzer interfeysi.
- `scripts/`: faqat Python standart kutubxonasi bilan RSS, saralash va taklif dalillarini tekshirish.
- `data/ai-candidates.json`: topilmalar, holat va saralash sabablari.
- `data/approved-ai.json`: katalogga qo‘shiladigan topilmalar.
- `data/promo-candidates.json`: takliflar, dalillar va `pending/rejected/expired/approved` holatlari.
- `data/monitor-status.json`: oxirgi ish va manbalar holati. Xatolar Actions logi va ish xulosasida ham ko‘rsatiladi.

Namoyish uchun yaratilgan mahsulotlar, sun’iy tashriflar va qalbaki reytinglar olib tashlangan. Fikr qoldirish shu brauzer xotirasida saqlanadi; umumiy serverga yuborilmaydi va barcha foydalanuvchilarning reytingi sifatida ko‘rsatilmaydi. Avtomatik topilmalar manba matnini saqlaydi, shuning uchun ayrim tavsiflar inglizcha bo‘lishi mumkin.

## Mahalliy tekshirish

Python 3.12+ va Node.js 22 bilan, qo‘shimcha paketlarsiz:

```sh
python -m unittest discover -s tests -v
node --test tests/*.test.js
node --check assets/site.js
python -m scripts.update_catalog
python -m scripts.validate_data
python -m http.server 8000
```

So‘ng `http://localhost:8000`ni oching. `file://` orqali JSON yuklanishi brauzer tomonidan cheklanishi mumkin.

## GitHub sozlamalari

Repo public qolishi va **Settings → Pages → Source: GitHub Actions** bo‘lishi kerak. Workflow’ning `contents: write`, `pages: write`, `id-token: write` ruxsatlari commit va Pages joylash uchun ishlatiladi. Alohida secret yoki PAT talab qilinmaydi. Fork PR tekshiruvida manbalar yangilanmaydi, commit/deploy bajarilmaydi.

Standart public runner ishlatiladi; Pages artefakti bir kun saqlanadi. Saqlash limiti va GitHub siyosatlari alohida amal qiladi.

Rasmiy hujjatlar: [schedule cheklovlari](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [GITHUB_TOKEN bilan workflow ishga tushishi](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [Actions narxlash](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
