from lib.conf_models import TTS_ENGINES, default_engine_settings


models = {
    "internal": {
        "lang": "multi",
        "repo": None,
        "sub": {},
        "voice": None,
        "files": [],
        "samplerate": default_engine_settings[TTS_ENGINES["AI_VOICE"]]["samplerate"],
    }
}
