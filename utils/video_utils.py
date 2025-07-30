"""
Görüntü İşleme Yardımcı Fonksiyonları

Bu modül, tepsi ve tabak tespiti sırasında kullanılan çeşitli yardımcı
fonksiyonları içerir. IOU hesaplama, aşırı parlaklık azaltma ve
kategori belirleme gibi görevler için kullanılır.
"""

import json
import os
import numpy as np
import cv2

def compute_iou(b1, b2):

    """
    IOU (Intersection over Union) hesaplar.

    Args:
        b1 (tuple): İlk bounding box (x1, y1, x2, y2).
        b2 (tuple): İkinci bounding box (x1, y1, x2, y2).

    Returns:
        float: IOU oranı (0 ile 1 arasında bir değer).
    """

    x1, y1, x2, y2 = b1
    x1g, y1g, x2g, y2g = b2
    xi1, yi1 = max(x1, x1g), max(y1, y1g)
    xi2, yi2 = min(x2, x2g), min(y2, y2g)
    inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x2g - x1g) * (y2g - y1g)
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0

def reduce_overexposed_regions(frame, v_limit=150):
    """
    Aşırı parlak bölgeleri sınırlandırmak için HSV uzayında V kanalını (Brightness) azaltır.
    Bunun amacı modelden kaynaklanan hatalı tabak tespitlerinden (False Positive) kurtulmaktır.

    Args:
        frame (np.ndarray): BGR formatında görüntü.
        v_limit (int): V kanalına uygulanacak üst sınır değeri (varsayılan 150).

    Returns:
        np.ndarray: Aydınlatması azaltılmış yeni görüntü.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = np.clip(v, 0, v_limit)
    hsv = cv2.merge((h, s, v))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def get_category(count):
    """
    Tabak sayısına göre kategori belirler.

    Args:
        count (int): Tepsi içindeki tabak sayısı.

    Returns:
        str: İlgili kategori stringi.
    """

    if count <= 1:
        return "category_1"
    elif count == 2:
        return "category_2"
    elif count == 3:
        return "category_3"
    elif count == 4:
        return "category_4"
    return "category_5"

def save_alarm(payload, save_dir="alarms"):
    os.makedirs(save_dir, exist_ok=True)

    json_path = os.path.join(save_dir, f"{payload['transaction_uuid']}.json")

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    if not isinstance(existing_data, list):
        existing_data = [existing_data]

    existing_data.append(payload)

    with open(json_path, "w") as f:
        json.dump(existing_data, f, indent=2)