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
MAX_LINE_WIDTH = 960


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


def _chunks(words: list[str], max_words: int = 4, max_chars: int = 30) -> list[tuple[int, int]]:
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


def _text_width(draw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=STROKE_WIDTH)
    return bbox[2] - bbox[0]


def _wrap_lines(draw, words: list[str], reserve_font):
    lines = []
    current = []
    current_width = 0

    for i, word in enumerate(words):
        width = _text_width(draw, word, reserve_font)
        next_width = width if not current else current_width + WORD_SPACING + width

        if current and next_width > MAX_LINE_WIDTH and len(lines) < 1:
            lines.append(current)
            current = [(i, word, width)]
            current_width = width
        else:
            current.append((i, word, width))
            current_width = next_width

    if current:
        lines.append(current)

    return lines


def _caption_layout(draw, words: list[str], reserve_size: int):
    while True:
        reserve_font = _load_font(reserve_size)
        lines = _wrap_lines(draw, words, reserve_font)
        widest = 0
        for line in lines:
            width = sum(item[2] for item in line) + WORD_SPACING * max(0, len(line) - 1)
            widest = max(widest, width)
        if (len(lines) <= 2 and widest <= MAX_LINE_WIDTH) or reserve_size <= 44:
            return lines, reserve_size
        reserve_size -= 4


def _draw_caption(
    path: str,
    layout: list[list[tuple[int, str, int]]],
    active_index: int,
    active_size: int,
) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    base_font = _load_font(max(38, active_size - 12))
    active_font = _load_font(active_size)

    line_height = max(active_size + 28, 100)
    total_height = line_height * len(layout)
    y = OUTPUT_HEIGHT - 330 - total_height

    for line in layout:
        line_width = sum(item[2] for item in line) + WORD_SPACING * max(0, len(line) - 1)
        x = (OUTPUT_WIDTH - line_width) // 2

        for i, word, width in line:
            is_active = i == active_index
            font = active_font if is_active else base_font
            fill = CLAUDE_ORANGE if is_active else TEXT_COLOR
            text_width = _text_width(draw, word, font)
            draw_x = x + (width - text_width) / 2
            draw.text(
                (draw_x, y),
                word,
                font=font,
                fill=fill,
                stroke_width=STROKE_WIDTH,
                stroke_fill=OUTLINE_COLOR,
            )
            x += width + WORD_SPACING

        y += line_height

    image.save(path)


def _add_overlay_event(
    events: list[dict],
    temp_dir: str,
    layout: list[list[tuple[int, str, int]]],
    active_index: int,
    start: float,
    end: float,
    active_size: int,
) -> None:
    if end <= start:
        return
    filename = f"subtitle_{len(events):04d}.png"
    path = os.path.join(temp_dir, filename)
    _draw_caption(path, layout, active_index, active_size)
    events.append({"path": path, "start": start, "end": end})


def create_subtitle_overlays(scenes: list[dict], temp_dir: str) -> list[dict]:
    os.makedirs(temp_dir, exist_ok=True)
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
            from PIL import Image, ImageDraw

            image = Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            layout, layout_active_size = _caption_layout(draw, chunk_words, POP_FONT_SIZE)
            for word_index in range(chunk_start, chunk_end):
                start, end = timings[word_index]
                absolute_start = scene_start + start
                absolute_end = scene_start + end
                active_index = word_index - chunk_start
                word_duration = absolute_end - absolute_start
                active_size = min(ACTIVE_FONT_SIZE, layout_active_size)
                pop_size = min(POP_FONT_SIZE, layout_active_size)

                if word_duration > 0.18:
                    pop_end = min(absolute_start + 0.12, absolute_end)
                    _add_overlay_event(
                        events,
                        temp_dir,
                        layout,
                        active_index,
                        absolute_start,
                        pop_end,
                        pop_size,
                    )
                    _add_overlay_event(
                        events,
                        temp_dir,
                        layout,
                        active_index,
                        pop_end,
                        absolute_end,
                        active_size,
                    )
                else:
                    _add_overlay_event(
                        events,
                        temp_dir,
                        layout,
                        active_index,
                        absolute_start,
                        absolute_end,
                        active_size,
                    )

        scene_start += duration

    return events
