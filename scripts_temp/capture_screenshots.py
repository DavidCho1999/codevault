"""
capture_screenshots.py - Part 9 섹션 스크린샷 캡처
- Playwright 사용
- 주요 섹션 스크린샷 저장
- PDF 대조용 증거 자료

사용법: python capture_screenshots.py
(dev 서버가 localhost:3001에서 실행 중이어야 함)
"""

import os
import sys
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright가 설치되어 있지 않습니다.")
    print("설치: pip install playwright && playwright install chromium")
    sys.exit(1)

# 설정
BASE_URL = "http://localhost:3001"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'screenshots')

# 캡처할 섹션 목록
SECTIONS = [
    "9.1.1",
    "9.3.1",
    "9.4.3",
    "9.6.1",
    "9.10.9",
    "9.15.3",
    "9.15.4",
    "9.23.3",
    "9.23.4",
    "9.25.2",
]


def capture_screenshots():
    """모든 섹션 스크린샷 캡처"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Part 9 섹션 스크린샷 캡처")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Sections: {len(SECTIONS)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        results = []

        for section_id in SECTIONS:
            url = f"{BASE_URL}/code/{section_id}"
            filename = f"{section_id.replace('.', '_')}_{timestamp}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)

            print(f"\n캡처 중: {section_id}...")

            try:
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=10000)

                # 콘텐츠 영역까지 스크롤
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)

                # 전체 페이지 스크린샷
                page.screenshot(path=filepath, full_page=True)

                results.append({
                    "section": section_id,
                    "status": "success",
                    "file": filename
                })
                print(f"  ✅ 저장됨: {filename}")

            except Exception as e:
                results.append({
                    "section": section_id,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"  ❌ 실패: {e}")

        browser.close()

    # 결과 요약
    print("\n" + "=" * 60)
    print("캡처 결과")
    print("=" * 60)

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    print(f"  성공: {success}/{len(SECTIONS)}")
    print(f"  실패: {failed}/{len(SECTIONS)}")

    if failed > 0:
        print("\n실패 목록:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['section']}: {r['error']}")

    # 결과 파일 저장
    result_file = os.path.join(OUTPUT_DIR, f"capture_result_{timestamp}.txt")
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"Part 9 Screenshot Capture Result\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Success: {success}/{len(SECTIONS)}\n\n")
        for r in results:
            f.write(f"{r['section']}: {r['status']}\n")
            if r['status'] == 'success':
                f.write(f"  File: {r['file']}\n")
            else:
                f.write(f"  Error: {r.get('error', 'Unknown')}\n")

    print(f"\n결과 파일: {result_file}")

    return success == len(SECTIONS)


if __name__ == "__main__":
    success = capture_screenshots()
    sys.exit(0 if success else 1)
