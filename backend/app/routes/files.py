from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import pylabs_bridge as pb
from app.deps import get_current_user
from app.models import User
from app.schemas import FileContentIn

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("")
def list_files(taskId: str | None = Query(default=None), user: User = Depends(get_current_user)):
    # taskId is accepted for forward-compat / URL clarity; the workspace is
    # per-user, not per-task, so today it's the whole user workspace tree.
    ws_dir = pb.workspace_dir_for(user.id)
    return {"files": pb.list_files(ws_dir)}


@router.get("/content")
def read_file_content(path: str = Query(...), user: User = Depends(get_current_user)):
    ws_dir = pb.workspace_dir_for(user.id)
    try:
        content = pb.read_file(ws_dir, path)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no such file: {path}")
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid path")
    return {"path": path, "content": content}


@router.post("/content")
def write_file_content(body: FileContentIn, user: User = Depends(get_current_user)):
    ws_dir = pb.workspace_dir_for(user.id)
    try:
        pb.write_file(ws_dir, body.path, body.content)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid path")
    return {"ok": True}
