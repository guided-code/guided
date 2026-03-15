from guided.skills.web_search import search_web_text, request_web
from guided.skills.container import exec_command, list_files, read_file, write_file

DEFAULT_TOOLS = [
    search_web_text,
    request_web,
    exec_command,
    list_files,
    read_file,
    write_file,
]
