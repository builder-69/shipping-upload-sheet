"""
롯데택배 통합주문서 생성 API 및 명령행 실행 진입점.
"""
from __future__ import annotations

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Callable
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

try:
    from .ably_parser import parse_ably_orders
    from .excel_writer import create_integrated_order_excel
    from .hyber_parser import parse_hyber_orders
    from .naver_parser import parse_naver_orders
except ImportError:
    from ably_parser import parse_ably_orders
    from excel_writer import create_integrated_order_excel
    from hyber_parser import parse_hyber_orders
    from naver_parser import parse_naver_orders


logger = logging.getLogger(__name__)

INTEGRATED_COLUMNS = [
    "주문번호",
    "받는사람",
    "전화번호1",
    "우편번호",
    "주소",
    "상품명1",
    "상품상세1",
    "내품수량1",
    "배송메시지",
    "수량(A타입)",
]

app = FastAPI(title="Shipping Upload Sheet API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Total-Orders", "X-Naver-Orders", "X-Hyber-Orders", "X-Ably-Orders"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
BACKEND_DIR = Path(__file__).resolve().parent
TEMP_DIR = BACKEND_DIR / "temp"
OUTPUT_DIR = BACKEND_DIR / "outputs"


def _empty_parsed_orders() -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.DataFrame(columns=INTEGRATED_COLUMNS), pd.DataFrame()


def _parse_or_empty(
    file_path: Path | None,
    parser: Callable[[str], tuple[pd.DataFrame, pd.DataFrame]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if file_path is None:
        return _empty_parsed_orders()
    return parser(str(file_path))


def generate_orders(
    naver_path: Path | None,
    hyber_path: Path | None,
    ably_path: Path | None,
    output_path: Path,
) -> dict[str, int]:
    """Run the existing parsers and Excel writer without changing their mappings."""
    naver_converted, naver_original = _parse_or_empty(naver_path, parse_naver_orders)
    hyber_converted, hyber_original = _parse_or_empty(hyber_path, parse_hyber_orders)
    ably_converted, ably_original = _parse_or_empty(ably_path, parse_ably_orders)

    create_integrated_order_excel(
        naver_converted,
        naver_original,
        hyber_converted,
        hyber_original,
        ably_converted,
        ably_original,
        str(output_path),
    )

    counts = {
        "naver": len(naver_converted),
        "hyber": len(hyber_converted),
        "ably": len(ably_converted),
    }
    counts["total"] = sum(counts.values())
    return counts


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    try:
        with destination.open("wb") as output_file:
            while chunk := await upload.read(1024 * 1024):
                output_file.write(chunk)
    finally:
        await upload.close()


@app.get("/", include_in_schema=False)
async def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/lotte_shipping_web.html", include_in_schema=False)
async def legacy_frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/generate", response_model=None)
async def generate_shipping_excel(
    naver_file: Annotated[UploadFile | None, File()] = None,
    hyber_file: Annotated[UploadFile | None, File()] = None,
    ably_file: Annotated[UploadFile | None, File()] = None,
) -> FileResponse | JSONResponse:
    uploads = {
        "naver": naver_file,
        "hyber": hyber_file,
        "ably": ably_file,
    }
    if not any(uploads.values()):
        return JSONResponse(
            status_code=400,
            content={"message": "최소 1개의 주문서 파일을 업로드해주세요."},
        )

    request_id = uuid4().hex
    temp_dir = TEMP_DIR / request_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: dict[str, Path | None] = {"naver": None, "hyber": None, "ably": None}
    output_path: Path | None = None

    try:
        for platform, upload in uploads.items():
            if upload is None:
                continue
            suffix = Path(upload.filename or "").suffix or ".xlsx"
            saved_path = temp_dir / f"{platform}{suffix}"
            await _save_upload(upload, saved_path)
            saved_paths[platform] = saved_path

        filename = f"통합주문서_{datetime.now():%Y%m%d_%H%M%S}_{request_id[:8]}.xlsx"
        output_path = OUTPUT_DIR / filename
        counts = generate_orders(
            saved_paths["naver"],
            saved_paths["hyber"],
            saved_paths["ably"],
            output_path,
        )
    except Exception as exc:
        if output_path and output_path.exists():
            output_path.unlink()
        logger.exception("Failed to generate the integrated order sheet")
        return JSONResponse(
            status_code=400,
            content={"message": f"주문서 처리 중 오류가 발생했습니다: {exc}"},
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "X-Total-Orders": str(counts["total"]),
            "X-Naver-Orders": str(counts["naver"]),
            "X-Hyber-Orders": str(counts["hyber"]),
            "X-Ably-Orders": str(counts["ably"]),
        },
    )


def main(naver_path: str, hyber_path: str, ably_path: str, output_path: str | None = None) -> str:
    """Maintain the original three-file command-line generation workflow."""
    target = Path(output_path) if output_path else Path(f"통합주문서_{datetime.now():%Y%m%d}.xlsx")
    generate_orders(Path(naver_path), Path(hyber_path), Path(ably_path), target)
    return str(target)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("사용법: python main.py <네이버파일> <하이버파일> <에이블리파일> [출력파일]")
        sys.exit(1)

    result = main(*sys.argv[1:4], sys.argv[4] if len(sys.argv) > 4 else None)
    print(f"생성된 파일: {result}")
