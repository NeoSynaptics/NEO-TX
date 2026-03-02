"""GPU model management — 14B conversational + specialized small models.

NEO-TX owns the GPU models for fast user interaction:
- 14B conversational model (semantic understanding, NOT coding)
- Small specialized models (~2B) for specific fast tasks
- Future: LoRA adapter hot-swap via llama.cpp

Models time-share the GPU (12GB VRAM) — 14B is resident, Whisper and
small models swap in on demand.
"""
