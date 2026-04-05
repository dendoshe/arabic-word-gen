try:
    import ujson as json
except ImportError:
    import json


ANIMATION_CONFIG_PATHS = (
    "animation_config.json",
    "lib/ui/resources/animation_config.json",
)

_EMPTY_ANIMATION_CONFIG = {
    "default_scene": None,
    "scene_aliases": {},
    "hint_keywords": (),
    "word_scene_map": {},
    "word_overrides": {},
    "scenes": {},
}

_CONFIG = None


def get_animation_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_animation_config()
    return _CONFIG


def resolve_animation_scene(word_key, word):
    config = get_animation_config()

    scene_key = _scene_from_word_animation(word)
    if scene_key:
        return normalize_scene_key(scene_key, config)

    scene_key = _scene_from_word_override(word_key, config)
    if scene_key:
        return normalize_scene_key(scene_key, config)

    scene_key = _scene_from_word_map(word_key, config)
    if scene_key:
        return normalize_scene_key(scene_key, config)

    scene_key = _scene_from_meaning(word, config)
    if scene_key:
        return normalize_scene_key(scene_key, config)

    return default_scene_key(config)


def get_scene_definition(scene_key):
    config = get_animation_config()
    scenes = config.get("scenes") or {}

    normalized = normalize_scene_key(scene_key, config)
    scene = scenes.get(normalized)
    if isinstance(scene, dict):
        return scene

    fallback = default_scene_key(config)
    if fallback:
        fallback_scene = scenes.get(fallback)
        if isinstance(fallback_scene, dict):
            return fallback_scene

    return {"elements": ()}


def default_scene_key(config=None):
    config = config or get_animation_config()
    scenes = config.get("scenes") or {}
    default_scene = normalize_scene_key(config.get("default_scene"), config)

    if default_scene in scenes:
        return default_scene
    if scenes:
        return next(iter(scenes))
    return None


def normalize_scene_key(scene_key, config=None):
    if not isinstance(scene_key, str) or not scene_key:
        return None

    config = config or get_animation_config()
    aliases = config.get("scene_aliases") or {}
    resolved = scene_key

    for _ in range(8):
        next_scene = aliases.get(resolved)
        if not isinstance(next_scene, str) or not next_scene or next_scene == resolved:
            break
        resolved = next_scene
    return resolved


def _load_animation_config():
    for path in ANIMATION_CONFIG_PATHS:
        try:
            with open(path, "r") as handle:
                data = json.load(handle)
        except Exception:
            continue

        config = _normalize_animation_config(data)
        if config is not None:
            return config

    print("animation config not found/invalid; disabling secondary animations")
    return dict(_EMPTY_ANIMATION_CONFIG)


def _normalize_animation_config(data):
    if not isinstance(data, dict):
        return None

    config = dict(_EMPTY_ANIMATION_CONFIG)
    config["default_scene"] = _normalize_string(data.get("default_scene"))
    config["scene_aliases"] = _normalize_string_map(data.get("scene_aliases"))
    config["word_scene_map"] = _normalize_string_map(data.get("word_scene_map"))
    config["word_overrides"] = _normalize_word_overrides(data.get("word_overrides"))
    config["hint_keywords"] = _normalize_hint_keywords(data.get("hint_keywords"))
    config["scenes"] = _normalize_scenes(data.get("scenes"))
    return config


def _normalize_string(value):
    if isinstance(value, str) and value:
        return value
    return None


def _normalize_string_map(value):
    if not isinstance(value, dict):
        return {}

    normalized = {}
    for key, mapped_value in value.items():
        if isinstance(key, str) and key and isinstance(mapped_value, str) and mapped_value:
            normalized[key] = mapped_value
    return normalized


def _normalize_word_overrides(value):
    if not isinstance(value, dict):
        return {}

    normalized = {}
    for key, override in value.items():
        if not isinstance(key, str) or not key:
            continue
        if isinstance(override, str) and override:
            normalized[key] = {"scene": override}
            continue
        if not isinstance(override, dict):
            continue
        scene = override.get("scene") or override.get("style")
        if isinstance(scene, str) and scene:
            normalized[key] = {"scene": scene}
    return normalized


def _normalize_hint_keywords(value):
    if not isinstance(value, list):
        return ()

    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        keyword = item.get("keyword")
        scene = item.get("scene")
        if isinstance(keyword, str) and keyword and isinstance(scene, str) and scene:
            normalized.append({"keyword": keyword, "scene": scene})
    return tuple(normalized)


def _normalize_scenes(value):
    if not isinstance(value, dict):
        return {}

    normalized = {}
    for name, scene in value.items():
        if not isinstance(name, str) or not name or not isinstance(scene, dict):
            continue

        elements = scene.get("elements")
        if not isinstance(elements, list):
            continue

        normalized_elements = []
        for element in elements:
            if not isinstance(element, dict):
                continue
            kind = element.get("kind")
            if isinstance(kind, str) and kind:
                normalized_elements.append(dict(element))

        normalized[name] = {"elements": normalized_elements}
    return normalized


def _scene_from_word_animation(word):
    animation = word.get("animation")
    if isinstance(animation, str) and animation:
        return animation
    if isinstance(animation, dict):
        scene = animation.get("scene") or animation.get("style")
        if isinstance(scene, str) and scene:
            return scene
    return None


def _scene_from_word_override(word_key, config):
    overrides = config.get("word_overrides") or {}
    override = overrides.get(word_key)
    if not isinstance(override, dict):
        return None
    scene = override.get("scene")
    if isinstance(scene, str) and scene:
        return scene
    return None


def _scene_from_word_map(word_key, config):
    scene = (config.get("word_scene_map") or {}).get(word_key)
    if isinstance(scene, str) and scene:
        return scene
    return None


def _scene_from_meaning(word, config):
    search_text = " ".join(
        (
            word.get("root_meaning", ""),
            word.get("sentence_en", ""),
            ((word.get("forms") or [{}])[0]).get("english", ""),
        )
    ).lower()

    for item in config.get("hint_keywords") or ():
        keyword = item["keyword"]
        if keyword in search_text:
            return item["scene"]
    return None
