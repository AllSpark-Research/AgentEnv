from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shlex
import time
from typing import TYPE_CHECKING, Any, Dict

import requests

from .file_state_cache import FILE_UNCHANGED_STUB, FILE_UNEXPECTEDLY_MODIFIED_ERROR, FileState, FileStateCache

if TYPE_CHECKING:
    from .sandbox import Sandbox
logger = logging.getLogger(__name__)
OUTPUT_LIMIT = 25000
DEFAULT_BASH_TIMEOUT_MS = 120000
SANDBOX_WORK_DIR = "/workspace"
MAX_READ_FILE_SIZE_BYTES = 256 * 1024
DEFAULT_MAX_READ_OUTPUT_TOKENS = 25000
MAX_LINES_TO_READ = 2000


def _truncate(text: str, limit: int = OUTPUT_LIMIT) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    half = limit // 2 - 100
    head = text[:half]
    tail = text[-half:]
    omitted = len(text) - len(head) - len(tail)
    return f"{head}\n\n... [TRUNCATED {omitted} chars in middle] ...\n\n{tail}"


def _shell_escape(s: str) -> str:
    return shlex.quote(s)


async def sandbox_run(sandbox: Sandbox, cmd: str, timeout_ms: int | None = None) -> tuple[str, str, int | None]:
    eff_timeout_ms = timeout_ms if timeout_ms is not None else DEFAULT_BASH_TIMEOUT_MS
    try:
        return await sandbox.run(cmd, timeout_ms=eff_timeout_ms)
    except TimeoutError:
        return "", f"[sandbox_run] 命令执行超过 {eff_timeout_ms}ms。", -1


async def sandbox_stat(sandbox: Sandbox, path: str) -> tuple[int, int, bool] | None:
    import base64

    py_script = "import os, sys\ntry:\n    s = os.stat(sys.argv[1])\nexcept FileNotFoundError:\n    sys.exit(2)\nexcept Exception as e:\n    sys.stderr.write('stat error: ' + str(e))\n    sys.exit(3)\nprint(str(s.st_size) + '|' + str(s.st_mtime_ns))\n"
    script_b64 = base64.b64encode(py_script.encode("utf-8")).decode()
    safe_path = _shell_escape(path)
    cmd = f"""python3 -c "import base64,sys; exec(base64.b64decode('{script_b64}'))" {safe_path}"""
    stdout, _stderr, exit_code = await sandbox_run(sandbox, cmd)
    if exit_code is not None and exit_code != 0:
        return None
    out = (stdout or "").strip()
    if "|" not in out:
        return None
    try:
        size_str, mtime_str = out.split("|", 1)
        size = int(size_str)
        mtime_ns = int(mtime_str)
        return (size, mtime_ns, True)
    except Exception:
        return None


def _approx_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _format_cmd_result(stdout: str, stderr: str, exit_code: int | None) -> str:
    parts: list[str] = []
    if stdout:
        parts.append(stdout)
    if stderr:
        if parts:
            parts.append("")
        parts.append("[stderr]")
        parts.append(stderr)
    if exit_code is not None and exit_code != 0:
        parts.append(f"[exit_code={exit_code}]")
    return "\n".join(parts)


async def tool_bash(
    sandbox: Sandbox,
    *,
    command: str,
    timeout: int | None = None,
    description: str | None = None,
    run_in_background: bool = False,
    **kwargs,
) -> str:
    if run_in_background:
        return "[Bash] run_in_background 在本框架不支持（沙箱内同步执行）。"
    full_cmd = f"cd {SANDBOX_WORK_DIR} && {command}"
    stdout, stderr, exit_code = await sandbox_run(sandbox, full_cmd, timeout_ms=timeout or DEFAULT_BASH_TIMEOUT_MS)
    return _truncate(_format_cmd_result(stdout, stderr, exit_code))


async def tool_read(
    sandbox: Sandbox,
    *,
    file_path: str,
    offset: int | None = None,
    limit: int | None = None,
    pages: str | None = None,
    cache: FileStateCache | None = None,
    **kwargs,
) -> str:
    if not file_path:
        return "[Read] 错误：file_path 不能为空。"
    if pages:
        return "[Read] 当前评测语料为 txt（无需 PDF/Notebook 模式），pages 参数已忽略。"
    stat = await sandbox_stat(sandbox, file_path)
    if stat is None:
        return f"[Read] 错误：文件不存在或无法访问: {file_path}"
    size_bytes, mtime_ns, _exists = stat
    if cache is not None:
        prev = cache.get(file_path)
        if prev is not None and prev.timestamp_ns == mtime_ns:
            cur_start = offset if offset and offset > 0 else 1
            cur_n = limit if limit and limit > 0 else MAX_LINES_TO_READ
            cur_end = cur_start + cur_n
            if not prev.is_partial:
                return FILE_UNCHANGED_STUB
            prev_start = prev.offset if prev.offset and prev.offset > 0 else 1
            prev_n = prev.limit if prev.limit and prev.limit > 0 else MAX_LINES_TO_READ
            prev_end = prev_start + prev_n
            if prev_start <= cur_start and cur_end <= prev_end:
                return FILE_UNCHANGED_STUB
    if offset is None and limit is None and (size_bytes > MAX_READ_FILE_SIZE_BYTES):
        return f"[Read] 错误：文件 {file_path} 大小为 {size_bytes} 字节，超过 {MAX_READ_FILE_SIZE_BYTES} 字节上限。请使用 Grep 进行定向搜索，或带上 offset + limit 分段读取。"
    start = offset if offset and offset > 0 else 1
    n = limit if limit and limit > 0 else MAX_LINES_TO_READ
    safe_path = _shell_escape(file_path)
    cmd = f"""awk -v s={start} -v n={n} 'NR>=s && NR<s+n {{ printf "%6d\\t%s\\n", NR, $0 }}' {safe_path}"""
    stdout, stderr, exit_code = await sandbox_run(sandbox, cmd)
    if exit_code and exit_code != 0:
        return _truncate(stderr or f"[Read] 读取失败 (exit={exit_code})")
    if not stdout.strip():
        return f"[Read] 文件 {file_path} 在 offset={start} limit={n} 范围内无内容（可能已超出文件末尾）。"
    approx = _approx_tokens(stdout)
    if approx > DEFAULT_MAX_READ_OUTPUT_TOKENS:
        return f"[Read] 错误：本次读取产出约 {approx} tokens，超过 {DEFAULT_MAX_READ_OUTPUT_TOKENS} tokens 上限。请减小 limit、提高 offset，或改用 Grep 做定向搜索。"
    if cache is not None:
        cache.set(
            file_path,
            FileState(
                content=stdout, timestamp_ns=mtime_ns, offset=offset, limit=limit, is_partial=bool(offset or limit)
            ),
        )
    return _truncate(stdout)


async def tool_edit(
    sandbox: Sandbox,
    *,
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    cache: FileStateCache | None = None,
    **kwargs,
) -> str:
    if not file_path:
        return "[Edit] 错误：file_path 不能为空。"
    if old_string == new_string:
        return "[Edit] 错误：old_string 不能等于 new_string。"
    if cache is not None:
        prev = cache.get(file_path)
        if prev is None:
            return f"[Edit] 错误：文件 {file_path} 在本会话中尚未被 Read。在编辑文件之前，你必须至少先用 Read 工具读取它一次。"
        cur = await sandbox_stat(sandbox, file_path)
        if cur is None:
            return f"[Edit] 错误：文件 {file_path} 不存在或无法访问。"
        _cur_size, cur_mtime_ns, _ = cur
        if cur_mtime_ns != prev.timestamp_ns:
            return FILE_UNEXPECTEDLY_MODIFIED_ERROR
    else:
        cur = await sandbox_stat(sandbox, file_path)
        if cur is None:
            return f"[Edit] 错误：文件 {file_path} 不存在或无法访问。"
    import base64

    py_script = "import sys, json\ndata = json.load(sys.stdin)\npath = data['path']\nold = data['old']\nnew = data['new']\nreplace_all = data['replace_all']\ntry:\n    with open(path, 'r', encoding='utf-8') as f:\n        content = f.read()\nexcept FileNotFoundError:\n    print('[Edit] 错误：文件不存在: ' + path); sys.exit(2)\ncount = content.count(old)\nif count == 0:\n    print('[Edit] 错误：old_string 在文件中未出现: ' + path); sys.exit(3)\nif count > 1 and not replace_all:\n    print('[Edit] 错误：old_string 出现 ' + str(count) + ' 次，非唯一。加更多上下文或传 replace_all=true。'); sys.exit(4)\nif replace_all:\n    new_content = content.replace(old, new); replaced = count\nelse:\n    new_content = content.replace(old, new, 1); replaced = 1\nwith open(path, 'w', encoding='utf-8') as f:\n    f.write(new_content)\nprint('[Edit] 成功：在 ' + path + ' 中替换 ' + str(replaced) + ' 处。')\n"
    payload = json.dumps({"path": file_path, "old": old_string, "new": new_string, "replace_all": bool(replace_all)})
    script_b64 = base64.b64encode(py_script.encode("utf-8")).decode()
    payload_b64 = base64.b64encode(payload.encode("utf-8")).decode()
    cmd = f'''echo {payload_b64} | base64 -d | python3 -c "import base64,sys; exec(base64.b64decode('{script_b64}'))"'''
    stdout, stderr, exit_code = await sandbox_run(sandbox, cmd)
    result = _format_cmd_result(stdout, stderr, exit_code)
    edit_succeeded = "[Edit] 成功" in (stdout or "") and (exit_code is None or exit_code == 0)
    if cache is not None and edit_succeeded:
        new_stat = await sandbox_stat(sandbox, file_path)
        if new_stat is not None:
            new_size, new_mtime_ns, _ = new_stat
            if new_size <= MAX_READ_FILE_SIZE_BYTES:
                cat_cmd = f"""awk '{{ printf "%6d\\t%s\\n", NR, $0 }}' {_shell_escape(file_path)}"""
                cat_out, _e1, cat_exit = await sandbox_run(sandbox, cat_cmd)
                if cat_exit == 0:
                    cache.set(
                        file_path,
                        FileState(
                            content=cat_out, timestamp_ns=new_mtime_ns, offset=None, limit=None, is_partial=False
                        ),
                    )
                else:
                    cache.set(
                        file_path,
                        FileState(content="", timestamp_ns=new_mtime_ns, offset=None, limit=None, is_partial=False),
                    )
            else:
                cache.set(
                    file_path,
                    FileState(content="", timestamp_ns=new_mtime_ns, offset=None, limit=None, is_partial=False),
                )
    return _truncate(result)


async def tool_write(
    sandbox: Sandbox, *, file_path: str, content: str, cache: FileStateCache | None = None, **kwargs
) -> str:
    if not file_path:
        return "[Write] 错误：file_path 不能为空。"
    if cache is not None:
        prev = cache.get(file_path)
        if prev is not None:
            cur = await sandbox_stat(sandbox, file_path)
            if cur is not None:
                _cur_size, cur_mtime_ns, _ = cur
                if cur_mtime_ns != prev.timestamp_ns:
                    return FILE_UNEXPECTEDLY_MODIFIED_ERROR
    try:
        parent = os.path.dirname(file_path)
        if parent and parent not in ("/", ""):
            await sandbox_run(sandbox, f"mkdir -p {_shell_escape(parent)}")
        await sandbox.write_file(file_path, content.encode("utf-8"))
    except Exception as e:
        return f"[Write] 失败：{type(e).__name__}: {e}"
    if cache is not None:
        new_stat = await sandbox_stat(sandbox, file_path)
        if new_stat is not None:
            _new_size, new_mtime_ns, _ = new_stat
            numbered_lines = []
            for i, line in enumerate(content.splitlines(), 1):
                numbered_lines.append(f"{i:>6}\t{line}")
            cache.set(
                file_path,
                FileState(
                    content="\n".join(numbered_lines),
                    timestamp_ns=new_mtime_ns,
                    offset=None,
                    limit=None,
                    is_partial=False,
                ),
            )
    return f"[Write] 成功：已写入 {file_path}（{len(content)} 字符）。"


async def tool_glob(sandbox: Sandbox, *, pattern: str, path: str | None = None, **kwargs) -> str:
    if not pattern:
        return "[Glob] 错误：pattern 不能为空。"
    base = path or SANDBOX_WORK_DIR
    import base64

    py_script = "import sys, os, glob\nbase = sys.argv[1]\npat = sys.argv[2]\nfull = pat if os.path.isabs(pat) else os.path.join(base, pat)\nmatches = glob.glob(full, recursive=True)\nmatches.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)\nif not matches:\n    print('[Glob] 无匹配。')\nelse:\n    for m in matches[:1000]:\n        print(m)\n"
    script_b64 = base64.b64encode(py_script.encode("utf-8")).decode()
    cmd = f"""python3 -c "import base64,sys; exec(base64.b64decode('{script_b64}'))" {_shell_escape(base)} {_shell_escape(pattern)}"""
    stdout, stderr, exit_code = await sandbox_run(sandbox, cmd)
    return _truncate(_format_cmd_result(stdout, stderr, exit_code))


async def tool_grep(
    sandbox: Sandbox,
    *,
    pattern: str,
    path: str | None = None,
    glob: str | None = None,
    output_mode: str = "files_with_matches",
    head_limit: int | None = 250,
    multiline: bool = False,
    **kwargs,
) -> str:
    if not pattern:
        return "[Grep] 错误：pattern 不能为空。"
    base = path or SANDBOX_WORK_DIR
    flags: list[str] = []
    ctx_before = kwargs.get("-B") or kwargs.get("B")
    ctx_after = kwargs.get("-A") or kwargs.get("A")
    ctx_around = kwargs.get("-C") or kwargs.get("C") or kwargs.get("context")
    if ctx_around is not None:
        flags.append(f"-C {int(ctx_around)}")
    if ctx_before is not None:
        flags.append(f"-B {int(ctx_before)}")
    if ctx_after is not None:
        flags.append(f"-A {int(ctx_after)}")
    if kwargs.get("-i") or kwargs.get("i"):
        flags.append("-i")
    show_lineno = kwargs.get("-n")
    if show_lineno is None or show_lineno is True:
        flags.append("-n")
    if multiline:
        flags.append("-z")
    om = output_mode or "files_with_matches"
    if om == "files_with_matches":
        flags.append("-l")
    elif om == "count":
        flags.append("-c")
    elif om == "content":
        pass
    else:
        return f"[Grep] 错误：未知 output_mode={om}"
    flags.append("-rE")
    if glob:
        flags.append(f"--include={_shell_escape(glob)}")
    cmd = f"grep {' '.join(flags)} {_shell_escape(pattern)} {_shell_escape(base)} 2>/dev/null"
    if head_limit and head_limit > 0:
        cmd = f"{cmd} | head -n {int(head_limit)}"
    stdout, stderr, exit_code = await sandbox_run(sandbox, cmd)
    if exit_code in (0, 1):
        if not stdout.strip():
            return "[Grep] 无匹配。"
        return _truncate(stdout)
    return _truncate(_format_cmd_result(stdout, stderr, exit_code))


SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
SERPER_BASE_URL = os.getenv("SERPER_BASE_URL", "https://google.serper.dev").rstrip("/")
SERPER_SCRAPE_URL = os.getenv("SERPER_SCRAPE_URL", "https://scrape.serper.dev").rstrip("/")
SERPER_SCRAPE_TIMEOUT = float(os.getenv("SERPER_SCRAPE_TIMEOUT", "60"))
SERPER_DEFAULT_GL = os.getenv("SERPER_DEFAULT_GL", "us")
SERPER_DEFAULT_HL = os.getenv("SERPER_DEFAULT_HL", "en")
SERPER_TIMEOUT = float(os.getenv("SERPER_TIMEOUT", "30"))
SERPER_MAX_RETRIES = max(1, int(os.getenv("SERPER_MAX_RETRIES", "3")))
SERPER_WAIT_MAX = float(os.getenv("SERPER_WAIT_MAX", "15"))
_SERPER_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 522, 524}
_BLOCKED_URL_SUBSTRS = (
    "huggingface.co/datasets",
    "huggingface.co/spaces",
    "officeqa",
    "2603.08655",
    "databricks/officeqa",
    "sec.gov",
    "annualreports.com",
    "bamsec.com",
    "last10k.com",
    "stockanalysis.com",
    "macrotrends.net",
    "huggingface",
    "hf.co",
    "hf-mirror.com",
    "github.com",
    "githubusercontent",
    "arxiv",
    "ar5iv",
    "modelscope",
    "kaggle.com",
    "grep.app",
    "searchcode.com",
    "paperswithcode.com",
)


def _is_blocked_url(url: str) -> bool:
    if not url:
        return False
    u = url.lower()
    return any((s in u for s in _BLOCKED_URL_SUBSTRS))


def _serper_search_sync(query: str, *, count: int = 10, gl: str | None = None, hl: str | None = None) -> str:
    if not SERPER_API_KEY:
        return json.dumps(
            {"success": False, "error": "SERPER_API_KEY environment variable not set", "results": []},
            ensure_ascii=False,
        )
    if not query or not query.strip():
        return json.dumps(
            {"success": False, "error": "Search query is required and cannot be empty", "results": []},
            ensure_ascii=False,
        )
    _gl = gl or SERPER_DEFAULT_GL
    _hl = hl or SERPER_DEFAULT_HL
    _num = min(max(int(count), 1), 50)
    payload: Dict[str, Any] = {"q": query.strip(), "gl": _gl, "hl": _hl, "num": _num, "autocorrect": False}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    last_exc: Exception | None = None
    for attempt in range(1, SERPER_MAX_RETRIES + 1):
        try:
            response = requests.post(f"{SERPER_BASE_URL}/search", json=payload, headers=headers, timeout=SERPER_TIMEOUT)
            if response.status_code >= 400:
                if response.status_code in _SERPER_RETRYABLE_STATUS and attempt < SERPER_MAX_RETRIES:
                    sleep_s = min(2 ** (attempt - 1), int(SERPER_WAIT_MAX))
                    logger.warning(
                        "Serper transient HTTP %d on attempt %d, retrying in %ds",
                        response.status_code,
                        attempt,
                        sleep_s,
                    )
                    time.sleep(sleep_s)
                    continue
                body = (response.text or "")[:200]
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Serper rejected the search (HTTP {response.status_code}): {body}. Reformulate the query or check SERPER_API_KEY.",
                        "results": [],
                    },
                    ensure_ascii=False,
                )
            data = response.json() or {}
            organic_out = []
            for item in data.get("organic") or []:
                link = (item.get("link") or "").strip()
                if not link or _is_blocked_url(link):
                    continue
                organic_out.append(
                    {
                        "title": item.get("title") or "",
                        "link": link,
                        "snippet": item.get("snippet") or "",
                        "media": item.get("source") or item.get("displayLink") or "",
                        "date": item.get("date") or "",
                    }
                )
            output: Dict[str, Any] = {
                "searchParameters": {"q": query.strip(), "engine": "serper", "gl": _gl, "hl": _hl, "num": _num},
                "organic": organic_out,
            }
            for k in ("answerBox", "knowledgeGraph", "peopleAlsoAsk", "relatedSearches"):
                if k in data and data[k]:
                    output[k] = data[k]
            return json.dumps(output, ensure_ascii=False)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt < SERPER_MAX_RETRIES:
                sleep_s = min(2 ** (attempt - 1), int(SERPER_WAIT_MAX))
                logger.warning("Serper %s on attempt %d, retrying in %ds", type(e).__name__, attempt, sleep_s)
                time.sleep(sleep_s)
                continue
        except Exception as e:
            logger.exception("Serper search unexpected failure")
            return json.dumps(
                {
                    "success": False,
                    "error": f"Internal error in Serper backend ({type(e).__name__}): {str(e)[:150]}",
                    "results": [],
                },
                ensure_ascii=False,
            )
    return json.dumps(
        {
            "success": False,
            "error": f"Serper search is temporarily unreachable after {SERPER_MAX_RETRIES} retries ({(type(last_exc).__name__ if last_exc else 'unknown')}). Please try a different search engine or retry later.",
            "results": [],
        },
        ensure_ascii=False,
    )


_MD_LINK_RE = re.compile("\\[([^\\]]+)\\]\\(([^)]+)\\)")


def _strip_markdown_links(text: str) -> str:
    if not text:
        return ""
    return _MD_LINK_RE.sub("\\1", text)


def _serper_scrape_sync(url: str) -> str:
    if not url or not url.startswith(("http://", "https://")):
        return f"[WebFetch] Invalid URL: '{url}'. URL must start with http:// or https://"
    if _is_blocked_url(url):
        return "[WebFetch] This URL is on the blocklist (dataset/repo/paper hosting pages are restricted in this sandbox). Use a different source."
    if not SERPER_API_KEY:
        return "[WebFetch] SERPER_API_KEY is not set; WebFetch is unavailable."
    payload = {"url": url, "includeMarkdown": True}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    last_exc: Exception | None = None
    for attempt in range(1, SERPER_MAX_RETRIES + 1):
        try:
            resp = requests.post(SERPER_SCRAPE_URL, json=payload, headers=headers, timeout=SERPER_SCRAPE_TIMEOUT)
            if resp.status_code == 404:
                return f"[WebFetch] Page Not Found (404): '{url}' does not exist."
            if resp.status_code == 403:
                return f"[WebFetch] Access Forbidden (403): '{url}' is forbidden."
            if resp.status_code in _SERPER_RETRYABLE_STATUS and attempt < SERPER_MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))
                continue
            resp.raise_for_status()
            data = resp.json() or {}
            content = data.get("markdown") or data.get("text") or ""
            meta = data.get("metadata") or {}
            title = meta.get("title", "") or ""
            description = meta.get("description", "") or ""
            if not content:
                return f"[WebFetch] No content retrieved from URL: {url}"
            parts: list[str] = []
            if title:
                parts.append(f"Title: {title}")
            if description:
                parts.append(f"Description: {description}")
            parts.append(f"URL: {url}")
            parts.append("")
            parts.append(_strip_markdown_links(content))
            return "\n".join(parts)
        except requests.exceptions.Timeout as e:
            last_exc = e
            if attempt < SERPER_MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))
                continue
            return f"[WebFetch] Timeout while scraping '{url}' after {SERPER_MAX_RETRIES} attempts."
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if status_code in _SERPER_RETRYABLE_STATUS and attempt < SERPER_MAX_RETRIES:
                last_exc = e
                time.sleep(2 ** (attempt - 1))
                continue
            return f"[WebFetch] HTTP Error ({status_code}) on '{url}': {str(e)[:150]}"
        except requests.ConnectionError as e:
            last_exc = e
            if attempt < SERPER_MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))
                continue
            return f"[WebFetch] Connection error on '{url}' after {SERPER_MAX_RETRIES} attempts."
        except Exception as e:
            logger.exception("Serper scrape unexpected failure")
            return f"[WebFetch] Unexpected error scraping '{url}': {type(e).__name__}: {str(e)[:150]}"
    return f"[WebFetch] Failed to scrape '{url}' after retries: {(type(last_exc).__name__ if last_exc else 'unknown')}"


async def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    *,
    sandbox: Sandbox | None = None,
    file_state_cache: FileStateCache | None = None,
) -> str:
    name = tool_name
    if name == "Bash":
        return await tool_bash(sandbox, **tool_input)
    if name == "Read":
        return await tool_read(sandbox, cache=file_state_cache, **tool_input)
    if name == "Edit":
        return await tool_edit(sandbox, cache=file_state_cache, **tool_input)
    if name == "Write":
        return await tool_write(sandbox, cache=file_state_cache, **tool_input)
    if name == "Glob":
        return await tool_glob(sandbox, **tool_input)
    if name == "Grep":
        return await tool_grep(sandbox, **tool_input)
    if name == "WebFetch":
        return await tool_web_fetch(**tool_input)
    if name == "WebSearch":
        return await tool_web_search(**tool_input)
    return f"[dispatch_tool] 未知工具: {name}"


CORE_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Executes a given bash command in the sandbox and returns its output. Working directory is /workspace (persistent across calls), but shell state (env vars, cd) does not persist. For a persistent Python REPL: use Write to save code to a .py file under /workspace/, then Bash 'python3 /workspace/your_task.py'. Save state across steps by appending to the same .py file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"},
                    "timeout": {"type": "integer", "description": "Optional timeout in ms (max 600000)"},
                    "description": {"type": "string", "description": "Short description of what this command does"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read a file from the sandbox filesystem in `cat -n` format. Use offset+limit to read a slice of large files instead of the whole file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path inside the sandbox"},
                    "offset": {"type": "integer", "description": "Starting line number (1-based)"},
                    "limit": {"type": "integer", "description": "Number of lines to read (default 2000)"},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Edit",
            "description": "Perform an exact string replacement in a file. You MUST have read the file with Read before editing. By default old_string must be unique in the file (use replace_all=true to replace all occurrences).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                    "replace_all": {"type": "boolean", "default": False},
                },
                "required": ["file_path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write a file to the sandbox filesystem (overwrites if exists). For existing files, prefer Edit. To build a persistent Python session, keep appending to /workspace/task_<uid>.py and re-run it via Bash.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Glob",
            "description": "Fast file pattern matching. Supports glob patterns like '**/*.txt'. Returns matching paths sorted by modification time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "Directory to search in. Defaults to /workspace"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Grep",
            "description": "Content search built on grep -rE. output_mode defaults to files_with_matches. Use context=N (or -C/-A/-B) for surrounding lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                    "glob": {"type": "string", "description": "Filename filter, e.g. *.txt"},
                    "output_mode": {"type": "string", "enum": ["content", "files_with_matches", "count"]},
                    "context": {"type": "integer", "description": "Lines of context around match"},
                    "head_limit": {"type": "integer", "description": "Limit output to first N lines"},
                },
                "required": ["pattern"],
            },
        },
    },
]
WEB_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "WebFetch",
            "description": "Fetch a URL and return its content as markdown (truncated to ~25000 chars). Use this when you have a specific URL (e.g. from WebSearch results) and want to read the actual page contents. Returns the raw markdown so you can extract details yourself with subsequent reasoning. No summarization happens server-side.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Full http(s) URL of the page to fetch."}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "WebSearch",
            "description": "Search the web via Google (Serper) and return a JSON array of organic results (title / link / snippet / media / date). Use this when external reference data (e.g. CPI values, exchange rates, definitions, dates) is needed and is NOT present in /workspace/corpus/transformed/. To read any specific result page, call WebFetch on its `link`.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 2,
                        "description": "Search query. Supports site: operators.",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of organic results to return (1-50, default 10).",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


TOOL_SCHEMAS: list[dict] = CORE_TOOL_SCHEMAS + WEB_TOOL_SCHEMAS


async def tool_web_search(*, query: str, count: int = 10) -> str:
    if not query or len(query) < 2:
        return "[WebSearch] 错误：query 太短。"
    try:
        raw = await asyncio.to_thread(_serper_search_sync, query, count=count)
    except Exception as error:
        return f"[WebSearch] 搜索失败：{type(error).__name__}: {error}"
    return _truncate(raw)


async def tool_web_fetch(*, url: str) -> str:
    if not url:
        return "[WebFetch] 错误：url 不能为空。"
    try:
        raw = await asyncio.to_thread(_serper_scrape_sync, url)
    except Exception as error:
        return f"[WebFetch] 抓取失败：{type(error).__name__}: {error}"
    return _truncate(raw)
