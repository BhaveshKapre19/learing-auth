#authentication.services.upload_path
import uuid

def user_profile_pic_path(instance, filename):
    """Store image under /media/<slug>/<filename>"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    user_slug = instance.user.slug
    return f"{user_slug}/{filename}"