import os
import shutil
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from core.analyzer import analyze_images
from core.fusion import fuse_prompt
from core.generator import generate_image

app = FastAPI(title="Style Template Tool API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temp and output directories exist
os.makedirs("outputs/temp", exist_ok=True)
os.makedirs("outputs/generated", exist_ok=True)

# Serve outputs directory statically so frontend can access images
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Pydantic models for request bodies
class FuseRequest(BaseModel):
    template_description: str
    user_prompt: str

class SingleGenerateRequest(BaseModel):
    fused_prompt: str
    aspect_ratio: str
    style_references: List[str]
    # Product reference will be handled via form-data since it's an image upload

class BatchGenerateRequest(BaseModel):
    template_description: str
    aspect_ratio: str
    style_references: List[str]
    scenes: List[int]

SCENES_PRESET = [
    ("产品主图", "product photography on clean white background, professional e-commerce style"),
    ("功效展示图", "showcasing efficacy and benefits, with data visualization"),
    ("成分说明图", "highlighting ingredients, scientific formula visualization"),
    ("使用场景图", "in lifestyle setting, bathroom vanity scene"),
    ("品牌故事图", "brand story visualization, laboratory background"),
]

def save_upload_file(upload_file: UploadFile, dest_dir: str) -> str:
    """Helper to save uploaded file and return its path"""
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(dest_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

@app.post("/api/analyze")
async def api_analyze(images: List[UploadFile] = File(...)):
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    saved_paths = []
    try:
        for image in images:
            path = save_upload_file(image, "outputs/temp")
            saved_paths.append(path)
            
        description, rep_indices, rep_paths = analyze_images(saved_paths)
        
        # Convert absolute/relative local paths to URL paths
        rep_urls = [f"/{path}" for path in rep_paths]
        
        return {
            "description": description,
            "representative_paths": rep_paths, # Keep local paths for generator
            "representative_urls": rep_urls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fuse")
async def api_fuse(req: FuseRequest):
    try:
        fused = fuse_prompt(req.template_description, req.user_prompt)
        return {"fused_prompt": fused}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/single")
async def api_generate_single(
    fused_prompt: str = Form(...),
    aspect_ratio: str = Form(...),
    style_references: str = Form(...), # Comma separated paths
    product_image: UploadFile = File(...)
):
    try:
        prod_path = save_upload_file(product_image, "outputs/temp")
        style_refs = [path.strip() for path in style_references.split(",") if path.strip()]
        
        result_paths = generate_image(
            prompt=fused_prompt,
            style_references=style_refs,
            product_reference=prod_path,
            aspect_ratio=aspect_ratio,
        )
        
        result_urls = [f"/{path}" for path in result_paths]
        return {"result_urls": result_urls, "result_paths": result_paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/batch")
async def api_generate_batch(
    template_description: str = Form(...),
    aspect_ratio: str = Form(...),
    style_references: str = Form(...),
    scenes: str = Form(...), # Comma separated indices
    product_image: UploadFile = File(...)
):
    try:
        prod_path = save_upload_file(product_image, "outputs/temp")
        style_refs = [path.strip() for path in style_references.split(",") if path.strip()]
        selected_scenes = [int(idx.strip()) for idx in scenes.split(",") if idx.strip()]
        
        if not selected_scenes:
            raise HTTPException(status_code=400, detail="No scenes selected")
            
        generated_urls = []
        logs = []
        
        for idx in selected_scenes:
            if idx < 0 or idx >= len(SCENES_PRESET):
                continue
                
            name, prompt = SCENES_PRESET[idx]
            logs.append(f"Generating: {name}")
            
            try:
                fused = fuse_prompt(template_description, prompt)
                result_paths = generate_image(
                    prompt=fused,
                    style_references=style_refs,
                    product_reference=prod_path,
                    aspect_ratio=aspect_ratio,
                )
                
                for path in result_paths:
                    new_name = f"batch_{idx}_{name}.png"
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    shutil.move(path, new_path)
                    generated_urls.append(f"/{new_path}")
                    logs.append(f"Success: {name}")
            except Exception as e:
                logs.append(f"Failed {name}: {str(e)}")
                
        return {"generated_urls": generated_urls, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
