import os
import sys
import time
import glob
import re
import random
import subprocess
import yt_dlp
from yt_dlp.utils import download_range_func
from core import PROXY_POOL, parse_time_to_seconds

class DownloaderMixin:
    def run_download_manager(self, url, folder, mode, res, audio_fmt, use_hb, hb_preset, trim_on, t_start, t_end):
        print("Attempting Direct Connection...")
        status = self.run_download_task(url, folder, mode, res, audio_fmt, use_hb, hb_preset, None, trim_on, t_start, t_end)

        if self.stop_event.is_set() or status == 0 or status == 2:
            return

        self.status_var.set("Network blocked. Switching to Proxies...")
        print("Engaging Proxies...")

        max_retries = 5
        used_proxies = set()
        for i in range(max_retries):
            if self.stop_event.is_set():
                return
            available = [p for p in PROXY_POOL if p not in used_proxies]
            if not available:
                break
            proxy_url = f"http://{random.choice(available)}"
            used_proxies.add(proxy_url)
            self.status_var.set(f"Retrying with Secure Proxy ({i+1}/{max_retries})...")
            status = self.run_download_task(url, folder, mode, res, audio_fmt, use_hb, hb_preset, proxy_url, trim_on, t_start, t_end)
            if status == 0 or status == 2:
                return
            time.sleep(1)

        if not self.stop_event.is_set():
            self.finish_fail("Connection failed. Try again later.")

    def run_download_task(self, url, folder, mode, res_text, audio_fmt, use_hb, hb_preset, proxy, trim_on, t_start, t_end):
        temp_filename = f"temp_{int(time.time())}"

        def progress_hook(d):
            if self.stop_event.is_set():
                raise Exception("Stopped")
            if d["status"] == "downloading" and d.get("total_bytes"):
                self.progress_bar.set(d["downloaded_bytes"] / d["total_bytes"])
                self.status_var.set(f"Downloading Source: {int(self.progress_bar.get() * 100)}%")

        height_limit = None
        if "Best" not in res_text:
            try:
                height_limit = int(res_text.split("p")[0])
            except (ValueError, IndexError):
                pass

        ydl_opts = {
            "outtmpl": os.path.join(folder, f"{temp_filename}.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "noplaylist": True,
            "socket_timeout": 20,
            "retries": 3,
            "ffmpeg_location": self.ffmpeg_path,
        }

        if trim_on:
            s_sec = parse_time_to_seconds(t_start) if t_start else 0
            e_sec = parse_time_to_seconds(t_end) if t_end else None
            if e_sec is not None and e_sec > s_sec:
                ydl_opts['download_ranges'] = download_range_func(None, [(s_sec, e_sec)])
                ydl_opts['force_keyframes_at_cuts'] = True

        if proxy:
            ydl_opts["proxy"] = proxy

        if mode == "Audio Only":
            ydl_opts.update({
                "format": "bestaudio/best",
                "outtmpl": os.path.join(folder, f"%(title)s.{audio_fmt}"),
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": audio_fmt}],
            })
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.after(0, self.finish_success)
                return 0
            except Exception as e:
                return 2 if "Stopped" in str(e) else 1

        if height_limit:
            ydl_opts["format"] = f"bestvideo[height<={height_limit}]+bestaudio/best[height<={height_limit}]/best"
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_title = re.sub(r'[\\/*?:"<>|]', "", info.get('title', 'video'))
                if trim_on:
                    start_str = (t_start.replace(":", "-") if t_start else "0-00")
                    end_str = (t_end.replace(":", "-") if t_end else "")
                    if end_str:
                        trim_prefix = f"{start_str} - {end_str} "
                        final_title = trim_prefix + final_title
                video_height = info.get('height', 0) or (height_limit if height_limit else 1080)
                video_width = info.get('width', 0) or 1920

            temp_files = glob.glob(os.path.join(folder, f"{temp_filename}.*"))
            if not temp_files:
                raise Exception("Temp missing")
            temp_fullpath = temp_files[0]
            ext = os.path.splitext(temp_fullpath)[1]
            final_output = os.path.join(folder, f"{final_title}.mp4" if use_hb else f"{final_title}{ext}")

        except Exception as e:
            self.clean_temp(folder, temp_filename)
            return 2 if "Stopped" in str(e) else 1

        if self.stop_event.is_set():
            self.clean_temp(folder, temp_filename)
            return 2

        if use_hb:
            try:
                if "Auto" in hb_preset:
                    is_4k = video_width > 2600 or video_height >= 2160
                    preset = "Fast 2160p60 4K HEVC" if is_4k else "Fast 1080p30" if video_height >= 1080 else "Fast 720p30"
                else:
                    if "Fast 2160p" in hb_preset:
                        preset = "Fast 2160p60 4K HEVC"
                    elif "HQ 2160p" in hb_preset:
                        preset = "HQ 2160p60 4K HEVC Surround"
                    else:
                        preset = hb_preset

                self.status_var.set(f"Processing ({preset})...")
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                self.current_process = subprocess.Popen([
                    self.handbrake_path, "-i", temp_fullpath, "-o", final_output, "-Z", preset, "-e", "x264", "--all-audio"
                ], startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                self.current_process.wait()

                if self.stop_event.is_set() or self.current_process.returncode != 0:
                    self.clean_temp(folder, temp_filename)
                    if os.path.exists(final_output):
                        os.remove(final_output)
                    return 2

                if os.path.exists(temp_fullpath):
                    os.remove(temp_fullpath)
                self.after(0, self.finish_success)
                return 0

            except Exception as e:
                self.clean_temp(folder, temp_filename)
                self.after(0, lambda: self.finish_fail(f"Processing Error: {str(e)[:30]}"))
                return 2
        else:
            try:
                if os.path.exists(final_output):
                    os.remove(final_output)
                os.rename(temp_fullpath, final_output)
                self.after(0, self.finish_success)
                return 0
            except OSError:
                return 2

    def clean_temp(self, folder, filename):
        for f in glob.glob(os.path.join(folder, f"{filename}.*")):
            try:
                os.remove(f)
            except OSError:
                pass
