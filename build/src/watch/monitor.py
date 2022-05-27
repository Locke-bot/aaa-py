import os
import sys
# add current folder to path
sys.path.append('.')
import collections
from src.build_single import build_single
import threading
from threading import Thread
import time
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PathList(collections.abc.MutableSequence):

    def __init__(self, *args):
        self._table = {}
        self.list = list()
        # after 3 seconds of inactivity, render edits on the folder
        self.timeout = 3
        self.extend(list(args))

    def __len__(self): return len(self.list)

    def __getitem__(self, i): return self.list[i]

    def __delitem__(self, i): del self.list[i]

    def __setitem__(self, i, v):
        self.check(v)
        self.list[i] = v
        
    def check_if_related(self, a, b):
        ap, bp = a.parts, b.parts
        # check if they belong in the same folder
        if ap[0] == bp[0]:
            return True
        else:
            return
    
    def check(self, item):
        check = None
        for enum, value in enumerate(self):
            check = self.check_if_related(item, value)
            if check:
                # there is a change on the folder, reset the timeout.
                self._table[value] = time.time() + self.timeout
                break
        return check
    
    def insert(self, i, v):
        # it must be a new folder, add to list
        if not self.check(v):
            self.list.insert(i, v)
            self._table[v] = time.time() + self.timeout

    def __str__(self):
        return str(self.list)
    
    def __contains__(self, item):
        return time.time() < self._table.get(item)
    

path_list = PathList()

class MonitorFolder(FileSystemEventHandler):

    def on_created(self, event):
        rel_path = Path(event.src_path).relative_to(src_path)
        print(rel_path, f"{event.event_type} event")
        path_list.append(rel_path)
   
    def on_modified(self, event):
        rel_path = Path(event.src_path).relative_to(src_path)
        print(rel_path, f"{event.event_type} event")
        path_list.append(rel_path)
    
    def on_deleted(self, event):
        # wont take an action on content delete
        pass

def render(chapter_name):
    print(f'rendering of {chapter_name}')
    try:
        build_single(chapter_name)
    except Exception as e:
        print(f"{chapter_name} render failed: {e}")
    finally:
        # kill the thread
        sys.exit()

def render_single():
    while True:
        time.sleep(1)
        for key, value in path_list._table.copy().items():
            if time.time() > value:
                del path_list._table[key]
                path_list.remove(key)
                render_thread = Thread(target=render, args=(Path(key).parts[0],))
                render_thread.daemon = True
                render_thread.start()
                print(f"{key} done copying,", threading.active_count())

if __name__ == "__main__":
    src_path = Path('contents/contents')
    event_handler=MonitorFolder()
    observer = Observer()
    observer.schedule(event_handler, path=src_path, recursive=True)
    render_single_thread = Thread(target=render_single)
    render_single_thread.daemon = True
    print(f"Monitoring started on {src_path}")
    observer.start()
    render_single_thread.start()
    
    try:
        while(True):
           time.sleep(0.5)       
    except KeyboardInterrupt:
            observer.stop()
            observer.join()