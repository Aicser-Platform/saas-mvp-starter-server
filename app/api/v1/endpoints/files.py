from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{blob_name:path}", summary="Redirect to a locally-stored file")
def get_file(blob_name: str):
    return RedirectResponse(url=f"/uploads/{blob_name}", status_code=302)
