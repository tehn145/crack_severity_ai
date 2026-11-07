"""
Phase 3 — Structural Health Monitoring (SHM) Engine
Hệ thống Giám định Mức độ Nghiêm trọng Kết cấu Công trình

Logic:
1. Dual inference: Run BOTH Phase 1.2 (crack) + Phase 2 (spalling/rebar/corrosion) on each image
2. Hybrid Defect Fusion: Overlay masks from both models, detect spatial intersections
3. Structural Element Risk Multiplier: Weight by structural component type
4. Spatial Overlap Deduplication: ORB feature matching between consecutive images to avoid double-counting
5. Structural Collapse Index (SCI): Compute 0-100% score with 4 risk tiers

Tác giả: crack_severity_ai — khóa luận tốt nghiệp
"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Đường dẫn mặc định cho hai model
# ---------------------------------------------------------------------------
DEFAULT_PHASE1_WEIGHT = str(
    Path("d:/crack_severity_ai/weights/phase1/results phase 1.2 6nov2026/best.pt")
)
DEFAULT_PHASE2_WEIGHT = str(
    Path("d:/crack_severity_ai/weights/phase2/results phase 2 6nov2026/best.pt")
)

# ---------------------------------------------------------------------------
# Hệ số rủi ro theo loại cấu kiện kết cấu
# ---------------------------------------------------------------------------
RISK_MULTIPLIER: dict[str, float] = {
    "column": 3.0,            # Cột chịu lực
    "beam_column_joint": 3.5, # Nút dầm-cột (nguy hiểm nhất)
    "beam": 2.5,              # Dầm chính
    "girder": 2.5,            # Dầm phụ
    "stair": 2.0,             # Cầu thang
    "slab": 1.5,              # Sàn
    "wall": 1.0,              # Tường thứ yếu
    "other": 1.0,
}

# ---------------------------------------------------------------------------
# Hệ số nghiêm trọng theo loại tổ hợp hư hỏng
# ---------------------------------------------------------------------------
SEVERITY_FACTOR: dict[str, float] = {
    "crack": 1.0,
    "spalling": 1.2,
    "exposed_rebar": 1.8,
    "corrosion": 1.4,
    "compound_damage": 1.5,              # crack + spalling overlap
    "compound_structural_failure": 2.5,  # crack + spalling + rebar overlap
}

# ---------------------------------------------------------------------------
# Màu sắc vẽ chú thích (BGR)
# ---------------------------------------------------------------------------
COLOR_CRACK = (255, 80, 0)      # Xanh dương đậm — Phase 1 crack
COLOR_SPALLING = (0, 165, 255)  # Cam — spalling
COLOR_REBAR = (0, 0, 220)       # Đỏ — exposed rebar
COLOR_CORROSION = (19, 69, 139) # Nâu — corrosion
COLOR_COMPOUND = (0, 200, 100)  # Xanh lá — vùng giao nhau

# Class ID → tên theo Phase 2 model (crack=0, spalling=1, exposed_rebar=2, corrosion=3)
P2_CLASS_NAMES: dict[int, str] = {
    0: "crack",
    1: "spalling",
    2: "exposed_rebar",
    3: "corrosion",
}

# ---------------------------------------------------------------------------
# Các ngưỡng SCI — phân cấp rủi ro
# ---------------------------------------------------------------------------
SCI_TIERS = [
    {
        "level": 1, "label": "AN TOÀN", "color": "#16a34a",
        "min": 0.0, "max": 15.0,
        "recommendation": (
            "Công trình ở trạng thái an toàn. Duy trì chương trình giám sát định kỳ "
            "(quan trắc 6 tháng/lần). Ghi nhận vị trí và theo dõi tiến triển vết nứt."
        ),
    },
    {
        "level": 2, "label": "CẢNH BÁO", "color": "#ca8a04",
        "min": 15.0, "max": 35.0,
        "recommendation": (
            "Phát hiện hư hỏng ở mức cảnh báo. Khuyến nghị bơm epoxy trám vết nứt, "
            "kiểm tra chi tiết bề mặt bê-tông. Tăng tần suất giám sát lên 3 tháng/lần."
        ),
    },
    {
        "level": 3, "label": "NGUY HIỂM", "color": "#ea580c",
        "min": 35.0, "max": 60.0,
        "recommendation": (
            "Mức độ hư hỏng NGUY HIỂM. Yêu cầu đánh giá kết cấu bởi kỹ sư có chứng chỉ. "
            "Xem xét gia cường bằng sợi CFRP hoặc tấm thép. Hạn chế tải trọng khai thác "
            "cho đến khi có kết luận chính thức."
        ),
    },
    {
        "level": 4, "label": "KHẨN CẤP - SƠ TÁN", "color": "#dc2626",
        "min": 60.0, "max": 101.0,
        "recommendation": (
            "⚠️ TÌNH TRẠNG KHẨN CẤP — SƠ TÁN NGAY LẬP TỨC! Nguy cơ sụp đổ cục bộ hoặc "
            "toàn bộ kết cấu. Phong tỏa khu vực, liên hệ ngay cơ quan quản lý xây dựng và "
            "đội ứng phó khẩn cấp. KHÔNG sử dụng công trình cho đến khi được kỹ sư kết cấu "
            "cấp phép."
        ),
    },
]


def _get_sci_tier(sci_score: float) -> dict:
    """Trả về tier SCI tương ứng với điểm số đầu vào."""
    for tier in SCI_TIERS:
        if tier["min"] <= sci_score < tier["max"]:
            return tier
    return SCI_TIERS[-1]


def _mask_to_binary(mask_data: Any, h: int, w: int) -> np.ndarray:
    """Chuyển mask từ YOLO result về ảnh nhị phân (H, W) uint8."""
    if mask_data is None:
        return np.zeros((h, w), dtype=np.uint8)
    # mask_data có thể là tensor (H, W) hoặc numpy array
    arr = np.array(mask_data, dtype=np.float32)
    if arr.ndim == 2:
        binary = (arr > 0.5).astype(np.uint8) * 255
    else:
        binary = np.zeros((h, w), dtype=np.uint8)
    # Resize về kích thước ảnh gốc nếu cần
    if binary.shape[0] != h or binary.shape[1] != w:
        binary = cv2.resize(binary, (w, h), interpolation=cv2.INTER_NEAREST)
    return binary


def _poly_to_binary(poly_xy: np.ndarray, h: int, w: int) -> np.ndarray:
    """Vẽ polygon mask lên ảnh nhị phân (H, W)."""
    canvas = np.zeros((h, w), dtype=np.uint8)
    if poly_xy is not None and len(poly_xy) >= 3:
        pts = poly_xy.astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(canvas, [pts], 255)
    return canvas


def _compute_overlap_ratio_orb(img1_bgr: np.ndarray, img2_bgr: np.ndarray) -> float:
    """
    Ước tính tỉ lệ vùng chồng lấp giữa hai ảnh liên tiếp bằng ORB + BFMatcher.

    Trả về giá trị trong [0, 1]: 0 = không chồng lấp, 1 = chồng hoàn toàn.
    Dùng để tránh tính đôi hư hỏng khi các ảnh cùng chụp một vùng bề mặt.
    """
    try:
        g1 = cv2.cvtColor(img1_bgr, cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(g1, None)
        kp2, des2 = orb.detectAndCompute(g2, None)

        if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
            return 0.0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        if not matches:
            return 0.0

        # Lọc match tốt: distance < 2 * median distance
        distances = [m.distance for m in matches]
        med_dist = float(np.median(distances))
        good = [m for m in matches if m.distance <= 2.0 * med_dist]

        # Tỉ lệ match tốt / tổng keypoints nhỏ nhất → proxy cho overlap
        min_kps = min(len(kp1), len(kp2))
        if min_kps == 0:
            return 0.0
        overlap_ratio = min(1.0, len(good) / min_kps)
        return float(overlap_ratio)

    except Exception as exc:
        logger.warning("ORB overlap estimation failed: %s", exc)
        return 0.0


def _annotate_image(
    img_bgr: np.ndarray,
    detections_p1: list[dict],
    detections_p2: list[dict],
    compound_zones: list[dict],
    sci_contribution: float,
) -> str:
    """
    Vẽ mask của cả hai model lên ảnh, thêm badge SCI.
    Trả về chuỗi base64 JPEG.
    """
    h, w = img_bgr.shape[:2]
    overlay = img_bgr.copy()
    alpha = 0.40  # độ trong suốt của mask

    # Màu theo loại hư hỏng (BGR)
    color_map = {
        "crack": COLOR_CRACK,
        "spalling": COLOR_SPALLING,
        "exposed_rebar": COLOR_REBAR,
        "corrosion": COLOR_CORROSION,
    }

    def _fill_mask(mask_b64: str | None, color: tuple[int, int, int]) -> None:
        """Giải mã mask binary (nếu có) và vẽ màu lên overlay."""
        if not mask_b64:
            return
        try:
            raw = base64.b64decode(mask_b64)
            arr = np.frombuffer(raw, dtype=np.uint8)
            mask = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                return
            if mask.shape[:2] != (h, w):
                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
            colored = np.zeros_like(img_bgr)
            colored[mask > 127] = color
            cv2.addWeighted(colored, alpha, overlay, 1 - alpha, 0, overlay)
        except Exception:
            pass

    def _fill_poly(pts: list[list[float]], color: tuple[int, int, int]) -> None:
        if not pts:
            return
        poly = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
        colored = np.zeros_like(img_bgr)
        cv2.fillPoly(colored, [poly], color)
        cv2.addWeighted(colored, alpha, overlay, 1 - alpha, 0, overlay)
        cv2.polylines(overlay, [poly], isClosed=True, color=color, thickness=2)

    # Vẽ Phase 1 (crack — xanh dương)
    for det in detections_p1:
        _fill_mask(det.get("mask_b64"), COLOR_CRACK)
        pts = det.get("mask_points")
        if pts:
            _fill_poly(pts, COLOR_CRACK)

    # Vẽ Phase 2 (spalling/rebar/corrosion)
    for det in detections_p2:
        cls_name = det.get("class_name", "spalling")
        color = color_map.get(cls_name, COLOR_SPALLING)
        _fill_mask(det.get("mask_b64"), color)
        pts = det.get("mask_points")
        if pts:
            _fill_poly(pts, color)

    # Vẽ vùng giao nhau (compound zones — xanh lá)
    for zone in compound_zones:
        pts = zone.get("contour_pts", [])
        if pts:
            _fill_poly(pts, COLOR_COMPOUND)

    # Badge SCI
    tier = _get_sci_tier(sci_contribution * 100)
    badge_text = f"SCI: {sci_contribution * 100:.1f}% | {tier['label']}"
    # Chuyển màu HEX → BGR
    hex_col = tier["color"].lstrip("#")
    r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
    badge_color_bgr = (b, g, r)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, min(1.2, w / 640))
    thickness = 2
    (tw, th), _ = cv2.getTextSize(badge_text, font, font_scale, thickness)
    pad = 8
    cv2.rectangle(overlay, (pad, pad), (pad + tw + pad, pad + th + pad * 2),
                  badge_color_bgr, -1)
    cv2.putText(overlay, badge_text, (pad * 2, pad + th + pad // 2),
                font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    # Encode JPEG → base64
    ok, buf = cv2.imencode(".jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


class SHMEngine:
    """
    Phase 3 Structural Health Monitoring Engine.

    Thực hiện dual inference (Phase 1 + Phase 2), fusion hư hỏng,
    và tính chỉ số SCI (Structural Collapse Index).
    """

    def __init__(
        self,
        phase1_weight: str = DEFAULT_PHASE1_WEIGHT,
        phase2_weight: str = DEFAULT_PHASE2_WEIGHT,
        conf1: float = 0.25,
        conf2: float = 0.25,
        device: str = "cpu",
    ) -> None:
        """
        Khởi tạo engine với đường dẫn weight và ngưỡng confidence.

        Args:
            phase1_weight: Đường dẫn file .pt của Phase 1.2 (crack detection).
            phase2_weight: Đường dẫn file .pt của Phase 2 (multi-defect).
            conf1: Ngưỡng confidence cho Phase 1.
            conf2: Ngưỡng confidence cho Phase 2.
            device: 'cpu' hoặc 'cuda:0' v.v.
        """
        self.phase1_weight = phase1_weight
        self.phase2_weight = phase2_weight
        self.conf1 = conf1
        self.conf2 = conf2
        self.device = device

        # Lazy-load — chưa tải model ngay để khởi động nhanh
        self._model1 = None
        self._model2 = None

    # ------------------------------------------------------------------
    # Private: Lazy-load models
    # ------------------------------------------------------------------

    def _get_model1(self):
        """Tải Phase 1.2 model lần đầu khi cần."""
        if self._model1 is None:
            from ultralytics import YOLO

            p = Path(self.phase1_weight)
            if not p.exists():
                raise FileNotFoundError(
                    f"[SHM] Không tìm thấy Phase 1 weight: {p}. "
                    "Kiểm tra đường dẫn hoặc biến môi trường."
                )
            logger.info("[SHM] Đang tải Phase 1 model: %s", p)
            self._model1 = YOLO(str(p))
        return self._model1

    def _get_model2(self):
        """Tải Phase 2 model lần đầu khi cần."""
        if self._model2 is None:
            from ultralytics import YOLO

            p = Path(self.phase2_weight)
            if not p.exists():
                raise FileNotFoundError(
                    f"[SHM] Không tìm thấy Phase 2 weight: {p}. "
                    "Kiểm tra đường dẫn hoặc biến môi trường."
                )
            logger.info("[SHM] Đang tải Phase 2 model: %s", p)
            self._model2 = YOLO(str(p))
        return self._model2

    # ------------------------------------------------------------------
    # Private: Run inference helpers
    # ------------------------------------------------------------------

    def _run_phase1(self, img_bgr: np.ndarray) -> list[dict]:
        """
        Chạy Phase 1.2 trên ảnh BGR.
        Trả về list detection (crack), mỗi phần tử gồm: conf, bbox, mask_points, defect_area_px, defect_ratio.
        """
        h, w = img_bgr.shape[:2]
        model = self._get_model1()
        res = model.predict(img_bgr, conf=self.conf1, verbose=False, device=self.device)[0]
        detections: list[dict] = []
        total_px = h * w

        n_masks = 0 if res.masks is None else len(res.masks)
        for i, box in enumerate(res.boxes):
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            det: dict[str, Any] = {
                "class_id": 0,
                "class_name": "crack",
                "conf": round(float(box.conf[0]), 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "defect_area_px": 0,
                "defect_ratio": 0.0,
                "mask_points": [],
            }
            if i < n_masks:
                poly = res.masks.xy[i]  # (N, 2) pixel coords
                det["mask_points"] = [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in poly]
                # Tính diện tích từ binary mask
                bin_mask = _poly_to_binary(poly, h, w)
                area = int(np.count_nonzero(bin_mask))
                det["defect_area_px"] = area
                det["defect_ratio"] = round(area / max(total_px, 1), 6)
            detections.append(det)

        return detections

    def _run_phase2(self, img_bgr: np.ndarray) -> list[dict]:
        """
        Chạy Phase 2 (multi-defect) trên ảnh BGR.
        Trả về list detection (crack/spalling/rebar/corrosion).
        """
        h, w = img_bgr.shape[:2]
        model = self._get_model2()
        res = model.predict(img_bgr, conf=self.conf2, verbose=False, device=self.device)[0]
        detections: list[dict] = []
        total_px = h * w

        n_masks = 0 if res.masks is None else len(res.masks)
        for i, box in enumerate(res.boxes):
            cls_id = int(box.cls[0])
            cls_name = P2_CLASS_NAMES.get(cls_id, f"class_{cls_id}")
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            det: dict[str, Any] = {
                "class_id": cls_id,
                "class_name": cls_name,
                "conf": round(float(box.conf[0]), 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "defect_area_px": 0,
                "defect_ratio": 0.0,
                "mask_points": [],
            }
            if i < n_masks:
                poly = res.masks.xy[i]
                det["mask_points"] = [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in poly]
                bin_mask = _poly_to_binary(poly, h, w)
                area = int(np.count_nonzero(bin_mask))
                det["defect_area_px"] = area
                det["defect_ratio"] = round(area / max(total_px, 1), 6)
            detections.append(det)

        return detections

    # ------------------------------------------------------------------
    # Private: Fusion logic
    # ------------------------------------------------------------------

    def _fuse_detections(
        self,
        detections_p1: list[dict],
        detections_p2: list[dict],
        h: int,
        w: int,
    ) -> tuple[list[dict], list[dict]]:
        """
        Phân loại tổ hợp hư hỏng (compound damage) dựa trên giao nhau mask.

        Returns:
            fused_dets: list các detection đã gắn defect_type + severity_factor
            compound_zones: list vùng giao nhau có cường độ cao
        """
        total_px = h * w

        # Tạo binary mask tổng hợp cho từng loại
        crack_mask = np.zeros((h, w), dtype=np.uint8)
        spalling_mask = np.zeros((h, w), dtype=np.uint8)
        rebar_mask = np.zeros((h, w), dtype=np.uint8)
        corrosion_mask = np.zeros((h, w), dtype=np.uint8)

        for det in detections_p1:
            pts = det.get("mask_points", [])
            if pts:
                poly = np.array(pts, dtype=np.float32)
                bin_m = _poly_to_binary(poly, h, w)
                crack_mask = cv2.bitwise_or(crack_mask, bin_m)

        for det in detections_p2:
            pts = det.get("mask_points", [])
            if not pts:
                continue
            poly = np.array(pts, dtype=np.float32)
            bin_m = _poly_to_binary(poly, h, w)
            cls = det.get("class_name", "spalling")
            if cls == "spalling":
                spalling_mask = cv2.bitwise_or(spalling_mask, bin_m)
            elif cls == "exposed_rebar":
                rebar_mask = cv2.bitwise_or(rebar_mask, bin_m)
            elif cls == "corrosion":
                corrosion_mask = cv2.bitwise_or(corrosion_mask, bin_m)

        compound_zones: list[dict] = []

        # Tính vùng giao nhau: crack ∩ spalling ∩ rebar → compound_structural_failure
        csf_mask = cv2.bitwise_and(crack_mask, cv2.bitwise_and(spalling_mask, rebar_mask))
        csf_area = int(np.count_nonzero(csf_mask))
        if csf_area > 0:
            contours, _ = cv2.findContours(csf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) > 50:
                    compound_zones.append({
                        "defect_type": "compound_structural_failure",
                        "area_px": int(cv2.contourArea(cnt)),
                        "defect_ratio": round(int(cv2.contourArea(cnt)) / max(total_px, 1), 6),
                        "severity_factor": SEVERITY_FACTOR["compound_structural_failure"],
                        "contour_pts": cnt.reshape(-1, 2).tolist(),
                    })

        # crack ∩ spalling → compound_damage (nếu không phải CSF)
        cd_mask = cv2.bitwise_and(crack_mask, spalling_mask)
        # Loại bỏ phần đã tính ở CSF
        cd_mask = cv2.bitwise_and(cd_mask, cv2.bitwise_not(csf_mask))
        cd_area = int(np.count_nonzero(cd_mask))
        if cd_area > 0:
            contours, _ = cv2.findContours(cd_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) > 50:
                    compound_zones.append({
                        "defect_type": "compound_damage",
                        "area_px": int(cv2.contourArea(cnt)),
                        "defect_ratio": round(int(cv2.contourArea(cnt)) / max(total_px, 1), 6),
                        "severity_factor": SEVERITY_FACTOR["compound_damage"],
                        "contour_pts": cnt.reshape(-1, 2).tolist(),
                    })

        # Gắn defect_type cho từng detection riêng lẻ
        fused_dets: list[dict] = []
        for det in detections_p1:
            d = dict(det)
            d["defect_type"] = "crack"
            d["severity_factor"] = SEVERITY_FACTOR["crack"]
            fused_dets.append(d)
        for det in detections_p2:
            d = dict(det)
            cls = d.get("class_name", "spalling")
            d["defect_type"] = cls
            d["severity_factor"] = SEVERITY_FACTOR.get(cls, 1.0)
            fused_dets.append(d)

        return fused_dets, compound_zones

    # ------------------------------------------------------------------
    # Public: Phân tích đơn ảnh
    # ------------------------------------------------------------------

    def analyze_image(
        self,
        img_bgr: np.ndarray,
        component_type: str = "wall",
    ) -> dict:
        """
        Phân tích SHM cho một ảnh đơn.

        Args:
            img_bgr: Ảnh BGR (numpy array).
            component_type: Loại cấu kiện kết cấu (vd 'column', 'beam', 'wall'...).

        Returns:
            dict gồm: sci_contribution, detections_p1, detections_p2,
                      compound_zones, annotated_b64, và các số liệu chi tiết.
        """
        t0 = time.perf_counter()
        h, w = img_bgr.shape[:2]
        total_px = h * w

        ai_component_info = None
        if component_type == "auto" or not component_type:
            try:
                from app.component_classifier import AIComponentClassifier
                ai_component_info = AIComponentClassifier.classify(img_bgr)
                component_type = ai_component_info["component_type"]
                risk_mult = ai_component_info["risk_multiplier"]
            except Exception as exc:
                logger.warning("AIComponentClassifier không chạy được: %s", exc)
                component_type = "wall"
                risk_mult = 1.0
        else:
            risk_mult = RISK_MULTIPLIER.get(component_type, 1.0)

        # 1. Dual inference
        try:
            dets_p1 = self._run_phase1(img_bgr)
        except Exception as exc:
            logger.error("[SHM Phase1] Lỗi inference: %s", exc)
            dets_p1 = []

        try:
            dets_p2 = self._run_phase2(img_bgr)
        except Exception as exc:
            logger.error("[SHM Phase2] Lỗi inference: %s", exc)
            dets_p2 = []

        # 2. Fusion + compound detection
        fused_dets, compound_zones = self._fuse_detections(dets_p1, dets_p2, h, w)

        # 3. Tính SCI contribution cho ảnh này
        raw_score = 0.0
        for det in fused_dets:
            dr = det.get("defect_ratio", 0.0)
            sf = det.get("severity_factor", 1.0)
            raw_score += dr * risk_mult * sf
        # Tính thêm từ vùng compound
        for zone in compound_zones:
            dr = zone.get("defect_ratio", 0.0)
            sf = zone.get("severity_factor", 1.0)
            raw_score += dr * risk_mult * sf

        # Normalize thành [0, 1] trước khi trả về (nhân 100 khi tổng hợp toàn thư mục)
        sci_contribution = min(1.0, raw_score)

        # 4. Annotate
        annotated_b64 = _annotate_image(
            img_bgr, dets_p1, dets_p2, compound_zones, sci_contribution
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return {
            "sci_contribution": sci_contribution,
            "component_type": component_type,
            "risk_multiplier": risk_mult,
            "ai_component": ai_component_info,
            "total_px": total_px,
            "image_wh": [w, h],
            "detections_p1": dets_p1,
            "detections_p2": dets_p2,
            "compound_zones": compound_zones,
            "fused_detections": fused_dets,
            "annotated_b64": annotated_b64,
            "elapsed_ms": round(elapsed_ms, 1),
        }

    # ------------------------------------------------------------------
    # Public: Phân tích hàng loạt (folder)
    # ------------------------------------------------------------------

    def analyze_folder(
        self,
        image_paths: list[str],
        component_types: list[str] | None = None,
        dedup_enabled: bool = True,
        overlap_threshold: float = 0.30,
    ) -> dict:
        """
        Phân tích SHM cho nhiều ảnh, kèm spatial deduplication.

        Args:
            image_paths: Danh sách đường dẫn ảnh.
            component_types: Loại cấu kiện tương ứng (None → dùng 'wall' cho tất cả).
            dedup_enabled: Có bật ORB deduplication không.
            overlap_threshold: Ngưỡng overlap ratio để áp dụng giảm trọng số.

        Returns:
            dict đầy đủ gồm: sci_score, sci_level, sci_label, sci_color,
                             recommendation, per_class, images, v.v.
        """
        t_start = time.perf_counter()

        if component_types is None:
            component_types = ["auto"] * len(image_paths)
        # Đảm bảo đủ số phần tử
        while len(component_types) < len(image_paths):
            component_types.append("auto")

        # -----------------------------------------------------------------
        # Bước 1: Chạy analyze_image cho từng ảnh, đọc BGR song song (tuần tự)
        # -----------------------------------------------------------------
        imgs_bgr: list[np.ndarray | None] = []
        for path in image_paths:
            try:
                bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
                imgs_bgr.append(bgr)
            except Exception:
                imgs_bgr.append(None)

        per_image_results: list[dict] = []
        for idx, path in enumerate(image_paths):
            bgr = imgs_bgr[idx]
            if bgr is None:
                per_image_results.append({
                    "path": str(path),
                    "error": "Không đọc được ảnh",
                    "sci_contribution": 0.0,
                    "detections_p1": [],
                    "detections_p2": [],
                    "compound_zones": [],
                    "annotated_b64": "",
                    "overlap_weight": 1.0,
                })
                continue
            comp = component_types[idx]
            result = self.analyze_image(bgr, component_type=comp)
            result["path"] = str(path)
            result["overlap_weight"] = 1.0  # mặc định chưa dedup
            per_image_results.append(result)

        # -----------------------------------------------------------------
        # Bước 2: Spatial deduplication qua ORB (các ảnh liên tiếp)
        # -----------------------------------------------------------------
        dedup_applied = False
        if dedup_enabled and len(imgs_bgr) >= 2:
            for i in range(len(imgs_bgr) - 1):
                b1 = imgs_bgr[i]
                b2 = imgs_bgr[i + 1]
                if b1 is None or b2 is None:
                    continue
                overlap_ratio = _compute_overlap_ratio_orb(b1, b2)
                if overlap_ratio > overlap_threshold:
                    # Giảm trọng số của ảnh thứ hai (không giảm ảnh đầu để không mất info)
                    weight = 1.0 - overlap_ratio
                    old_w = per_image_results[i + 1].get("overlap_weight", 1.0)
                    per_image_results[i + 1]["overlap_weight"] = min(old_w, weight)
                    per_image_results[i + 1]["overlap_ratio_with_prev"] = round(overlap_ratio, 4)
                    dedup_applied = True
                    logger.info(
                        "[SHM Dedup] Ảnh %d↔%d: overlap=%.1f%% → weight=%.3f",
                        i, i + 1, overlap_ratio * 100, weight,
                    )

        # -----------------------------------------------------------------
        # Bước 3: Tính SCI tổng hợp
        # raw_score = Σ (defect_ratio * risk_mult * severity_factor * overlap_weight)
        # -----------------------------------------------------------------
        raw_score_total = 0.0
        per_class: dict[str, dict] = {
            cls: {"area_ratio": 0.0, "count": 0}
            for cls in [
                "crack", "spalling", "exposed_rebar", "corrosion",
                "compound_damage", "compound_structural_failure",
            ]
        }
        total_defect_ratio = 0.0

        for res in per_image_results:
            if "error" in res:
                continue
            ow = res.get("overlap_weight", 1.0)
            risk_m = res.get("risk_multiplier", 1.0)

            # Từng detection riêng lẻ
            for det in res.get("fused_detections", []):
                dr = det.get("defect_ratio", 0.0)
                sf = det.get("severity_factor", 1.0)
                cls = det.get("defect_type", "crack")
                contrib = dr * risk_m * sf * ow
                raw_score_total += contrib
                # Thống kê per_class
                if cls in per_class:
                    per_class[cls]["area_ratio"] += dr * ow
                    per_class[cls]["count"] += 1
                total_defect_ratio += dr * ow

            # Vùng compound
            for zone in res.get("compound_zones", []):
                dr = zone.get("defect_ratio", 0.0)
                sf = zone.get("severity_factor", 1.0)
                cls = zone.get("defect_type", "compound_damage")
                contrib = dr * risk_m * sf * ow
                raw_score_total += contrib
                if cls in per_class:
                    per_class[cls]["area_ratio"] += dr * ow
                    per_class[cls]["count"] += 1

        sci_score = round(min(100.0, raw_score_total * 100), 2)
        tier = _get_sci_tier(sci_score)

        # Round per_class
        for cls in per_class:
            per_class[cls]["area_ratio"] = round(per_class[cls]["area_ratio"], 6)

        # Chuẩn bị danh sách ảnh cho output (loại bỏ fused_detections để gọn)
        images_out: list[dict] = []
        for res in per_image_results:
            img_entry = {
                "path": res.get("path", ""),
                "sci_contribution": round(res.get("sci_contribution", 0.0) * 100, 4),
                "overlap_weight": round(res.get("overlap_weight", 1.0), 4),
                "detections_p1": res.get("detections_p1", []),
                "detections_p2": res.get("detections_p2", []),
                "compound_zones": res.get("compound_zones", []),
                "annotated_b64": res.get("annotated_b64", ""),
            }
            if "error" in res:
                img_entry["error"] = res["error"]
            if "overlap_ratio_with_prev" in res:
                img_entry["overlap_ratio_with_prev"] = res["overlap_ratio_with_prev"]
            images_out.append(img_entry)

        elapsed_total_ms = (time.perf_counter() - t_start) * 1000

        return {
            "sci_score": sci_score,
            "sci_level": tier["level"],
            "sci_label": tier["label"],
            "sci_color": tier["color"],
            "recommendation": tier["recommendation"],
            "total_images": len(image_paths),
            "total_defect_ratio": round(total_defect_ratio, 6),
            "per_class": per_class,
            "images": images_out,
            "overlap_dedup_applied": dedup_applied,
            "processing_time_ms": round(elapsed_total_ms, 1),
        }


# ---------------------------------------------------------------------------
# CLI helper (gọi trực tiếp từ command line để test nhanh)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Phase 3 SHM Engine — phân tích hư hỏng kết cấu công trình"
    )
    parser.add_argument("images", nargs="+", help="Đường dẫn ảnh cần phân tích")
    parser.add_argument(
        "--component", default="wall",
        help=f"Loại cấu kiện ({', '.join(RISK_MULTIPLIER.keys())})"
    )
    parser.add_argument("--conf1", type=float, default=0.25, help="Conf Phase 1")
    parser.add_argument("--conf2", type=float, default=0.25, help="Conf Phase 2")
    parser.add_argument("--device", default="cpu", help="Device (cpu / cuda:0)")
    parser.add_argument("--no-dedup", action="store_true", help="Tắt ORB deduplication")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    engine = SHMEngine(conf1=args.conf1, conf2=args.conf2, device=args.device)

    if len(args.images) == 1:
        bgr = cv2.imread(args.images[0], cv2.IMREAD_COLOR)
        if bgr is None:
            print(f"Không đọc được ảnh: {args.images[0]}", file=sys.stderr)
            sys.exit(1)
        result = engine.analyze_image(bgr, component_type=args.component)
        # Không in base64
        result.pop("annotated_b64", None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = engine.analyze_folder(
            args.images,
            component_types=[args.component] * len(args.images),
            dedup_enabled=not args.no_dedup,
        )
        # Không in base64 từng ảnh
        for img_entry in result.get("images", []):
            img_entry.pop("annotated_b64", None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
