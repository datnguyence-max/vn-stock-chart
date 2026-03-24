# VN Stock Chart

Phan mem bieu do co phieu Viet Nam — nguon du lieu TCBS/KBS qua vnstock.

## Tinh nang
- Nhap nhieu ma co phieu VN cung luc (DCM, DPM, VRE, FPT...)
- Bieu do nen Nhat + duong gia
- 8 khung thoi gian: 1 ngay den 5 nam
- MA20, MA50, MA200
- Volume, so sanh % nhieu ma
- Tu dong lam moi moi 5 phut
- Giao dien dark mode

## Cach su dung

### Option 1: Tai file EXE (khong can cai Python)
1. Vao tab **Actions** tren GitHub
2. Chon workflow run moi nhat
3. Download **VNStockChart-Windows** artifact
4. Giai nen va chay `VNStockChart.exe`

### Option 2: Chay bang Python
```bash
pip install -r requirements.txt
python launcher.py
```

### Option 3: Build EXE tren may local (Windows)
```
build_local.bat
```

## Cau truc
```
vn_stock_app/
├── app.py              # Ung dung chinh (Dash)
├── launcher.py         # Entry point cho EXE
├── requirements.txt    # Thu vien can thiet
├── build_local.bat     # Script build EXE tren Windows
└── .github/
    └── workflows/
        └── build.yml   # GitHub Actions tu dong build
```

## Nguon du lieu
Du lieu lay tu **vnstock** qua cac nguon: KBS → TCBS → VCI (tu dong fallback).
