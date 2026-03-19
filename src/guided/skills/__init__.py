from guided.skills.web_search import search_web_text, request_web
from guided.skills.container import (
    build_container_image,
    exec_command,
    list_files,
    read_file,
    write_file,
)
from guided.skills.kubernetes import (
    kubectl_get,
    kubectl_describe,
    kubectl_logs,
    kubectl_exec,
    kubectl_apply,
    kubectl_delete,
    kubectl_rollout_status,
)

DEFAULT_TOOLS = [
    search_web_text,
    request_web,
    build_container_image,
    exec_command,
    list_files,
    read_file,
    write_file,
    kubectl_get,
    kubectl_describe,
    kubectl_logs,
    kubectl_exec,
    kubectl_apply,
    kubectl_delete,
    kubectl_rollout_status,
]
