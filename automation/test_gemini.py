"""
Standalone Gemini API diagnostic.

Usage:
  python test_gemini.py                       # auto-pick latest screenshot
  python test_gemini.py path/to/screenshot.png
"""
import os
import sys
from pathlib import Path


# Only models that are currently valid on Google's v1beta API.
# gemini-1.5-* and gemini-2.0-flash have been retired — they will 404.
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]


def _redact(msg: str, key: str) -> str:
    return msg.replace(key, "***REDACTED***") if key else msg


def _shorten(msg: str, n: int = 200) -> str:
    msg = " ".join(msg.split())
    return msg if len(msg) <= n else msg[: n - 3] + "..."


def main() -> int:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    print("=" * 60)
    print("GEMINI API DIAGNOSTIC")
    print("=" * 60)
    print(f"GEMINI_API_KEY set: {bool(os.getenv('GEMINI_API_KEY'))}")
    print(f"GOOGLE_API_KEY set: {bool(os.getenv('GOOGLE_API_KEY'))}")

    if not key:
        print("\n[FAIL] No API key found.")
        print('  Set it with: $env:GOOGLE_API_KEY="your-key"')
        print("  Get a free key at: https://aistudio.google.com/apikey")
        return 1

    print(f"Key length:  {len(key)} chars")
    print(f"Key preview: {key[:6]}...{key[-4:]}")

    # --- Import SDK ------------------------------------------------------
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        print("\n[OK]   google-genai SDK imported")
    except ImportError as e:
        print(f"\n[FAIL] google-genai not installed: {e}")
        print("  Fix: pip install google-genai")
        return 1

    # --- Create client ---------------------------------------------------
    try:
        client = genai.Client(api_key=key)
        print("[OK]   Client created")
    except Exception as e:
        print(f"\n[FAIL] Client creation failed: {_redact(str(e), key)}")
        return 1

    # --- List available models ------------------------------------------
    print("\nListing models available to your key...")
    listed = set()
    try:
        all_models = list(client.models.list())
        print(f"  Found {len(all_models)} models total")
        for m in all_models:
            name = m.name.replace("models/", "", 1) if m.name else ""
            if name:
                listed.add(name)
        vision_like = sorted(
            n for n in listed if any(k in n.lower() for k in ("flash", "pro"))
        )
        if vision_like:
            print("  Vision-capable candidates:")
            for name in vision_like:
                print(f"    - {name}")
    except Exception as e:
        print(f"\n[FAIL] Cannot list models: {_redact(str(e), key)}")
        print("\n  Most likely causes:")
        print("    1. API key is invalid / expired")
        print("    2. Generative Language API not enabled:")
        print("       https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
        return 1

    # --- Pick a screenshot ----------------------------------------------
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        shots_dir = Path(__file__).parent.parent / "screenshots"
        candidates = sorted(shots_dir.glob("run_*/TC-*/TC-*_step-*.png"))
        img_path = candidates[-1] if candidates else None

    if not img_path or not img_path.exists():
        print("\n[SKIP] No screenshot available to test with.")
        print("       Pass one explicitly: python test_gemini.py path/to.png")
        return 0

    print(f"\nTrying a real vision call with: {img_path}")
    img_bytes = img_path.read_bytes()
    print(f"  Image size: {len(img_bytes):,} bytes")

    # --- Try each candidate model ---------------------------------------
    any_ok = False
    working_models: list[str] = []

    for model_name in CANDIDATE_MODELS:
        # Skip models the key doesn't list at all (saves noisy 404s).
        if listed and model_name not in listed:
            print(f"  [SKIP] {model_name} (not listed for this key)")
            continue

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    "Describe this screenshot in one short sentence.",
                ],
                config=types.GenerateContentConfig(temperature=0.0),
            )
            text = getattr(response, "text", None) or "(no text)"
            print(f"  [OK]   {model_name}")
            print(f"         {_shorten(text, 140)}")
            any_ok = True
            working_models.append(model_name)
        except Exception as e:
            err = _redact(str(e), key)
            print(f"  [FAIL] {model_name}: {type(e).__name__}: {_shorten(err)}")

    # --- Verdict ---------------------------------------------------------
    print()
    if any_ok:
        print("[DONE] At least one model works.")
        print(f"       Working models: {', '.join(working_models)}")
        print()
        print("       Set your primary model in automation/config.py to:")
        print(f'           AI_MODEL = "{working_models[0]}"')
        return 0

    print("[FAIL] No candidate model worked.")
    print("       Check that one of these exists in the list printed above:")
    for m in CANDIDATE_MODELS:
        print(f"         - {m}")
    return 1


if __name__ == "__main__":
    sys.exit(main())