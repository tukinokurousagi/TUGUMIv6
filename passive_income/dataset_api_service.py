# -*- coding: utf-8 -*-
"""
TUGUMIv6 Dataset & Micro-API Monetization Service
- Formats structured datasets (QA pairs, cybersecurity CVEs, code snippets)
- Hosts commercial FastAPI micro-endpoints via Cloudflare Tunnel
"""

import json
import os
from typing import Dict, Any, List

class DatasetAPIService:
    """Specialized Dataset Generation & Monetization API"""
    def __init__(self, data_store_dir: str = "/data/data/com.termux/files/home/TUGUMIv6/data/datasets"):
        self.data_store_dir = data_store_dir
        os.makedirs(self.data_store_dir, exist_ok=True)

    def create_dataset_pack(self, name: str, items: List[Dict[str, Any]]) -> str:
        """高品質データセットをJSONL形式で保存"""
        file_path = os.path.join(self.data_store_dir, f"{name}.jsonl")
        with open(file_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return file_path

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        datasets = []
        for fn in os.listdir(self.data_store_dir):
            if fn.endswith(".jsonl"):
                fp = os.path.join(self.data_store_dir, fn)
                size_kb = os.path.getsize(fp) / 1024.0
                datasets.append({"name": fn, "size_kb": round(size_kb, 2), "path": fp})
        return datasets
