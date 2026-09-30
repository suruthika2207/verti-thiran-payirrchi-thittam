from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.schemas import (
    ComicResponse,
    PromptRequest,
)

from app.services.image_generator import (
    ImageGenerator,
)

from app.services.workflow import (
    generate_comic,
)


router = APIRouter()


templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    try:

        payload = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        layout, pdf_path = generate_comic(
            payload,
            get_settings()
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": pdf_path,
            }
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
    response_model=ComicResponse
)
async def generate_comic_json(
    payload: PromptRequest
):

    try:

        layout, pdf_path = generate_comic(
            payload,
            get_settings()
        )

        return ComicResponse(
            success=True,
            panels=layout,
            pdf_path=pdf_path,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request,
    pdf_path: str | None = None
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path
        }
    )


@router.get("/download")
async def download_pdf(path: str):

    file_path = Path(path).resolve()

    exports_root = (
        Path("static/exports")
        .resolve()
    )

    # Security check
    if (
        exports_root not in file_path.parents
        or not file_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="PDF not found"
        )

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=file_path.name
    )


@router.post("/test-image")
async def test_image(payload: dict):

    prompt = str(
        payload.get("prompt", "")
    ).strip()

    if not prompt:

        raise HTTPException(
            status_code=422,
            detail="prompt is required"
        )

    try:

        path = ImageGenerator(
            get_settings()
        ).generate_image(prompt)

        return {
            "success": True,
            "image_path": path,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc