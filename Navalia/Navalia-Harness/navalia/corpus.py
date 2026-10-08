from __future__ import annotations

import json
import os

DEFAULT_CORPUS_ROOT = "/workspace/corpus/transformed"
KEEP_LIST_REMOTE = "/tmp/officeqa_keep.txt"
CLEANUP_SCRIPT_REMOTE = "/tmp/officeqa_cleanup.py"
_CLEANUP_SCRIPT_TEMPLATE = r'''
"""沙箱内执行：读 keep-list，保留 keep 里的文件，删 corpus_root 下其余所有文件。

输出一行 JSON 到 stdout。
退出码 0：清理完成（即便有 unlink 错误也算完成）
退出码 1：致命错误（如 corpus_root 不存在）
"""
import json, os, sys, time

KEEP_LIST = "__KEEP_LIST__"
CORPUS_ROOT = "__CORPUS_ROOT__"

t0 = time.time()

if not os.path.isdir(CORPUS_ROOT):
    print(json.dumps({"fatal": "corpus_root not a dir: " + CORPUS_ROOT}))
    sys.exit(1)

if not os.path.isfile(KEEP_LIST):
    print(json.dumps({"fatal": "keep-list not found: " + KEEP_LIST}))
    sys.exit(1)

with open(KEEP_LIST, "r", encoding="utf-8") as f:
    keep = set(line.strip() for line in f if line.strip())

if not keep:
    print(json.dumps({"fatal": "keep-list is empty"}))
    sys.exit(1)

deleted = 0
kept = 0
errors = []
seen_in_root = set()

for name in os.listdir(CORPUS_ROOT):
    full = os.path.join(CORPUS_ROOT, name)
    if not os.path.isfile(full):
        # 子目录或 symlink 一律不动（image 是扁平的，正常不应出现）
        continue
    seen_in_root.add(name)
    if name in keep:
        kept += 1
        continue
    try:
        os.unlink(full)
        deleted += 1
    except OSError as e:
        errors.append(name + ": " + type(e).__name__ + ": " + str(e))
        if len(errors) > 50:  # 防止异常爆量
            break

missing_keep = sorted(keep - seen_in_root)

print(json.dumps({
    "kept": kept,
    "deleted": deleted,
    "missing_keep_count": len(missing_keep),
    "missing_keep_sample": missing_keep[:10],
    "elapsed_sec": round(time.time() - t0, 2),
    "errors": errors[:5],
    "error_count": len(errors),
}))
'''


def _build_cleanup_script(corpus_root: str) -> str:
    return _CLEANUP_SCRIPT_TEMPLATE.replace("__KEEP_LIST__", KEEP_LIST_REMOTE).replace("__CORPUS_ROOT__", corpus_root)


async def _run_cmd(sandbox, cmd: str) -> tuple[str, str, int | None]:
    return await sandbox.run(cmd)


async def trim_corpus_to_task(sandbox, corpus_subset: list[str], *, corpus_root: str = DEFAULT_CORPUS_ROOT) -> dict:
    if not corpus_subset:
        raise ValueError("corpus_subset 不能为空")
    keep_basenames = sorted({os.path.basename(p) for p in corpus_subset})
    keep_text = "\n".join(keep_basenames) + "\n"
    await sandbox.write_file(KEEP_LIST_REMOTE, keep_text.encode("utf-8"))
    script = _build_cleanup_script(corpus_root)
    await sandbox.write_file(CLEANUP_SCRIPT_REMOTE, script.encode("utf-8"))
    stdout, stderr, exit_code = await _run_cmd(sandbox, f"python3 {CLEANUP_SCRIPT_REMOTE}")
    try:
        result = json.loads(stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        raise RuntimeError(
            f"清理脚本输出无法解析: exit={exit_code}\nstdout: {stdout[:500]!r}\nstderr: {stderr[:500]!r}\nparse error: {e}"
        )
    if "fatal" in result:
        raise RuntimeError(f"清理脚本致命错误: {result['fatal']}")
    if exit_code not in (0, None):
        raise RuntimeError(f"清理脚本退出码异常: {exit_code}\nstdout: {stdout}\nstderr: {stderr}")
    result["expected_kept"] = len(keep_basenames)
    result["ok"] = result.get("kept", 0) == len(keep_basenames) and result.get("error_count", 0) == 0
    return result
