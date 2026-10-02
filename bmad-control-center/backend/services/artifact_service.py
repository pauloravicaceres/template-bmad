import os
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set
import aiofiles
from fastapi import HTTPException

from core.config import settings
from core.security import validate_sandbox_path, PathTraversalError
from models.directory import DirectoryNode, ArtifactTreeResponse
from models.artifact import ArtifactContent, MAX_ARTIFACT_SIZE


BINARY_EXTENSIONS: Set[str] = {
    ".bin", ".pdf", ".zip", ".tar", ".gz", ".7z", ".png", ".jpg", ".jpeg",
    ".gif", ".ico", ".webp", ".svgz", ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".class", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    ".wav", ".avi", ".mov", ".lock"
}


class ArtifactService:
    """Service for securely exploring and reading workspace artifacts."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or settings.WORKSPACE_ROOT).resolve()

    def _format_mtime(self, path: Path) -> str:
        """Converts file mtime to ISO 8601 UTC string."""
        try:
            mtime = path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except Exception:
            return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _scan_directory_node(self, current_dir: Path, rel_root: str) -> DirectoryNode:
        """Recursively builds DirectoryNode for a directory."""
        norm_rel = rel_root.replace("\\", "/").strip("/")
        dir_name = current_dir.name or norm_rel
        parent_rel = "/".join(norm_rel.split("/")[:-1]) if "/" in norm_rel else ("" if norm_rel else None)
        
        children: List[DirectoryNode] = []
        child_files_count = 0

        try:
            entries = sorted(list(current_dir.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Fallo al indexar los directorios del espacio de trabajo debido a un error de lectura física: {str(e)}"
            )

        for entry in entries:
            # Skip hidden git and cache dirs
            if entry.name in [".git", "__pycache__", ".pytest_cache", "node_modules", ".venv"]:
                continue
            
            entry_rel = f"{norm_rel}/{entry.name}" if norm_rel else entry.name
            entry_rel = entry_rel.replace("\\", "/")

            if entry.is_dir():
                sub_node = self._scan_directory_node(entry, entry_rel)
                children.append(sub_node)
            else:
                child_files_count += 1
                file_node = DirectoryNode(
                    node_id=entry_rel,
                    name=entry.name,
                    node_type="FILE",
                    relative_path=entry_rel,
                    parent_path=norm_rel,
                    child_file_count=0,
                    is_empty=False,
                    last_modified=self._format_mtime(entry),
                    children=[],
                    type="FILE",
                    path=entry_rel
                )
                children.append(file_node)

        is_empty = (child_files_count == 0 and len([c for c in children if c.node_type == "DIRECTORY"]) == 0) or (child_files_count == 0)

        return DirectoryNode(
            node_id=norm_rel or "workspace_root",
            name=dir_name,
            node_type="DIRECTORY",
            relative_path=norm_rel,
            parent_path=parent_rel,
            child_file_count=child_files_count,
            is_empty=is_empty,
            last_modified=self._format_mtime(current_dir),
            children=children,
            type="DIRECTORY",
            path=f"{norm_rel}/" if norm_rel else "/"
        )

    def get_artifact_tree(self, root: str = "all") -> ArtifactTreeResponse:
        """
        Escanea recursivamente las raíces del workspace autorizadas ('files/', 'specs/', '.specify/').
        Valida que el parámetro root pertenezca a la lista blanca o sea 'all'.
        """
        valid_roots = ["files", "specs", ".specify", "all"]
        if root not in valid_roots:
            raise HTTPException(
                status_code=400,
                detail=f"El parámetro 'root' recibido ('{root}') no es una raíz autorizada. Valores admitidos: 'files', 'specs', '.specify', 'all'."
            )

        roots_to_scan = settings.ALLOWED_ROOTS if root == "all" else [root]
        
        children: List[DirectoryNode] = []
        for r in roots_to_scan:
            r_path = (self.workspace_root / r).resolve()
            if r_path.exists() and r_path.is_dir():
                node = self._scan_directory_node(r_path, r)
                children.append(node)
            elif r_path.exists() and r_path.is_file():
                # Single file root
                rel = r.replace("\\", "/")
                file_node = DirectoryNode(
                    node_id=rel,
                    name=r_path.name,
                    node_type="FILE",
                    relative_path=rel,
                    parent_path="",
                    child_file_count=0,
                    is_empty=False,
                    last_modified=self._format_mtime(r_path),
                    children=[],
                    type="FILE",
                    path=rel
                )
                children.append(file_node)
            else:
                # Directory does not exist yet -> create empty representation
                children.append(
                    DirectoryNode(
                        node_id=r,
                        name=r,
                        node_type="DIRECTORY",
                        relative_path=r,
                        parent_path="",
                        child_file_count=0,
                        is_empty=True,
                        last_modified=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        children=[],
                        type="DIRECTORY",
                        path=f"{r}/"
                    )
                )

        root_node = DirectoryNode(
            node_id="workspace_root",
            name="Dashboard BMAD Workspace",
            node_type="DIRECTORY",
            relative_path="",
            parent_path=None,
            child_file_count=0,
            is_empty=False,
            last_modified=self._format_mtime(self.workspace_root),
            children=children,
            type="DIRECTORY",
            path="/"
        )

        return ArtifactTreeResponse(
            root_node=root_node,
            type="DIRECTORY",
            name="root",
            path="/",
            children=children
        )

    async def get_artifact_content(self, relative_path: str) -> ArtifactContent:
        """
        Lectura segura del contenido UTF-8 de un archivo documental con guardas de sandbox,
        límite de tamaño (5MB) y detección de binarios.
        """
        if not relative_path or not relative_path.strip():
            raise HTTPException(
                status_code=400,
                detail="El parámetro 'path' es obligatorio."
            )

        # 1. Sandboxing Path Traversal check
        canonical_path = validate_sandbox_path(
            relative_path,
            allowed_roots=settings.ALLOWED_ROOTS,
            workspace_root=self.workspace_root
        )

        # 2. Check physical existence
        if not canonical_path.exists() or not canonical_path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"El artefacto '{relative_path}' no existe en el sistema de archivos local."
            )

        # 3. Check file size (5MB threshold)
        try:
            stat_info = canonical_path.stat()
            size_bytes = stat_info.st_size
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ocurrió un error inesperado al leer los metadatos del archivo en el sistema de archivos local: {str(e)}"
            )

        if size_bytes > settings.MAX_PAYLOAD_SIZE:
            mb_size = round(size_bytes / (1024 * 1024), 1)
            raise HTTPException(
                status_code=413,
                detail=f"El archivo '{canonical_path.name}' ({mb_size} MB) sobrepasa el límite máximo admitido de 5 MB para previsualización en el navegador."
            )

        # 4. Check for unsupported binary media
        ext = canonical_path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(canonical_path))
        
        is_binary_extension = ext in BINARY_EXTENSIONS
        is_binary_mime = False
        if mime_type:
            if not (mime_type.startswith("text/") or mime_type in [
                "application/json", "application/javascript", "application/xml",
                "application/x-yaml", "application/yaml", "text/markdown"
            ]):
                is_binary_mime = True

        if is_binary_extension or is_binary_mime:
            detected_mime = mime_type or "application/octet-stream"
            raise HTTPException(
                status_code=415,
                detail=f"El archivo '{canonical_path.name}' posee un formato binario ('{detected_mime}') no renderizable en modo texto o Markdown."
            )

        # 5. Read file asynchronously with aiofiles
        try:
            async with aiofiles.open(canonical_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
        except UnicodeDecodeError:
            # File is binary or not valid UTF-8
            raise HTTPException(
                status_code=415,
                detail=f"El archivo '{canonical_path.name}' posee una codificación no válida o binaria no representable en UTF-8."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ocurrió un error inesperado al leer el descriptor del archivo en el sistema de archivos local: {str(e)}"
            )

        # Format detection
        detected_format = "MARKDOWN" if ext in [".md", ".markdown"] else "TEXT"
        final_mime = mime_type or ("text/markdown" if detected_format == "MARKDOWN" else "text/plain")
        norm_rel = relative_path.replace("\\", "/")

        return ArtifactContent(
            relative_path=norm_rel,
            filename=canonical_path.name,
            raw_content=content,
            detected_format=detected_format,
            encoding="utf-8",
            size_bytes=size_bytes,
            is_oversized=False,
            is_unsupported_media=False,
            mime_type=final_mime,
            last_modified=self._format_mtime(canonical_path),
            content=content,
            format=detected_format
        )
