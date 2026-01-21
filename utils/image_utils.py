# utils/image_utils.py

CDN_BASE = "https://cdn.nashikcityguide.com/"
PLACEHOLDER = CDN_BASE + "assets/images/default_placeholder.jpg"  # keep if you want a fallback later

def build_image_url(thumbnail_image: str | None) -> str | None:
    """
    Return a full CDN URL for a thumbnail path coming from dataset.
    If thumbnail_image is falsy, returns None (no placeholder).
    """
    if not thumbnail_image:
        return None
    # ensure no leading slash duplication
    return CDN_BASE + thumbnail_image.lstrip("/")
