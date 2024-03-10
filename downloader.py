import os.path
from functools import partial
from urllib.request import urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

def copy_url(task_id: TaskID, url: str, path: str) -> None:
    response = urlopen(url)
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data))
    progress.console.log(f":white_heavy_check_mark: Downloaded newer version of ImagineSuite!")


def download(url, dest_dir: str):
    with progress:
        filename = url.split("/")[-1]
        dest_path = os.path.join(dest_dir, filename)
        task_id = progress.add_task("download", filename=filename, start=False)
        copy_url(task_id, url, dest_path)