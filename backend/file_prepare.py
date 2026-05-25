from __future__ import annotations

import os
import zipfile
from pathlib import Path, PurePosixPath


SUPPORTED_ORDER_EXTENSIONS = {".xlsx", ".xls", ".csv"}


class FilePreparationError(Exception):
    """User-facing upload preparation failure."""


def _safe_output_path(output_dir: Path, member_name: str) -> Path:
    pure = PurePosixPath(member_name.replace("\\", "/"))
    filename = Path(pure.name).name
    if not filename:
        raise FilePreparationError("zip 내부 파일명을 확인할 수 없습니다.")
    return output_dir / filename


def _decrypt_excel_if_needed(source: Path, output_dir: Path, password: str | None) -> Path:
    try:
        import pandas as pd

        excel = pd.ExcelFile(source)
        excel.close()
        return source
    except Exception:
        pass

    try:
        import msoffcrypto
    except ImportError as exc:
        raise FilePreparationError("암호화된 엑셀 파일을 처리하려면 msoffcrypto-tool 설치가 필요합니다.") from exc

    with source.open("rb") as file:
        try:
            office_file = msoffcrypto.OfficeFile(file)
            is_encrypted = office_file.is_encrypted()
        except Exception as exc:
            raise FilePreparationError("네이버 주문서 파일을 열 수 없습니다.") from exc

        if not is_encrypted:
            raise FilePreparationError("네이버 주문서 파일을 열 수 없습니다.")

        if not password:
            raise FilePreparationError("네이버 주문서 비밀번호가 설정되어 있지 않습니다.")

        target = output_dir / source.name
        try:
            office_file.load_key(password=password)
            with target.open("wb") as output:
                office_file.decrypt(output)
        except Exception as exc:
            raise FilePreparationError("네이버 주문서 비밀번호가 올바르지 않거나 파일을 열 수 없습니다.") from exc

    return target


def _extract_zip(source: Path, output_dir: Path, password: str | None) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    password_bytes = password.encode("utf-8") if password else None

    try:
        import pyzipper

        zip_class = pyzipper.AESZipFile
    except ImportError:
        zip_class = zipfile.ZipFile

    extracted: list[Path] = []
    try:
        with zip_class(source) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            supported = [
                info for info in members
                if Path(info.filename).suffix.lower() in SUPPORTED_ORDER_EXTENSIONS
            ]
            if not supported:
                raise FilePreparationError("하이버 zip 내부에 xlsx/xls/csv 파일이 없습니다.")

            for info in supported:
                target = _safe_output_path(output_dir, info.filename)
                if target.exists():
                    stem = target.stem
                    suffix = target.suffix
                    index = 2
                    while target.exists():
                        target = output_dir / f"{stem}_{index}{suffix}"
                        index += 1
                try:
                    data = archive.read(info.filename, pwd=password_bytes)
                except TypeError:
                    if password_bytes and hasattr(archive, "setpassword"):
                        archive.setpassword(password_bytes)
                    data = archive.read(info.filename)
                except RuntimeError as exc:
                    if "password" in str(exc).lower() or "encrypted" in str(exc).lower():
                        if not password:
                            raise FilePreparationError("하이버 zip 비밀번호가 설정되어 있지 않습니다.") from exc
                        raise FilePreparationError("하이버 zip 비밀번호가 올바르지 않습니다.") from exc
                    raise

                if target.suffix.lower() == ".csv" and data.startswith(b"PK"):
                    target = target.with_suffix(".xlsx")
                target.write_bytes(data)
                extracted.append(target)
    except zipfile.BadZipFile as exc:
        raise FilePreparationError("하이버 zip 파일이 손상되었거나 올바른 zip 형식이 아닙니다.") from exc
    except FilePreparationError:
        raise
    except Exception as exc:
        raise FilePreparationError("하이버 zip 파일을 압축 해제할 수 없습니다.") from exc

    return extracted


def prepare_naver_order_file(source: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in {".xlsx", ".xls"}:
        return _decrypt_excel_if_needed(source, output_dir, os.getenv("NAVER_ORDER_PASSWORD"))
    return source


def prepare_hyber_order_file(source: Path, output_dir: Path) -> Path:
    if source.suffix.lower() != ".zip":
        return source

    extracted = _extract_zip(source, output_dir / source.stem, os.getenv("HYBER_ORDER_PASSWORD"))
    if len(extracted) != 1:
        raise FilePreparationError("하이버 zip 내부에는 주문서 파일이 1개만 있어야 합니다.")
    return extracted[0]
