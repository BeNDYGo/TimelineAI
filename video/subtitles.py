import os
import re


OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
TEXT_COLOR = (247, 244, 239, 255)
CLAUDE_ORANGE = (217, 119, 87, 255)
OUTLINE_COLOR = (18, 18, 18, 255)
BASE_FONT_SIZE = 78
ACTIVE_FONT_SIZE = 90
POP_FONT_SIZE = 98
STROKE_WIDTH = 6
WORD_SPACING = 24


def check_subtitle_dependencies() -> dict:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return {
            "status": "error",
            "error": "Pillow is required for subtitles. Install requirements.txt.",
        }
    return {"status": "ok"}


def _load_font(size: int):
    from PIL import ImageFont

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _word_weight(word: str) -> float:
    letters = re.sub(r"[^\wа-яА-ЯёЁ]", "", word, flags=re.UNICODE)
    weight = max(1.0, len(letters) ** 0.75)
    if word.endswith((",", ";", ":")):
        weight += 0.45
    if word.endswith((".", "!", "?")):
        weight += 0.8
    return weight


def _word_timings(words: list[str], duration: float) -> list[tuple[float, float]]:
    if not words:
        return []

    weights = [_word_weight(word) for word in words]
    total = sum(weights)
    current = 0.0
    timings = []

    for i, weight in enumerate(weights):
        if i == len(words) - 1:
            end = duration
        else:
            end = current + duration * weight / total
        timings.append((current, end))
        current = end

    return timings


def _chunks(words: list[str], max_words: int = 6, max_chars: int = 42) -> list[tuple[int, int]]:
    chunks = []
    start = 0

    while start < len(words):
        end = start
        chars = 0

        while end < len(words) and end - start < max_words:
            next_len = len(words[end]) + (1 if end > start else 0)
            if end > start and chars + next_len > max_chars:
                break
            chars += next_len
            end += 1

        if end == start:
            end += 1

        chunks.append((start, end))
        start = end

    return chunks


def _split_lines(words: list[str]) -> list[list[str]]:
    if len(words) <= 3:
        return [words]
    break_at = (len(words) + 1) // 2
    return [words[:break_at], words[break_at:]]


def _text_width(draw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=STROKE_WIDTH)
    return bbox[2] - bbox[0]


def _draw_caption(path: str, words: list[str], active_index: int, active_size: int) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    base_font = _load_font(BASE_FONT_SIZE)
    active_font = _load_font(active_size)
    lines = _split_lines(words)
    line_height = max(active_size + 28, 108)
    total_height = line_height * len(lines)
    y = OUTPUT_HEIGHT - 330 - total_height
    word_offset = 0

    for line in lines:
        widths = []
        for i, word in enumerate(line):
            font = active_font if word_offset + i == active_index else base_font
            widths.append(_text_width(draw, word, font))

        line_width = sum(widths) + WORD_SPACING * max(0, len(line) - 1)
        x = (OUTPUT_WIDTH - line_width) // 2

        for i, word in enumerate(line):
            is_active = word_offset + i == active_index
            font = active_font if is_active else base_font
            fill = CLAUDE_ORANGE if is_active else TEXT_COLOR
            draw.text(
                (x, y),
                word,
                font=font,
                fill=fill,
                stroke_width=STROKE_WIDTH,
                stroke_fill=OUTLINE_COLOR,
            )
            x += widths[i] + WORD_SPACING

        y += line_height
        word_offset += len(line)

    image.save(path)


def _add_overlay_event(
    events: list[dict],
    temp_dir: str,
    words: list[str],
    active_index: int,
    start: float,
    end: float,
    active_size: int,
) -> None:
    if end <= start:
        return
    filename = f"subtitle_{len(events):04d}.png"
    path = os.path.join(temp_dir, filename)
    _draw_caption(path, words, active_index, active_size)
    events.append({"path": path, "start": start, "end": end})


def create_subtitle_overlays(scenes: list[dict], temp_dir: str) -> list[dict]:
    events = []
    scene_start = 0.0

    for scene in scenes:
        duration = float(scene.get("duration") or 0)
        text = (scene.get("text") or "").strip()

        if duration <= 0:
            continue

        words = re.findall(r"\S+", text)
        timings = _word_timings(words, duration)

        for chunk_start, chunk_end in _chunks(words):
            chunk_words = words[chunk_start:chunk_end]
            for word_index in range(chunk_start, chunk_end):
                start, end = timings[word_index]
                absolute_start = scene_start + start
                absolute_end = scene_start + end
                active_index = word_index - chunk_start
                word_duration = absolute_end - absolute_start

                if word_duration > 0.18:
                    pop_end = min(absolute_start + 0.12, absolute_end)
                    _add_overlay_event(
                        events,
                        temp_dir,
                        chunk_words,
                        active_index,
                        absolute_start,
                        pop_end,
                        POP_FONT_SIZE,
                    )
                    _add_overlay_event(
                        events,
                        temp_dir,
                        chunk_words,
                        active_index,
                        pop_end,
                        absolute_end,
                        ACTIVE_FONT_SIZE,
                    )
                else:
                    _add_overlay_event(
                        events,
                        temp_dir,
                        chunk_words,
                        active_index,
                        absolute_start,
                        absolute_end,
                        ACTIVE_FONT_SIZE,
                    )

        scene_start += duration

    return events
