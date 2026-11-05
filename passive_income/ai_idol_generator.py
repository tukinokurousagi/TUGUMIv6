# -*- coding: utf-8 -*-
"""
TUGUMIv6 Autonomous AI Idol & Photobook Production Pipeline
- Integrates with GeminiImageStudio (tools.media_tools) for Character-DNA-locked photorealistic portraits
- Generates concept sheets, outfit variations, and KDP/photobook metadata packages
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

from tools.media_tools import GeminiImageStudio, IMAGES_DIR


class AIIdolGenerator:
    """Autonomous AI Beauty Model & Photobook Asset Producer"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or IMAGES_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def produce_portrait_shot(
        self,
        concept_prompt: str,
        aspect_ratio: str = "3:4",
        reference_images: Optional[List[str]] = None,
        outfit: str = "",
        background: str = ""
    ) -> Dict[str, Any]:
        """Produce a studio-grade photorealistic portrait or face-locked dressup shot."""
        if reference_images:
            valid_refs = [p for p in reference_images if os.path.isfile(p)]
            if valid_refs:
                return GeminiImageStudio.face_lock_dressup(
                    image_paths=valid_refs,
                    outfit=outfit or concept_prompt,
                    background=background,
                )

        return GeminiImageStudio.generate(
            prompt=concept_prompt,
            photoreal=True,
            style="photoreal",
            aspect_ratio=aspect_ratio,
        )

    def build_photobook_manifest(
        self,
        title: str,
        theme: str,
        image_paths: List[str]
    ) -> Dict[str, Any]:
        """Create a structured KDP/Digital Photobook manifest JSON for generated shots."""
        valid_images = [p for p in image_paths if os.path.isfile(p)]
        manifest = {
            "title": title,
            "theme": theme,
            "created_at": int(time.time()),
            "total_pages": len(valid_images),
            "pages": [
                {"page": idx, "image_path": path, "size_bytes": os.path.getsize(path)}
                for idx, path in enumerate(valid_images, start=1)
            ],
        }
        manifest_path = os.path.join(self.output_dir, f"photobook_{int(time.time())}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        manifest["manifest_path"] = manifest_path
        return manifest
