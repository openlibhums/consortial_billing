from plugins.consortial_billing import plugin_settings
from events import logic as events_logic


def event_signup(request, supporter):
    kwargs = {
        'request': request,
        'supporter': supporter,
    }

    events_logic.Events.raise_event(
        plugin_settings.ON_SIGNUP,
        **kwargs,
    )
