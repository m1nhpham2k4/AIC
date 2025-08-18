import numpy as np
import torch
import open_clip
from app.config import DEVICE, TOPK_DEFAULT
from app.services.index_store import INDEX
from app.services.result_mapper import attach_image_url

# SigLIP2 (text tower) qua OpenCLIP
MODEL_ID = "hf-hub:timm/ViT-gopt-16-SigLIP2-384"
_model, _, _ = open_clip.create_model_and_transforms(MODEL_ID, device=DEVICE)
_tokenizer = open_clip.get_tokenizer(MODEL_ID)
_model.eval()
for p in _model.parameters(): p.requires_grad_(False)

def _encode_text(text: str) -> np.ndarray:
    toks = _tokenizer([text], context_length=getattr(_model, "context_length", 64)).to(DEVICE)
    with torch.no_grad(), torch.cuda.amp.autocast(enabled=("cuda" in DEVICE)):
        z = _model.encode_text(toks, normalize=True)  # (1,D) L2-norm
    return z[0].float().cpu().numpy()

def search(text: str, top_k: int = TOPK_DEFAULT):
    q = _encode_text(text)
    if q.shape[0] != INDEX.dim:
        raise RuntimeError(f"Dim mismatch: model={q.shape[0]} index={INDEX.dim}")
    hits = INDEX.search_dot(q, top_k)
    return [attach_image_url(h) for h in hits]
